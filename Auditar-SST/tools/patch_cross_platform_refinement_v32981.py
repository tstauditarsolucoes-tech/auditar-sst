#!/usr/bin/env python3
from pathlib import Path
import re, sys

root=Path(sys.argv[1])
platform=(sys.argv[2] if len(sys.argv)>2 else 'android').lower()

def read(rel): return (root/rel).read_text(encoding='utf-8')
def write(rel,text): (root/rel).write_text(text,encoding='utf-8',newline='\n')
def once(text,old,new,label):
    if new in text: return text
    if old not in text: raise RuntimeError('Marcador ausente: '+label)
    return text.replace(old,new,1)

pub=read('pubspec.yaml')
version='3.30.9+196' if platform=='windows' else '3.29.81+223'
pub,n=re.subn(r'^version:\s*[^\n]+',f'version: {version}',pub,count=1,flags=re.M)
if n!=1: raise RuntimeError('Versão não localizada')
write('pubspec.yaml',pub)

rel='lib/services/ai_assistant_service.dart'
c=read(rel)
if "import 'web_service_config.dart';" not in c:
    c=once(c,"import 'management_panel_service.dart';\n","import 'management_panel_service.dart';\nimport 'web_service_config.dart';\n",'import web config IA')
pattern=re.compile(
r"""    final endpoint = \(await db\.getSetting\(
      'management_panel_endpoint',
      fallback: '',
    \)\)
        \.trim\(\);
    final syncKey = \(await db\.getSetting\(
      'management_panel_sync_key',
      fallback: '',
    \)\)
        \.trim\(\);""",re.S)
replacement="""    final savedEndpoint = (await db.getSetting(
      'management_panel_endpoint',
      fallback: '',
    )).trim();
    final savedSyncKey = (await db.getSetting(
      'management_panel_sync_key',
      fallback: '',
    )).trim();
    final endpoint = savedEndpoint.isNotEmpty
        ? savedEndpoint
        : WebServiceConfig.endpoint.trim();
    final syncKey = savedSyncKey.isNotEmpty
        ? savedSyncKey
        : WebServiceConfig.syncKey.trim();"""
c,n=pattern.subn(replacement,c,count=1)
if n!=1 and 'final savedEndpoint =' not in c: raise RuntimeError('Credenciais IA não localizadas')
write(rel,c)

rel='lib/services/training_import_service.dart'
s=read(rel)
if "package:image/image.dart' as img;" not in s:
    s=once(s,"import 'package:file_picker/file_picker.dart';\n","import 'package:file_picker/file_picker.dart';\nimport 'package:image/image.dart' as img;\n",'image import')
if "package:pdf/pdf.dart" not in s:
    s=once(s,"import 'package:pdf/widgets.dart' as pw;\n","import 'package:pdf/pdf.dart';\nimport 'package:pdf/widgets.dart' as pw;\n",'pdf format import')
if "import 'web_service_config.dart';" not in s:
    s=once(s,"import 'apps_script_http.dart';\n","import 'apps_script_http.dart';\nimport 'web_service_config.dart';\n",'web config training')

helper_anchor='class TrainingImportService {\n'
helper="""class TrainingImportService {
  static Future<Map<String, String>> _centralCredentials() async {
    final db = AppDatabase.instance;
    final savedEndpoint = (await db.getSetting(
      'management_panel_endpoint',
      fallback: '',
    )).trim();
    final savedSyncKey = (await db.getSetting(
      'management_panel_sync_key',
      fallback: '',
    )).trim();
    return <String, String>{
      'endpoint': savedEndpoint.isNotEmpty
          ? savedEndpoint
          : WebServiceConfig.endpoint.trim(),
      'syncKey': savedSyncKey.isNotEmpty
          ? savedSyncKey
          : WebServiceConfig.syncKey.trim(),
    };
  }

"""
if '_centralCredentials()' not in s:
    s=once(s,helper_anchor,helper,'helper credenciais training')

