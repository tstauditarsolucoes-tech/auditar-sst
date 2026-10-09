#!/usr/bin/env python3
"""Auditar SST v3.29.145 / v3.30.64

Photo AI performance package on top of field productivity releases:
- image resize/encode outside the UI isolate;
- adaptive payload by photo count;
- checklist tries fast image route first;
- avoids a second long fallback after a timeout;
- Ronda shows elapsed analysis time.

Protected byte-for-byte: sync, DB, auth, media, Drive, Apps Script.
"""
from pathlib import Path
import hashlib
import sys

if len(sys.argv) < 3:
    raise SystemExit("uso: patch_ai_photo_speed_v329145_v33064.py <APP_DIR> <android|windows>")

root = Path(sys.argv[1])
platform = sys.argv[2].strip().lower()
if platform not in ("android", "windows"):
    raise SystemExit("plataforma invalida")

def read(rel):
    return (root / rel).read_text(encoding="utf-8")

def write(rel, value):
    (root / rel).write_text(value, encoding="utf-8", newline="\n")

def once(text, old, new, label):
    if new in text:
        return text
    if text.count(old) != 1:
        raise RuntimeError(label + ": esperado 1, encontrado " + str(text.count(old)))
    return text.replace(old, new, 1)

protected = [
    "lib/database.dart",
    "lib/services/device_sync_service.dart",
    "lib/services/apps_script_http.dart",
    "lib/services/sync_coordinator.dart",
    "lib/services/auth_service.dart",
    "lib/services/drive_service.dart",
    "lib/services/media_sync_service.dart",
    "painel_web_google_apps_script/Code.gs",
    "painel_web_google_apps_script/MultiUser.gs",
    "painel_web_google_apps_script/ClientPortal.gs",
    "painel_web_google_apps_script/ClientPortal.html",
    "painel_web_google_apps_script/ReportEmail.gs",
]
before = {
    name: hashlib.sha256((root / name).read_bytes()).hexdigest()
    for name in protected
}

# ---------------------------------------------------------------------------
# AI service
# ---------------------------------------------------------------------------
rel = "lib/services/ai_assistant_service.dart"
ai = read(rel)
if "import 'dart:isolate';" not in ai:
    ai = once(
        ai,
        "import 'dart:io';\n",
        "import 'dart:io';\nimport 'dart:isolate';\n",
        "import isolate",
    )

check_start = ai.find("  static Future<AiAssistantReply> analyzeChecklistPhotos({")
check_end = ai.find("  static Future<AiAssistantReply> analyzeSafetyObservationPhoto({", check_start)
if check_start < 0 or check_end < 0:
    raise RuntimeError("analyzeChecklistPhotos nao localizado")

new_check = r"""  static Future<AiAssistantReply> analyzeChecklistPhotos({
    required Inspection inspection,
    required String companyName,
    required ChecklistItem item,
    required List<String> photoPaths,
    String technicianContext = '',
  }) async {
    if (photoPaths.isEmpty) {
      return const AiAssistantReply(
        success: false,
        message: 'Adicione pelo menos uma foto antes de analisar.',
      );
    }

    try {
      final available = <File>[];
      for (final path in photoPaths.take(4)) {
        final file = File(path);
        if (await file.exists()) available.add(file);
      }
      if (available.isEmpty) {
        return const AiAssistantReply(
          success: false,
          message: 'Não foi possível abrir as fotos selecionadas.',
        );
      }

      final images = <String>[];
      var totalBytes = 0;
      for (var index = 0; index < available.length; index++) {
        final originalBytes = await available[index].readAsBytes();
        final single = available.length == 1;
        final bytes = await _preparePhotoForAiAsync(
          originalBytes,
          maxDimension: single ? 720 : (index == 0 ? 640 : 560),
          quality: single ? 55 : (index == 0 ? 52 : 48),
          maxBytes: single ? 650000 : 480000,
        );
        if (totalBytes + bytes.length > 3200000 && images.isNotEmpty) break;
        totalBytes += bytes.length;
        images.add('data:image/jpeg;base64,${base64Encode(bytes)}');
      }

      if (images.isEmpty) {
        return const AiAssistantReply(
          success: false,
          message: 'Não foi possível preparar as fotos selecionadas.',
        );
      }

      final payload = <String, Object?>{
        'mode': 'checklist_photo',
        'companyName': companyName,
        'area': inspection.area,
        'question': item.text,
        'category': item.category,
        'reference': item.reference,
        'technicianContext': technicianContext.trim(),
        'images': images,
      };

      final fast = await _send({
        ...payload,
        'rondaDeferred': false,
      });
      if (fast.success) return fast;

      final lower = fast.message.toLowerCase();
      final timedOut =
          lower.contains('demor') ||
          lower.contains('timeout') ||
          lower.contains('não respondeu a tempo');
      if (timedOut) return fast;

      return _send({
        ...payload,
        'rondaDeferred': true,
      });
    } catch (error) {
      return AiAssistantReply(
        success: false,
        message: 'Não foi possível preparar as fotos: $error',
      );
    }
  }

"""
ai = ai[:check_start] + new_check + ai[check_end:]

