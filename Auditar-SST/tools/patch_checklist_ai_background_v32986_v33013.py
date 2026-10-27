#!/usr/bin/env python3
from pathlib import Path
import re, shutil, sys

if len(sys.argv) < 2:
    raise SystemExit("uso: patch_checklist_ai_background_v32986_v33013.py <APP_DIR> [android|windows]")

root = Path(sys.argv[1])
platform = (sys.argv[2] if len(sys.argv) > 2 else "android").lower()
repo = Path.cwd()

def read(rel):
    return (root / rel).read_text(encoding="utf-8")

def write(rel, text):
    (root / rel).write_text(text, encoding="utf-8", newline="\n")

def insert_import(text, statement):
    if statement in text:
        return text
    imports = list(re.finditer(r"(?m)^import\s+[^;]+;\s*$", text))
    if not imports:
        raise RuntimeError("nenhum import localizado")
    pos = imports[-1].end()
    return text[:pos] + "\n" + statement + text[pos:]

def replace_dart_method(text, signature, replacement):
    start = text.find(signature)
    if start < 0:
        raise RuntimeError("método não localizado: " + signature)
    brace = text.find("{", start)
    if brace < 0:
        raise RuntimeError("abertura do método não localizada: " + signature)

    depth = 0
    quote = None
    escape = False
    line_comment = False
    block_comment = False
    i = brace
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""

        if line_comment:
            if ch == "\n":
                line_comment = False
            i += 1
            continue
        if block_comment:
            if ch == "*" and nxt == "/":
                block_comment = False
                i += 2
                continue
            i += 1
            continue
        if quote:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == quote:
                quote = None
            i += 1
            continue

        if ch == "/" and nxt == "/":
            line_comment = True
            i += 2
            continue
        if ch == "/" and nxt == "*":
            block_comment = True
            i += 2
            continue
        if ch in ("'", '"'):
            quote = ch
            i += 1
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                return text[:start] + replacement.rstrip() + text[end:]
        i += 1
    raise RuntimeError("fim do método não localizado: " + signature)

src = repo / "build_sources/v3.29.86-background-ai/inspection_photo_ai_queue_service.dart"
dst = root / "lib/services/inspection_photo_ai_queue_service.dart"
dst.parent.mkdir(parents=True, exist_ok=True)
shutil.copyfile(src, dst)

rel = "lib/screens/checklist_screen.dart"
c = read(rel)
c = insert_import(c, "import 'dart:async';")
c = insert_import(c, "import '../services/inspection_photo_ai_queue_service.dart';")

old_pending = """  void _markAiPhotoPending(String itemId) {
    final status = statuses[itemId] ?? '';
    final hasPhotos = (photos[itemId] ?? const <String>[]).isNotEmpty;
    if ((status == 'Não Conforme' || status == 'Parcial') && hasPhotos) {
      aiPhotoMeta[itemId] = <String, dynamic>{
        'status': 'PENDENTE',
        'queuedAt': DateTime.now().toUtc().toIso8601String(),
        'lastError': '',
      };
    } else {
      aiPhotoMeta[itemId] = <String, dynamic>{};
    }
  }
"""
new_pending = """  void _markAiPhotoPending(String itemId) {
    final status = statuses[itemId] ?? '';
    final hasPhotos = (photos[itemId] ?? const <String>[]).isNotEmpty;
    if ((status == 'Não Conforme' || status == 'Parcial') && hasPhotos) {
      aiPhotoMeta[itemId] = <String, dynamic>{
        'status': 'PENDENTE',
        'queuedAt': DateTime.now().toUtc().toIso8601String(),
        'lastError': '',
      };
    } else {
      aiPhotoMeta[itemId] = <String, dynamic>{};
    }
    InspectionPhotoAiQueueService.rememberMeta(
      widget.inspection.id,
      itemId,
      aiPhotoMeta[itemId] ?? const <String, dynamic>{},
    );
  }
"""
if new_pending not in c:
    if old_pending not in c:
        raise RuntimeError("_markAiPhotoPending não localizado")
    c = c.replace(old_pending, new_pending, 1)

old_current = """    final currentAi = Map<String, dynamic>.from(
      aiPhotoMeta[itemId] ?? const <String, dynamic>{},
    );
"""
new_current = """    final liveAi = InspectionPhotoAiQueueService.liveMeta(
      widget.inspection.id,
      itemId,
    );
    if (liveAi != null) {
      aiPhotoMeta[itemId] = Map<String, dynamic>.from(liveAi);
    }
    final currentAi = Map<String, dynamic>.from(
      liveAi ?? aiPhotoMeta[itemId] ?? const <String, dynamic>{},
    );
"""
if new_current not in c:
    if old_current not in c:
        raise RuntimeError("meta local da IA não localizada")
    c = c.replace(old_current, new_current, 1)