cred_patterns=[
re.compile(r"""    final endpoint=\(await AppDatabase\.instance\.getSetting\('management_panel_endpoint',fallback:''\)\)\.trim\(\);
    final syncKey=\(await AppDatabase\.instance\.getSetting\('management_panel_sync_key',fallback:''\)\)\.trim\(\);"""),
re.compile(r"""    final endpoint = \(await AppDatabase\.instance\.getSetting\(
      'management_panel_endpoint',
      fallback: '',
    \)\)\.trim\(\);
    final syncKey = \(await AppDatabase\.instance\.getSetting\(
      'management_panel_sync_key',
      fallback: '',
    \)\)\.trim\(\);""",re.S),
]
for p in cred_patterns:
    while True:
        m=p.search(s)
        if not m: break
        repl="""    final credentials = await _centralCredentials();
    final endpoint = credentials['endpoint'] ?? '';
    final syncKey = credentials['syncKey'] ?? '';"""
        s=s[:m.start()]+repl+s[m.end():]

start=s.find('  static Future<TrainingImportPreview> prepareFromImagePaths({')
end=s.find('  static _ParsedDocument _parsePhotoText(',start)
if start<0 or end<0: raise RuntimeError('prepareFromImagePaths não localizado')
new_photo=r'''  static Future<TrainingImportPreview> prepareFromImagePaths({
    required String companyId,
    required List<String> imagePaths,
  }) async {
    final paths = imagePaths
        .map((path) => path.trim())
        .where((path) => path.isNotEmpty)
        .take(8)
        .toList();
    if (paths.isEmpty) {
      throw const TrainingImportException('Nenhuma foto foi selecionada.');
    }

    final workers = await AppDatabase.instance.getWorkers(
      companyId: companyId,
      onlyActive: true,
    );
    if (workers.isEmpty) {
      throw const TrainingImportException(
        'Esta empresa ainda não possui trabalhadores ativos cadastrados.',
      );
    }
    final existing = await AppDatabase.instance.getTrainingControls(
      companyId: companyId,
    );

    var parsed = const _ParsedDocument(
      rows: <_RawTrainingRow>[],
      metadata: _TrainingMetadata(),
      fullText: '',
    );
    var aiUsed = false;
    final warnings = <String>[];

    if (!Platform.isWindows) {
      try {
        final recognizer = TextRecognizer(script: TextRecognitionScript.latin);
        final pages = <String>[];
        try {
          for (final path in paths) {
            final file = File(path);
            if (!await file.exists()) continue;
            final input = InputImage.fromFilePath(path);
            final recognized = await recognizer.processImage(input);
            final pageText = _normalizeText(recognized.text);
            if (pageText.isNotEmpty) pages.add(pageText);
          }
        } finally {
          await recognizer.close();
        }
        final text = _normalizeText(pages.join('\n'));
        if (text.isNotEmpty) {
          parsed = _parsePhotoText(text, workers);
        }
      } catch (_) {
        warnings.add(
          'A leitura local da foto não ficou disponível; a IA será usada como alternativa.',
        );
      }
    }

    final essentialsMissing = parsed.rows.isEmpty ||
        parsed.metadata.trainingDate == null ||
        (parsed.metadata.code.isEmpty && parsed.metadata.title.isEmpty);

    if (Platform.isWindows || essentialsMissing) {
      try {
        final photoPdf = await _buildPhotoPdf(paths);
        final ai = await _tryTrainingAi(
          photoPdf,
          workers,
          parsed,
          warnings,
          throwWhenNoLocalRows: parsed.rows.isEmpty,
        );
        if (ai != null) {
          parsed = ai;
          aiUsed = true;
        }
      } on TrainingImportException catch (error) {
        if (parsed.rows.isEmpty) rethrow;
        warnings.add('A IA não ficou disponível: \${error.message}');
      }
    }

    if (parsed.rows.isEmpty) {
      throw const TrainingImportException(
        'Não consegui identificar participantes nas fotos. Tente imagens mais nítidas, sem reflexo, ou use PDF/planilha.',
      );
    }

    final resolved = _matchRows(
      parsed.rows,
      workers: workers,
      existing: existing,
      defaultCode: parsed.metadata.code,
      defaultTitle: parsed.metadata.title,
      defaultTrainingDate: parsed.metadata.trainingDate,
    );

    if (parsed.metadata.trainingDate == null &&
        resolved.every((row) => row.trainingDate == null)) {
      warnings.add(
        'A data do treinamento não foi identificada. Informe-a antes de cadastrar.',
      );
    }
    if (parsed.metadata.expiryDate == null &&
        resolved.every((row) => row.expiryDate == null)) {
      warnings.add(
        'A validade não foi identificada. Você pode informá-la na conferência.',
      );
    }
    if (parsed.metadata.code.isEmpty &&
        parsed.metadata.title.isEmpty &&
        resolved.every((row) => row.code.isEmpty && row.title.isEmpty)) {
      warnings.add(
        'O treinamento não foi identificado. Informe o código ou título antes de cadastrar.',
      );
    }

    return TrainingImportPreview(
      fileName: paths.length == 1
          ? 'Foto da lista de treinamento'
          : '\${paths.length} fotos da lista de treinamento',
      method: Platform.isWindows
          ? 'Fotos • IA da Central'
          : (aiUsed
              ? 'Fotos • leitura local + IA'
              : 'Fotos • leitura inteligente local'),
      detectedCode: parsed.metadata.code,
      detectedTitle: parsed.metadata.title,
      detectedTrainingDate: parsed.metadata.trainingDate,
      detectedExpiryDate: parsed.metadata.expiryDate,
      rows: resolved,
      warnings: warnings,
      aiUsed: aiUsed,
    );
  }

  static Future<Uint8List> _buildPhotoPdf(List<String> paths) async {
    final doc = pw.Document(compress: true);
    var added = 0;
    for (final path in paths.take(8)) {
      final file = File(path);
      if (!await file.exists()) continue;
      final raw = await file.readAsBytes();
      final decoded = img.decodeImage(raw);
      if (decoded == null) continue;
      var normalized = img.bakeOrientation(decoded);
      final largest = normalized.width > normalized.height
          ? normalized.width
          : normalized.height;
      if (largest > 1500) {
        if (normalized.width >= normalized.height) {
          normalized = img.copyResize(normalized, width: 1500);
        } else {
          normalized = img.copyResize(normalized, height: 1500);
        }
      }
      final jpg = Uint8List.fromList(img.encodeJpg(normalized, quality: 72));
      final memory = pw.MemoryImage(jpg);
      doc.addPage(
        pw.Page(
          pageFormat: PdfPageFormat.a4,
          margin: const pw.EdgeInsets.all(12),
          build: (_) => pw.Center(
            child: pw.Image(memory, fit: pw.BoxFit.contain),
          ),
        ),
      );
      added++;
    }
    if (added == 0) {
      throw const TrainingImportException(
        'Não foi possível abrir as fotos selecionadas.',
      );
    }
    final bytes = Uint8List.fromList(await doc.save());
    if (bytes.length > 15000000) {
      throw const TrainingImportException(
        'As fotos ficaram muito grandes para análise. Selecione menos páginas por vez.',
      );
    }
    return bytes;
  }

'''
s=s[:start]+new_photo+s[end:]
s=s.replace(
'Se for um PDF escaneado, use também "Tirar foto da lista", que funciona localmente.',
'Se for um PDF escaneado, tente também a leitura por fotos.'
)
write(rel,s)