round_start = ai.find("  static Future<AiAssistantReply> analyzeSafetyObservationPhoto({")
round_end = ai.find("  static Future<AiAssistantReply> reviewExpressRound(", round_start)
if round_start < 0 or round_end < 0:
    raise RuntimeError("analyzeSafetyObservationPhoto nao localizado")

new_round = r"""  static Future<AiAssistantReply> analyzeSafetyObservationPhoto({
    required Company company,
    required String observationKind,
    required String sectorName,
    required String location,
    required String photoPath,
    String? secondPhotoPath,
    String technicianContext = '',
  }) async {
    if (photoPath.trim().isEmpty) {
      return const AiAssistantReply(
        success: false,
        message: 'Adicione uma foto antes de analisar.',
      );
    }

    final watch = Stopwatch()..start();
    try {
      final file = File(photoPath);
      if (!await file.exists()) {
        return const AiAssistantReply(
          success: false,
          message:
              'A foto não está disponível neste aparelho. Aguarde a recuperação da mídia ou escolha a foto novamente.',
        );
      }

      final bytes = await _preparePhotoForAiAsync(
        await file.readAsBytes(),
        maxDimension: 720,
        quality: 55,
        maxBytes: 650000,
      );
      final images = <String>[
        'data:image/jpeg;base64,${base64Encode(bytes)}',
      ];

      if (secondPhotoPath != null && secondPhotoPath.trim().isNotEmpty) {
        final second = File(secondPhotoPath);
        if (await second.exists()) {
          final thumb = await _preparePhotoForAiAsync(
            await second.readAsBytes(),
            maxDimension: 560,
            quality: 48,
            maxBytes: 420000,
          );
          images.add('data:image/jpeg;base64,${base64Encode(thumb)}');
        }
      }

      final area = [
        sectorName.trim(),
        location.trim(),
      ].where((value) => value.isNotEmpty).join(' • ');

      final context = [
        technicianContext.trim(),
        if (observationKind == 'Conformidade')
          'Trate este registro como CONFORMIDADE/BOA PRÁTICA. Descreva somente aspectos positivos visíveis. Não invente risco ou irregularidade. A recomendação deve indicar como manter o padrão.'
        else
          'Trate este registro como NÃO CONFORMIDADE. Descreva somente o que for sustentado pela foto e pelo contexto do técnico. Sugira risco, recomendação e prioridade; referências normativas precisam ser conferidas pelo responsável técnico.',
      ].where((value) => value.isNotEmpty).join('\n');

      final fastReply = await _send({
        'mode': 'checklist_photo',
        'rondaDeferred': false,
        'companyName': company.name,
        'area': area.isEmpty ? 'Ronda Expressa' : area,
        'question':
            observationKind == 'Conformidade'
                ? 'Ronda Expressa: registrar uma conformidade ou boa prática observável na foto.'
                : 'Ronda Expressa: registrar uma não conformidade observável na foto.',
        'category': 'Ronda Expressa',
        'reference': '',
        'technicianContext': context,
        'images': images,
      });

      AiAssistantReply reply = fastReply;
      final fastDescription = '${fastReply.result['description'] ?? ''}'.trim();
      final lower = fastReply.message.toLowerCase();
      final timedOut =
          lower.contains('demor') ||
          lower.contains('timeout') ||
          lower.contains('não respondeu a tempo');

      if ((!fastReply.success || fastDescription.isEmpty) && !timedOut) {
        reply = await _send({
          'mode': 'safety_observation_photo',
          'rondaDeferred': false,
          'companyName': company.name,
          'observationKind': observationKind,
          'sectorName': sectorName,
          'location': location,
          'technicianContext': context,
          'images': images,
        });
      }

      if (!reply.success) return reply;

      final normalized = Map<String, dynamic>.from(reply.result);
      normalized.putIfAbsent('title', () => '');
      normalized.putIfAbsent('possibleConsequence', () => '');
      normalized['aiImageBytes'] = bytes.length;
      normalized['aiElapsedMs'] = watch.elapsedMilliseconds;
      normalized['aiPhotoCount'] = images.length;
      return AiAssistantReply(
        success: true,
        message: 'Foto analisada. Revise a sugestão antes de usar no relatório.',
        result: normalized,
      );
    } catch (error) {
      return AiAssistantReply(
        success: false,
        message: 'Não foi possível preparar a foto para a IA: $error',
      );
    } finally {
      watch.stop();
    }
  }

"""
ai = ai[:round_start] + new_round + ai[round_end:]