new_analyze = r'''  Future<void> _analyzeWithAi(ChecklistItem item) async {
    final evidence = photos[item.id] ?? const <String>[];
    if (evidence.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Tire ou escolha pelo menos uma foto antes de analisar.'),
        ),
      );
      return;
    }

    final currentStatus = statuses[item.id] ?? '';
    if (currentStatus != 'Não Conforme' && currentStatus != 'Parcial') {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Para análise de evidência, marque primeiro o item como Não Conforme ou Parcial.',
          ),
        ),
      );
      return;
    }

    final inspectionId = widget.inspection.id;
    final queueWasRunning =
        InspectionPhotoAiQueueService.isRunning(inspectionId);

    setState(() {
      _markAiPhotoPending(item.id);
      if (!queueWasRunning) {
        analyzingItems.add(item.id);
      }
    });

    await _saveDraft();
    if (!mounted) return;

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          queueWasRunning
              ? 'Foto adicionada à fila da IA. Continue a vistoria normalmente.'
              : 'IA iniciada em segundo plano. Pode continuar descendo e preenchendo a vistoria.',
        ),
        duration: const Duration(seconds: 4),
      ),
    );

    if (queueWasRunning) {
      return;
    }

    unawaited(
      InspectionPhotoAiQueueService.processPending(inspectionId)
          .then((summary) async {
        final answers = await AppDatabase.instance.getAnswers(inspectionId);
        final refreshed = <String, Map<String, dynamic>>{};
        for (final answer in answers) {
          final raw = answer.occurrencesJson.trim();
          if (raw.isEmpty) continue;
          try {
            final decoded = jsonDecode(raw);
            if (decoded is! Map) continue;
            final meta = decoded['aiPhoto'];
            if (meta is Map) {
              refreshed[answer.questionId] =
                  Map<String, dynamic>.from(meta);
            }
          } catch (_) {}
        }

        if (!mounted) return;
        setState(() {
          for (final entry in refreshed.entries) {
            aiPhotoMeta[entry.key] = entry.value;
          }
          analyzingItems.clear();
        });

        if (summary.completed > 0) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(
                'IA concluiu ${summary.completed} análise(s). As sugestões ficaram salvas para revisar no final.',
              ),
              duration: const Duration(seconds: 4),
            ),
          );
        } else if (summary.failed > 0) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text(
                'Algumas fotos ficaram pendentes por instabilidade da Central. Você pode tentar novamente no final da vistoria.',
              ),
              duration: Duration(seconds: 4),
            ),
          );
        }
      }).catchError((_) {
        if (!mounted) return;
        setState(() => analyzingItems.clear());
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text(
              'A análise ficou pendente. A foto continua salva e pode ser processada no final da vistoria.',
            ),
          ),
        );
      }),
    );
  }'''

c = replace_dart_method(
    c,
    "  Future<void> _analyzeWithAi(ChecklistItem item) async",
    new_analyze,
)

c = c.replace(
    "'Analisando fotos...'",
    "'IA trabalhando em segundo plano...'",
)
c = c.replace(
    "'Analisar em segundo plano com IA (opcional)'",
    "'Enviar para fila da IA (opcional)'",
)
c = c.replace(
    "Você pode continuar respondendo o checklist enquanto a IA analisa. Quando terminar, a sugestão ficará salva para revisão e não abrirá nenhuma janela automaticamente. Se preferir, também pode analisar depois pela tela Relatórios. Evite rostos, crachás, documentos e outros dados pessoais.",
    "Você pode continuar descendo e respondendo o checklist enquanto a IA trabalha. Nenhuma janela será aberta quando terminar. Se preferir, não analise agora: no final da vistoria use “Analisar todas as fotos pendentes”. Evite rostos, crachás, documentos e outros dados pessoais.",
)
write(rel, c)

rel = "lib/screens/report_screen.dart"
r = read(rel)
r = r.replace(
    "'Analisar fotos em segundo plano'",
    "'Analisar todas as fotos pendentes'",
)
r = r.replace(
    "Você pode gerar e compartilhar o relatório agora. As fotos de itens Não Conforme/Parcial podem ser analisadas depois; a IA prepara sugestões e só altera o registro após sua aprovação.",
    "As fotos de itens Não Conforme/Parcial podem ser analisadas aqui, depois que a coleta de campo terminar. A IA trabalha em fila, prepara sugestões e só altera o registro após sua aprovação.",
)
write(rel, r)

rel = "pubspec.yaml"
pub = read(rel)
version = "3.30.13+200" if platform == "windows" else "3.29.86+228"
pub, count = re.subn(
    r"(?m)^version:\s*[^\r\n]+",
    "version: " + version,
    pub,
    count=1,
)
if count != 1:
    raise RuntimeError("versão não localizada")
write(rel, pub)

queue = read("lib/services/inspection_photo_ai_queue_service.dart")
check = read("lib/screens/checklist_screen.dart")
report = read("lib/screens/report_screen.dart")
for marker in [
    "_analyzeWithRetry",
    "attempt <= 3",
    "_latestAnswer",
    "_photoFingerprint",
    "rememberMeta",
    "liveMeta",
    "A evidência mudou durante a análise",
]:
    assert marker in queue, "fila sem marcador: " + marker
for marker in [
    "Enviar para fila da IA (opcional)",
    "IA iniciada em segundo plano",
    "InspectionPhotoAiQueueService.processPending",
]:
    assert marker in check, "checklist sem marcador: " + marker
assert "Analisar todas as fotos pendentes" in report
assert f"version: {version}" in read("pubspec.yaml")
print("CHECKLIST_AI_BACKGROUND_OK", platform, version)