rel='lib/screens/training_import_screen.dart'
ui=read(rel)
if "import 'dart:io';" not in ui:
    ui="import 'dart:io';\n\n"+ui
old="""  Future<void> _takePhotosAndAnalyze() async {
    if (busy) return;
    final paths = <String>[];
"""
new="""  Future<void> _takePhotosAndAnalyze() async {
    if (busy) return;
    if (Platform.isWindows) {
      await _pickPhotosAndAnalyze();
      return;
    }
    final paths = <String>[];
"""
ui=once(ui,old,new,'Windows fotos training')
ui=ui.replace(
"""                  const Text(
                    'Importe PDF, XLSX, XLS ou CSV, ou fotografe a lista. Fotos são lidas no próprio aparelho e comparadas apenas com os trabalhadores desta empresa. Nada é cadastrado antes da sua confirmação.',
                    style: TextStyle(fontSize: 12.5),
                  ),""",
"""                  Text(
                    Platform.isWindows
                        ? 'Importe PDF, XLSX, XLS ou CSV, ou selecione fotos da lista. No computador, as fotos são analisadas pela IA da Central e comparadas somente com os trabalhadores desta empresa. Nada é cadastrado antes da sua confirmação.'
                        : 'Importe PDF, XLSX, XLS ou CSV, ou fotografe a lista. O app tenta leitura local e usa a IA quando necessário. Nada é cadastrado antes da sua confirmação.',
                    style: const TextStyle(fontSize: 12.5),
                  ),"""
)
ui=ui.replace(
"""                        icon: const Icon(Icons.photo_camera_outlined),
                        label: const Text('Tirar foto da lista'),""",
"""                        icon: Icon(
                          Platform.isWindows
                              ? Icons.add_photo_alternate_outlined
                              : Icons.photo_camera_outlined,
                        ),
                        label: Text(
                          Platform.isWindows
                              ? 'Selecionar fotos da lista'
                              : 'Tirar foto da lista',
                        ),"""
)
ui=ui.replace(
"""                    const Text(
                      'Para listas com várias páginas, tire uma foto por página. O app pergunta se deseja adicionar a próxima.',
                      style: TextStyle(fontSize: 11.5, color: Colors.black54),
                    ),""",
"""                    Text(
                      Platform.isWindows
                          ? 'Selecione até 8 fotos, uma por página. A IA lê o conjunto e você confere os dados antes de cadastrar.'
                          : 'Para listas com várias páginas, tire uma foto por página. O app pergunta se deseja adicionar a próxima.',
                      style: const TextStyle(fontSize: 11.5, color: Colors.black54),
                    ),"""
)
write(rel,ui)