helper_start = ai.find("  static Uint8List _prepareRoundPhotoForAi(Uint8List originalBytes) {")
helper_end = ai.find("  static Uint8List _prepareImage(Uint8List originalBytes) {", helper_start)
if helper_start < 0 or helper_end < 0:
    raise RuntimeError("helper de foto da IA nao localizado")

new_helpers = r"""  static Future<Uint8List> _preparePhotoForAiAsync(
    Uint8List originalBytes, {
    required int maxDimension,
    required int quality,
    required int maxBytes,
  }) {
    return Isolate.run(
      () => _preparePhotoForAi(
        originalBytes,
        maxDimension: maxDimension,
        quality: quality,
        maxBytes: maxBytes,
      ),
    );
  }

  static Uint8List _preparePhotoForAi(
    Uint8List originalBytes, {
    required int maxDimension,
    required int quality,
    required int maxBytes,
  }) {
    final decoded = img.decodeImage(originalBytes);
    if (decoded == null) {
      throw const FormatException('formato de imagem não reconhecido');
    }

    var prepared = img.bakeOrientation(decoded);
    if (prepared.width > maxDimension || prepared.height > maxDimension) {
      prepared =
          prepared.width >= prepared.height
              ? img.copyResize(prepared, width: maxDimension)
              : img.copyResize(prepared, height: maxDimension);
    }

    final sanitized = img.Image(
      width: prepared.width,
      height: prepared.height,
      numChannels: 3,
    );
    img.compositeImage(sanitized, prepared);

    var encoded = Uint8List.fromList(
      img.encodeJpg(sanitized, quality: quality),
    );
    if (encoded.length > maxBytes) {
      final reducedDimension = (maxDimension * .82).round();
      final reducedQuality = quality - 6 < 38 ? 38 : quality - 6;
      final smaller =
          prepared.width >= prepared.height
              ? img.copyResize(sanitized, width: reducedDimension)
              : img.copyResize(sanitized, height: reducedDimension);
      encoded = Uint8List.fromList(
        img.encodeJpg(smaller, quality: reducedQuality),
      );
    }
    return encoded;
  }

  static Uint8List _prepareRoundPhotoForAi(Uint8List originalBytes) {
    return _preparePhotoForAi(
      originalBytes,
      maxDimension: 720,
      quality: 55,
      maxBytes: 650000,
    );
  }

"""
ai = ai[:helper_start] + new_helpers + ai[helper_end:]

old_timeout = """    final requestTimeout =
        rondaDeferred
            ? const Duration(seconds: 95)
            : aiMode == 'checklist_photo' ||
                aiMode == 'safety_observation_photo'
            ? const Duration(seconds: 55)"""