rel='lib/screens/facial_confirmation_screen.dart'
if (root/rel).exists():
    f=read(rel)
    f=f.replace(
"""        source: ImageSource.camera,
        preferredCameraDevice: CameraDevice.front,""",
"""        source: Platform.isWindows ? ImageSource.gallery : ImageSource.camera,
        preferredCameraDevice: CameraDevice.front,"""
)
    f=f.replace(
"""              label: Text(ready ? 'Refazer foto' : 'Abrir câmera frontal'),""",
"""              label: Text(
                Platform.isWindows
                    ? (ready ? 'Selecionar outra foto' : 'Selecionar foto')
                    : (ready ? 'Refazer foto' : 'Abrir câmera frontal'),
              ),"""
)
    f=f.replace(
"""                      'A câmera frontal registra a foto no momento da ficha. O Auditar vincula a imagem ao participante, data/hora e gera um código de comprovação da evidência.',""",
"""                      Platform.isWindows
                          ? 'No computador, selecione uma foto atual do participante. O Auditar vincula a imagem ao participante, data/hora e gera um código de comprovação da evidência.'
                          : 'A câmera frontal registra a foto no momento da ficha. O Auditar vincula a imagem ao participante, data/hora e gera um código de comprovação da evidência.',"""
)
    f=f.replace(
        "const Text(\n                      Platform.isWindows",
        "Text(\n                      Platform.isWindows",
        1,
    )
    write(rel,f)

rel='lib/screens/express_round_screen.dart'
r=read(rel)
old="""  Future<void> _pickPhoto(ImageSource source) async {
    final image = await picker.pickImage(
      source: source,
"""
new="""  Future<void> _pickPhoto(ImageSource source) async {
    final effectiveSource =
        Platform.isWindows && source == ImageSource.camera
            ? ImageSource.gallery
            : source;
    final image = await picker.pickImage(
      source: effectiveSource,
"""
r=once(r,old,new,'ronda foto Windows')
write(rel,r)

rel='lib/screens/checklist_screen.dart'
k=read(rel)
k=k.replace(
"""    final image = await picker.pickImage(
      source: ImageSource.camera,""",
"""    final image = await picker.pickImage(
      source: Platform.isWindows ? ImageSource.gallery : ImageSource.camera,""",
1)
write(rel,k)

rel='lib/screens/non_conformity_detail_screen.dart'
if (root/rel).exists():
    n=read(rel)
    n=n.replace(
      'source: ImageSource.camera,',
      'source: Platform.isWindows ? ImageSource.gallery : ImageSource.camera,'
    )
    write(rel,n)

assert f'version: {version}' in read('pubspec.yaml')
assert 'WebServiceConfig.endpoint' in read('lib/services/ai_assistant_service.dart')
assert 'Fotos • IA da Central' in read('lib/services/training_import_service.dart')
assert '_buildPhotoPdf' in read('lib/services/training_import_service.dart')
assert 'Selecionar fotos da lista' in read('lib/screens/training_import_screen.dart')
assert 'effectiveSource' in read('lib/screens/express_round_screen.dart')
print('CROSS_PLATFORM_REFINEMENT_OK',platform,version)