new_timeout = """    final requestTimeout =
        rondaDeferred
            ? const Duration(seconds: 90)
            : aiMode == 'checklist_photo' ||
                aiMode == 'safety_observation_photo'
            ? const Duration(seconds: 50)"""
if old_timeout not in ai:
    raise RuntimeError("timeout da IA foto nao localizado")
ai = ai.replace(old_timeout, new_timeout, 1)
write(rel, ai)

# ---------------------------------------------------------------------------
# Ronda UX: visible elapsed time, with proper cleanup.
# ---------------------------------------------------------------------------
rel = "lib/screens/express_round_screen.dart"
screen = read(rel)
if "Timer? _aiPhotoTimer;" not in screen:
    screen = once(
        screen,
        "  bool analyzingWithAi = false;\n",
        "  bool analyzingWithAi = false;\n"
        "  Timer? _aiPhotoTimer;\n"
        "  int _aiPhotoElapsedSeconds = 0;\n",
        "campos timer IA",
    )

if "_aiPhotoTimer?.cancel();" not in screen:
    dispose_anchor = "  void dispose() {"
    dispose_pos = screen.find(dispose_anchor)
    if dispose_pos < 0:
        raise RuntimeError("dispose da Ronda nao localizado")
    insert_pos = dispose_pos + len(dispose_anchor)
    screen = (
        screen[:insert_pos]
        + "\n    _aiPhotoTimer?.cancel();"
        + screen[insert_pos:]
    )

screen = once(
    screen,
    "    setState(() => analyzingWithAi = true);\n",
    """    _aiPhotoTimer?.cancel();
    setState(() {
      analyzingWithAi = true;
      _aiPhotoElapsedSeconds = 0;
    });
    _aiPhotoTimer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (mounted && analyzingWithAi) {
        setState(() => _aiPhotoElapsedSeconds++);
      }
    });
""",
    "inicio timer",
)

screen = once(
    screen,
    "    if (mounted) setState(() => analyzingWithAi = false);\n",
    """    _aiPhotoTimer?.cancel();
    if (mounted) {
      setState(() => analyzingWithAi = false);
    }
""",
    "fim timer",
)

screen = once(
    screen,
    """                  analyzingWithAi
                      ? 'Analisando...'
                      : 'IA foto · analisar evidência',""",
    """                  analyzingWithAi
                      ? 'IA analisando foto • ${_aiPhotoElapsedSeconds}s'
                      : 'IA foto · analisar evidência',""",
    "rotulo timer IA",
)
write(rel, screen)

# ---------------------------------------------------------------------------
# Release version only.
# ---------------------------------------------------------------------------
rel = "pubspec.yaml"
pub = read(rel)
old_version, new_version = (
    ("3.29.144+286", "3.29.145+287")
    if platform == "android"
    else ("3.30.63+250", "3.30.64+251")
)
marker = "version: " + old_version
if pub.count(marker) != 1:
    raise RuntimeError("versao esperada ausente: " + old_version)
write(rel, pub.replace(marker, "version: " + new_version, 1))

changed = [
    name for name, digest in before.items()
    if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest
]
if changed:
    raise SystemExit("PROTECTED_CORE_MODIFIED: " + repr(changed))

final_ai = read("lib/services/ai_assistant_service.dart")
final_round = read("lib/screens/express_round_screen.dart")
assert "import 'dart:isolate';" in final_ai
assert "_preparePhotoForAiAsync" in final_ai
assert "maxDimension: single ? 720" in final_ai
assert "'rondaDeferred': false" in final_ai
assert "'rondaDeferred': true" in final_ai
assert "const Duration(seconds: 50)" in final_ai
assert "const Duration(seconds: 90)" in final_ai
assert "IA analisando foto • ${_aiPhotoElapsedSeconds}s" in final_round
assert "version: " + new_version in read("pubspec.yaml")

print("AI_PHOTO_SPEED_OK", platform, new_version)
print("SYNC_DB_AUTH_MEDIA_DRIVE_GS_BYTE_IDENTICAL_OK")
