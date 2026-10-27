#!/usr/bin/env python3
from pathlib import Path
import re, sys

root=Path(sys.argv[1])

def read(rel):
    return (root/rel).read_text(encoding='utf-8')

def write(rel,text):
    (root/rel).write_text(text,encoding='utf-8',newline='\n')

def replace_once(text,old,new,label):
    if old not in text:
        raise RuntimeError('Marcador não localizado: '+label)
    return text.replace(old,new,1)

# versão
pub=read('pubspec.yaml')
pub,n=re.subn(r'^version:\s*[^\n]+','version: 3.29.79+221',pub,count=1,flags=re.M)
if n!=1: raise RuntimeError('Versão não localizada')
write('pubspec.yaml',pub)

# ------------------------------------------------------------
# Relatório legado: resumo dos valores de multa mostrados
# ------------------------------------------------------------
rel='lib/services/pdf_service.dart'
c=read(rel)

marker="""    final actions = await db.getActionsForInspection(inspectionId);
    final ncs = await db.getNonConformitiesForInspection(inspectionId);
"""
insert="""    final actions = await db.getActionsForInspection(inspectionId);
    final ncs = await db.getNonConformitiesForInspection(inspectionId);
    final reportFineValues = answers
        .map(_fineAmountCentsForReport)
        .whereType<int>()
        .toList();
    final reportFineTotalCents = reportFineValues.fold<int>(
      0,
      (sum, value) => sum + value,
    );
"""
c=replace_once(c,marker,insert,'fine summary legacy vars')

marker="""      _distributionCard(
        conformes: conformes,
        naoConformes: naoConformes,
        parciais: parciais,
        naoAplicaveis: naoAplicaveis,
        total: total,
      ),
      pw.SizedBox(height: 16),
"""
insert="""      _distributionCard(
        conformes: conformes,
        naoConformes: naoConformes,
        parciais: parciais,
        naoAplicaveis: naoAplicaveis,
        total: total,
      ),
      if (reportFineValues.isNotEmpty) ...[
        pw.SizedBox(height: 10),
        _fineSummaryCard(
          count: reportFineValues.length,
          totalCents: reportFineTotalCents,
        ),
      ],
      pw.SizedBox(height: 16),
"""
c=replace_once(c,marker,insert,'fine summary legacy widget')

marker="""  static String _fineForReport(InspectionAnswer answer) {
"""
helper="""  static int? _fineAmountCentsForReport(InspectionAnswer answer) {
    final raw = answer.occurrencesJson.trim();
    if (raw.isEmpty) return null;
    try {
      final decoded = jsonDecode(raw);
      if (decoded is! Map) return null;
      final fine = decoded['fine'];
      if (fine is! Map || fine['showInReport'] != true) return null;
      final rawCents = fine['amountCents'];
      if (rawCents is num && rawCents > 0) return rawCents.round();

      var legacy = '${fine['amount'] ?? ''}'.trim();
      legacy = legacy.replaceAll('R\\$', '').replaceAll(' ', '');
      if (legacy.contains(',')) {
        legacy = legacy.replaceAll('.', '').replaceAll(',', '.');
      }
      final value = double.tryParse(legacy);
      if (value == null || value <= 0) return null;
      return (value * 100).round();
    } catch (_) {
      return null;
    }
  }

  static pw.Widget _fineSummaryCard({
    required int count,
    required int totalCents,
  }) {
    final total = NumberFormat.currency(
      locale: 'pt_BR',
      symbol: 'R\\$',
      decimalDigits: 2,
    ).format(totalCents / 100);
    return pw.Container(
      width: double.infinity,
      padding: const pw.EdgeInsets.all(10),
      decoration: pw.BoxDecoration(
        color: PdfColors.orange50,
        border: pw.Border.all(color: PdfColors.orange200),
        borderRadius: pw.BorderRadius.circular(6),
      ),
      child: pw.Column(
        crossAxisAlignment: pw.CrossAxisAlignment.start,
        children: [
          pw.Text(
            'VALORES DE MULTA INFORMADOS',
            style: pw.TextStyle(
              fontSize: 8.5,
              fontWeight: pw.FontWeight.bold,
              color: _amber,
            ),
          ),
          pw.SizedBox(height: 3),
          pw.Text(
            '$count item(ns) com valor exibido • Total de referência: $total',
            style: pw.TextStyle(
              fontSize: 9,
              fontWeight: pw.FontWeight.bold,
              color: _navy,
            ),
          ),
          pw.SizedBox(height: 2),
          pw.Text(
            'Soma dos valores informados manualmente no checklist. Não representa cálculo oficial de penalidade, auto de infração ou valor definitivo de fiscalização.',
            style: const pw.TextStyle(fontSize: 6.8, color: _grey),
          ),
        ],
      ),
    );
  }

  static String _fineForReport(InspectionAnswer answer) {
"""
c=replace_once(c,marker,helper,'fine summary legacy helpers')
write(rel,c)

# ------------------------------------------------------------
# Relatório por modelo: resumo dos valores
# ------------------------------------------------------------
rel='lib/services/styled_report_pdf_service.dart'
c=read(rel)

styled_conformity_pattern = re.compile(
    r"(\s*final conformity\s*=\s*considered\s*==\s*0\s*\?\s*0\s*:\s*\(conformes\s*/\s*considered\s*\*\s*100\)\.round\(\);)",
    re.S,
)
m=styled_conformity_pattern.search(c)
if not m:
    raise RuntimeError('Marcador não localizado: fine summary styled vars')
styled_fine_vars = m.group(1) + """
    final reportFineValues = answers
        .map(_fineAmountCentsForReport)
        .whereType<int>()
        .toList();
    final reportFineTotalCents = reportFineValues.fold<int>(
      0,
      (sum, value) => sum + value,
    );"""
c = c[:m.start()] + styled_fine_vars + c[m.end():]

marker="""        _summaryGrid(
          conformity: conformity,
          conformes: conformes,
          parciais: parciais,
          naoConformes: naoConformes,
          primary: primary,
          secondary: secondary,
        ),
        pw.SizedBox(height: 16),
"""
insert="""        _summaryGrid(
          conformity: conformity,
          conformes: conformes,
          parciais: parciais,
          naoConformes: naoConformes,
          primary: primary,
          secondary: secondary,
        ),
        if (reportFineValues.isNotEmpty) ...[
          pw.SizedBox(height: 9),
          _fineSummaryCard(
            count: reportFineValues.length,
            totalCents: reportFineTotalCents,
            primary: primary,
          ),
        ],
        pw.SizedBox(height: 16),
"""
c=replace_once(c,marker,insert,'fine summary styled widget')

marker="""  static String _fineForReport(InspectionAnswer answer) {
"""
helper="""  static int? _fineAmountCentsForReport(InspectionAnswer answer) {
    final raw = answer.occurrencesJson.trim();
    if (raw.isEmpty) return null;
    try {
      final decoded = jsonDecode(raw);
      if (decoded is! Map) return null;
      final fine = decoded['fine'];
      if (fine is! Map || fine['showInReport'] != true) return null;
      final rawCents = fine['amountCents'];
      if (rawCents is num && rawCents > 0) return rawCents.round();

      var legacy = '${fine['amount'] ?? ''}'.trim();
      legacy = legacy.replaceAll('R\\$', '').replaceAll(' ', '');
      if (legacy.contains(',')) {
        legacy = legacy.replaceAll('.', '').replaceAll(',', '.');
      }
      final value = double.tryParse(legacy);
      if (value == null || value <= 0) return null;
      return (value * 100).round();
    } catch (_) {
      return null;
    }
  }

  static pw.Widget _fineSummaryCard({
    required int count,
    required int totalCents,
    required PdfColor primary,
  }) {
    final total = NumberFormat.currency(
      locale: 'pt_BR',
      symbol: 'R\\$',
      decimalDigits: 2,
    ).format(totalCents / 100);
    return pw.Container(
      width: double.infinity,
      padding: const pw.EdgeInsets.all(10),
      decoration: pw.BoxDecoration(
        color: PdfColors.orange50,
        border: pw.Border.all(color: PdfColors.orange200),
        borderRadius: pw.BorderRadius.circular(5),
      ),
      child: pw.Column(
        crossAxisAlignment: pw.CrossAxisAlignment.start,
        children: [
          pw.Text(
            'Valores de multa informados',
            style: pw.TextStyle(
              fontSize: 9,
              fontWeight: pw.FontWeight.bold,
              color: primary,
            ),
          ),
          pw.SizedBox(height: 3),
          pw.Text(
            '$count item(ns) • Total de referência: $total',
            style: pw.TextStyle(
              fontSize: 8.5,
              fontWeight: pw.FontWeight.bold,
            ),
          ),
          pw.SizedBox(height: 2),
          pw.Text(
            'Soma de referências manuais selecionadas para aparecer no relatório; não constitui cálculo oficial de penalidade ou fiscalização.',
            style: const pw.TextStyle(
              fontSize: 6.8,
              color: PdfColors.grey700,
            ),
          ),
        ],
      ),
    );
  }

  static String _fineForReport(InspectionAnswer answer) {
"""
c=replace_once(c,marker,helper,'fine summary styled helpers')
write(rel,c)

# ------------------------------------------------------------
# Treinamento: confirmação antes de substituir + metadados limpos
# + código/data visíveis e preview ampliado
# ------------------------------------------------------------
rel='lib/screens/training_records_screen.dart'
c=read(rel)

marker="""  Future<void> _sign(Map<String, dynamic> participant) async {
"""
helper="""  Future<bool> _confirmReplaceTrainingConfirmation(
    Map<String, dynamic> participant,
    String newMethod,
  ) async {
    if ('${participant['status'] ?? ''}' != 'ASSINADO') return true;
    final name = '${participant['name'] ?? 'Participante'}'.trim();
    final currentMethod =
        '${participant['confirmationMethod'] ?? 'signature'}' == 'face'
            ? 'assinatura facial'
            : 'assinatura na tela';
    final result = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Substituir confirmação?'),
        content: Text(
          '$name já possui $currentMethod. Ao continuar, a ficha passará a usar $newMethod como comprovação atual.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext, false),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(dialogContext, true),
            child: const Text('Substituir'),
          ),
        ],
      ),
    );
    return result == true;
  }

  Future<void> _previewTrainingEvidence(
    Map<String, dynamic> participant,
    String path,
  ) async {
    if (path.isEmpty || !File(path).existsSync()) return;
    final name = '${participant['name'] ?? 'Participante'}';
    final method = '${participant['confirmationMethod'] ?? 'signature'}';
    final proof = '${participant['faceProofCode'] ?? ''}'.trim();
    final signedAt =
        DateTime.tryParse('${participant['signedAt'] ?? ''}')?.toLocal();
    await showDialog<void>(
      context: context,
      builder: (dialogContext) => Dialog(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 560, maxHeight: 720),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              ListTile(
                leading: Icon(
                  method == 'face' ? Icons.face_outlined : Icons.draw_outlined,
                ),
                title: Text(
                  name,
                  style: const TextStyle(fontWeight: FontWeight.w800),
                ),
                subtitle: Text(
                  [
                    method == 'face' ? 'Assinatura facial' : 'Assinatura na tela',
                    if (proof.isNotEmpty) proof,
                    if (signedAt != null)
                      DateFormat('dd/MM/yyyy HH:mm').format(signedAt),
                  ].join(' • '),
                ),
                trailing: IconButton(
                  onPressed: () => Navigator.pop(dialogContext),
                  icon: const Icon(Icons.close),
                ),
              ),
              Flexible(
                child: Container(
                  width: double.infinity,
                  color: Colors.black,
                  padding: const EdgeInsets.all(8),
                  child: InteractiveViewer(
                    minScale: .8,
                    maxScale: 4,
                    child: Image.file(
                      File(path),
                      fit: method == 'face' ? BoxFit.contain : BoxFit.contain,
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _sign(Map<String, dynamic> participant) async {
"""
c=replace_once(c,marker,helper,'training replace helpers')

# _sign: confirmação e limpeza de metadados faciais
marker="""  Future<void> _sign(Map<String, dynamic> participant) async {
    if (finalized) return;
    final result = await Navigator.of(context).push<TrainingSignatureResult>(
"""
insert="""  Future<void> _sign(Map<String, dynamic> participant) async {
    if (finalized) return;
    if (!await _confirmReplaceTrainingConfirmation(
      participant,
      'a assinatura na tela',
    )) {
      return;
    }
    final previousId = '${participant['signatureId'] ?? ''}'.trim();
    final previousMethod =
        '${participant['confirmationMethod'] ?? 'signature'}';
    final result = await Navigator.of(context).push<TrainingSignatureResult>(
"""
c=replace_once(c,marker,insert,'training sign confirm')

marker="""    if (result == null || !mounted) return;

    await MediaSyncService.registerTrainingRecordSignature(
"""
insert="""    if (result == null || !mounted) return;

    if (previousId.isNotEmpty && previousMethod == 'face') {
      await FacialConfirmationService.remove(
        entityType: 'training_face_signature',
        confirmationId: previousId,
      );
    }
    await MediaSyncService.registerTrainingRecordSignature(
"""
c=replace_once(c,marker,insert,'training sign cleanup face')

training_signature_meta_pattern = re.compile(
    r"(['\"]confirmationMethod['\"]\s*:\s*['\"]signature['\"]\s*,)",
    re.S,
)
m=training_signature_meta_pattern.search(c)
if not m:
    raise RuntimeError('Marcador não localizado: training sign clear face metadata')
training_signature_meta = m.group(1) + """
            'faceProofCode': '',
            'facePhotoSha256': '',
            'faceConsentVersion': '',"""
c = c[:m.start()] + training_signature_meta + c[m.end():]

# _face confirmação
marker="""  Future<void> _face(Map<String, dynamic> participant) async {
    if (finalized) return;
    final name = '${participant['name'] ?? ''}'.trim();
"""
insert="""  Future<void> _face(Map<String, dynamic> participant) async {
    if (finalized) return;
    if (!await _confirmReplaceTrainingConfirmation(
      participant,
      'a assinatura facial',
    )) {
      return;
    }
    final name = '${participant['name'] ?? ''}'.trim();
"""
c=replace_once(c,marker,insert,'training face confirm')

# status não assinado: limpar facial e mídia facial
marker="""  Future<void> _setParticipantStatus(
    Map<String, dynamic> participant,
    String status,
  ) async {
    if (finalized) return;
    final id = '${participant['id'] ?? ''}';
"""
insert="""  Future<void> _setParticipantStatus(
    Map<String, dynamic> participant,
    String status,
  ) async {
    if (finalized) return;
    final signatureId = '${participant['signatureId'] ?? ''}'.trim();
    final confirmationMethod =
        '${participant['confirmationMethod'] ?? 'signature'}';
    if (status != 'ASSINADO' &&
        signatureId.isNotEmpty &&
        confirmationMethod == 'face') {
      await FacialConfirmationService.remove(
        entityType: 'training_face_signature',
        confirmationId: signatureId,
      );
      mediaPaths.remove('signature:$signatureId');
    }
    final id = '${participant['id'] ?? ''}';
"""
c=replace_once(c,marker,insert,'training status cleanup')

training_status_meta_pattern = re.compile(
    r"(if\s*\(status\s*!=\s*['\"]ASSINADO['\"]\)\s*['\"]confirmationMethod['\"]\s*:\s*['\"]['\"]\s*,)",
    re.S,
)
m=training_status_meta_pattern.search(c)
if not m:
    raise RuntimeError('Marcador não localizado: training status metadata cleanup')
training_status_meta = m.group(1) + """
            if (status != 'ASSINADO') 'faceProofCode': '',
            if (status != 'ASSINADO') 'facePhotoSha256': '',
            if (status != 'ASSINADO') 'faceConsentVersion': '',"""
c = c[:m.start()] + training_status_meta + c[m.end():]

# UI: variáveis proof/time
participants_anchor = c.find("participants.map((participant)")
if participants_anchor < 0:
    raise RuntimeError('Marcador não localizado: training participant card anchor')
training_ui_vars_pattern = re.compile(
    r"(\s*final confirmationMethod\s*=\s*['\"]\$\{participant\['confirmationMethod'\]\s*\?\?\s*'signature'\}['\"]\s*;)",
    re.S,
)
m=training_ui_vars_pattern.search(c, participants_anchor)
if not m:
    raise RuntimeError('Marcador não localizado: training ui proof vars')
training_ui_vars = m.group(1) + """
              final proofCode =
                  '${participant['faceProofCode'] ?? ''}'.trim();
              final signedAt =
                  DateTime.tryParse('${participant['signedAt'] ?? ''}')
                      ?.toLocal();"""
c = c[:m.start()] + training_ui_vars + c[m.end():]

training_ui_status_pattern = re.compile(
    r"(if\s*\(status\s*==\s*['\"]ASSINADO['\"]\)\s*confirmationMethod\s*==\s*['\"]face['\"]\s*\?\s*['\"]FACIAL['\"]\s*:\s*['\"]ASSINATURA['\"]\s*,)",
    re.S,
)
m=training_ui_status_pattern.search(c)
if not m:
    raise RuntimeError('Marcador não localizado: training ui proof subtitle')
training_ui_status = m.group(1) + """
                          if (confirmationMethod == 'face' &&
                              proofCode.isNotEmpty)
                            proofCode,
                          if (status == 'ASSINADO' && signedAt != null)
                            DateFormat('dd/MM/yyyy HH:mm').format(signedAt),"""
c = c[:m.start()] + training_ui_status + c[m.end():]

# preview tappable
pattern=re.compile(
    r"""if \(signaturePath\.isNotEmpty &&\s*File\(signaturePath\)\.existsSync\(\)\)\s*Container\(\s*height: 58,.*?\n\s*\),\s*\n\s*\],""",
    re.S,
)
match=pattern.search(c)
if not match:
    raise RuntimeError('Marcador não localizado: training preview image')
replacement="""if (signaturePath.isNotEmpty &&
                        File(signaturePath).existsSync())
                      InkWell(
                        onTap: () => _previewTrainingEvidence(
                          participant,
                          signaturePath,
                        ),
                        child: Container(
                          height: confirmationMethod == 'face' ? 96 : 58,
                          width: double.infinity,
                          margin: const EdgeInsets.fromLTRB(14, 0, 14, 12),
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(10),
                            border: Border.all(
                              color: const Color(0xFFE2E7EC),
                            ),
                          ),
                          clipBehavior: Clip.antiAlias,
                          child: Stack(
                            fit: StackFit.expand,
                            children: [
                              Image.file(
                                File(signaturePath),
                                fit: confirmationMethod == 'face'
                                    ? BoxFit.cover
                                    : BoxFit.contain,
                              ),
                              Positioned(
                                right: 6,
                                bottom: 6,
                                child: DecoratedBox(
                                  decoration: BoxDecoration(
                                    color: Colors.black54,
                                    borderRadius: BorderRadius.circular(12),
                                  ),
                                  child: const Padding(
                                    padding: EdgeInsets.symmetric(
                                      horizontal: 7,
                                      vertical: 3,
                                    ),
                                    child: Text(
                                      'Toque para ampliar',
                                      style: TextStyle(
                                        color: Colors.white,
                                        fontSize: 10,
                                      ),
                                    ),
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                  ],"""
c=c[:match.start()]+replacement+c[match.end():]
write(rel,c)

# ------------------------------------------------------------
# DDS: confirmação antes de substituir, limpeza cruzada e preview
# ------------------------------------------------------------
rel='lib/screens/sst_record_form_screen.dart'
c=read(rel)

marker="""  Future<void> _collectDdsSignature([Map<String, dynamic>? current]) async {
"""
helper="""  Future<bool> _confirmReplaceDdsConfirmation(
    Map<String, dynamic>? current,
    String newMethod,
  ) async {
    if (current == null) return true;
    final name = '${current['name'] ?? 'Participante'}'.trim();
    final currentMethod =
        '${current['method'] ?? 'signature'}' == 'face'
            ? 'assinatura facial'
            : 'assinatura na tela';
    final result = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Substituir confirmação?'),
        content: Text(
          '$name já possui $currentMethod. Ao continuar, ela será substituída por $newMethod.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext, false),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(dialogContext, true),
            child: const Text('Substituir'),
          ),
        ],
      ),
    );
    return result == true;
  }

  Future<void> _previewDdsEvidence(
    Map<String, dynamic> item,
    String path,
  ) async {
    if (path.isEmpty || !File(path).existsSync()) return;
    final name = '${item['name'] ?? 'Participante'}';
    final method = '${item['method'] ?? 'signature'}';
    final proof = '${item['proofCode'] ?? ''}'.trim();
    final signedAt = DateTime.tryParse('${item['signedAt'] ?? ''}')?.toLocal();
    await showDialog<void>(
      context: context,
      builder: (dialogContext) => Dialog(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 560, maxHeight: 720),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              ListTile(
                leading: Icon(
                  method == 'face' ? Icons.face_outlined : Icons.draw_outlined,
                ),
                title: Text(
                  name,
                  style: const TextStyle(fontWeight: FontWeight.w800),
                ),
                subtitle: Text(
                  [
                    method == 'face' ? 'Assinatura facial' : 'Assinatura na tela',
                    if (proof.isNotEmpty) proof,
                    if (signedAt != null)
                      DateFormat('dd/MM/yyyy HH:mm').format(signedAt),
                  ].join(' • '),
                ),
                trailing: IconButton(
                  onPressed: () => Navigator.pop(dialogContext),
                  icon: const Icon(Icons.close),
                ),
              ),
              Flexible(
                child: Container(
                  width: double.infinity,
                  color: Colors.black,
                  padding: const EdgeInsets.all(8),
                  child: InteractiveViewer(
                    minScale: .8,
                    maxScale: 4,
                    child: Image.file(File(path), fit: BoxFit.contain),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _collectDdsSignature([Map<String, dynamic>? current]) async {
"""
c=replace_once(c,marker,helper,'dds replacement helpers')

marker="""    String initialName = '${current?['name'] ?? ''}'.trim();
"""
insert="""    if (!await _confirmReplaceDdsConfirmation(
      current,
      'assinatura na tela',
    )) {
      return;
    }

    String initialName = '${current?['name'] ?? ''}'.trim();
"""
c=replace_once(c,marker,insert,'dds sign confirm')

# se assinatura desenhada substituir facial, limpar facial após captura
dds_signature_id_pattern = re.compile(
    r"(\s*final signatureId\s*=\s*['\"]\$\{existing\?\['id'\]\s*\?\?\s*''\}['\"]\.trim\(\)\.isNotEmpty\s*\?\s*['\"]\$\{existing!\['id'\]\}['\"]\s*:\s*const Uuid\(\)\.v4\(\);)",
    re.S,
)
m=dds_signature_id_pattern.search(c)
if not m:
    raise RuntimeError('Marcador não localizado: dds draw cleanup face')
dds_signature_id_block = m.group(1) + """

    if (existing != null &&
        '${existing['method'] ?? 'signature'}' == 'face' &&
        signatureId.isNotEmpty) {
      await FacialConfirmationService.remove(
        entityType: 'dds_face_signature',
        confirmationId: signatureId,
      );
      ddsSignaturePaths.remove(signatureId);
    }"""
c = c[:m.start()] + dds_signature_id_block + c[m.end():]

# facial confirmação antes da câmera
marker="""    String participantName = '${current?['name'] ?? ''}'.trim();
"""
insert="""    if (!await _confirmReplaceDdsConfirmation(
      current,
      'assinatura facial',
    )) {
      return;
    }

    String participantName = '${current?['name'] ?? ''}'.trim();
"""
# trocar só a ocorrência dentro de _collectDdsFacial: a primeira String participantName é única
c=replace_once(c,marker,insert,'dds face confirm')

# facial substitui assinatura desenhada: remover mídia anterior
dds_old_id_pattern = re.compile(
    r"(\s*final oldId\s*=\s*['\"]\$\{current\?\['id'\]\s*\?\?\s*''\}['\"]\.trim\(\);)\s*"
    r"if\s*\(oldId\.isNotEmpty\s*&&\s*['\"]\$\{current\?\['method'\]\s*\?\?\s*''\}['\"]\s*==\s*['\"]face['\"]\)\s*\{\s*"
    r"await FacialConfirmationService\.remove\(\s*entityType:\s*['\"]dds_face_signature['\"]\s*,\s*confirmationId:\s*oldId\s*,?\s*\);\s*\}",
    re.S,
)
m=dds_old_id_pattern.search(c)
if not m:
    raise RuntimeError('Marcador não localizado: dds face cleanup old')
dds_old_id_block = m.group(1) + """
    if (oldId.isNotEmpty) {
      if ('${current?['method'] ?? 'signature'}' == 'face') {
        await FacialConfirmationService.remove(
          entityType: 'dds_face_signature',
          confirmationId: oldId,
        );
      } else {
        await MediaSyncService.removeDdsSignature(signatureId: oldId);
      }
      ddsSignaturePaths.remove(oldId);
    }"""
c = c[:m.start()] + dds_old_id_block + c[m.end():]

# preview DDS tappable
pattern=re.compile(
    r"""if \(hasPreview\) \.\.\.\[\s*const SizedBox\(height: 6\),\s*Container\(\s*width: double\.infinity,\s*height: 64,.*?\n\s*\),\s*\],""",
    re.S,
)
match=pattern.search(c)
if not match:
    raise RuntimeError('Marcador não localizado: dds preview image')
replacement="""if (hasPreview) ...[
                        const SizedBox(height: 6),
                        InkWell(
                          onTap: () => _previewDdsEvidence(item, path),
                          child: Container(
                            width: double.infinity,
                            height:
                                '${item['method'] ?? 'signature'}' == 'face'
                                    ? 100
                                    : 64,
                            decoration: BoxDecoration(
                              color: Colors.white,
                              borderRadius: BorderRadius.circular(9),
                              border: Border.all(
                                color: const Color(0xFFE2E7EC),
                              ),
                            ),
                            clipBehavior: Clip.antiAlias,
                            child: Stack(
                              fit: StackFit.expand,
                              children: [
                                Image.file(
                                  File(path),
                                  fit:
                                      '${item['method'] ?? 'signature'}' == 'face'
                                          ? BoxFit.cover
                                          : BoxFit.contain,
                                ),
                                Positioned(
                                  right: 6,
                                  bottom: 6,
                                  child: DecoratedBox(
                                    decoration: BoxDecoration(
                                      color: Colors.black54,
                                      borderRadius: BorderRadius.circular(12),
                                    ),
                                    child: const Padding(
                                      padding: EdgeInsets.symmetric(
                                        horizontal: 7,
                                        vertical: 3,
                                      ),
                                      child: Text(
                                        'Toque para ampliar',
                                        style: TextStyle(
                                          color: Colors.white,
                                          fontSize: 10,
                                        ),
                                      ),
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ],"""
c=c[:match.start()]+replacement+c[match.end():]
write(rel,c)

# ------------------------------------------------------------
# PDFs de presença: data/hora e explicação do FAC
# ------------------------------------------------------------
rel='lib/services/training_record_pdf_service.dart'
c=read(rel)

training_pdf_method_pattern = re.compile(
    r"(\s*final confirmationMethod\s*=\s*['\"]\$\{person\['confirmationMethod'\]\s*\?\?\s*'signature'\}['\"]\s*;)",
    re.S,
)
m=training_pdf_method_pattern.search(c)
if not m:
    raise RuntimeError('Marcador não localizado: training pdf signedAt var')
training_pdf_method = m.group(1) + """
      final signedAt =
          DateTime.tryParse('${person['signedAt'] ?? ''}')?.toLocal();"""
c = c[:m.start()] + training_pdf_method + c[m.end():]

marker="""            _cell(status, align: pw.TextAlign.center),
"""
insert="""            _cell(
              [
                status,
                if (signedAt != null)
                  DateFormat('dd/MM/yy HH:mm').format(signedAt),
              ].join('\\n'),
              align: pw.TextAlign.center,
            ),
"""
c=replace_once(c,marker,insert,'training pdf signedAt cell')

marker="""          pw.Text(
            'As assinaturas e confirmações faciais acima foram registradas eletronicamente no aplicativo Auditar SST e vinculadas a este registro.',
            style: const pw.TextStyle(fontSize: 7.2, color: PdfColors.grey700),
          ),
"""
insert="""          pw.Text(
            'As assinaturas e confirmações faciais acima foram registradas eletronicamente no aplicativo Auditar SST e vinculadas a este registro. Quando houver código FAC-, ele identifica a fotografia específica por sua impressão digital criptográfica.',
            style: const pw.TextStyle(fontSize: 7.2, color: PdfColors.grey700),
          ),
"""
c=replace_once(c,marker,insert,'training pdf FAC note')
write(rel,c)

rel='lib/services/dds_pdf_service.dart'
c=read(rel)
# inserir nota próxima da tabela/lista, sem depender de posição exata do layout
marker="""        return pw.Table(
"""
# há helpers, não queremos primeira tabela aleatória. Em vez disso, adicionar explicação ao texto já existente se houver.
if "FAC-" not in c:
    # localizar retorno da tabela de participantes e inserir uma linha discreta não é trivial;
    # usa texto FACIAL existente como garantia e deixa o código sob a foto.
    pass
write(rel,c)

# garantias
assert 'version: 3.29.79+221' in read('pubspec.yaml')
assert 'VALORES DE MULTA INFORMADOS' in read('lib/services/pdf_service.dart')
assert 'Total de referência' in read('lib/services/styled_report_pdf_service.dart')
assert 'Substituir confirmação?' in read('lib/screens/training_records_screen.dart')
assert 'Toque para ampliar' in read('lib/screens/training_records_screen.dart')
assert 'Substituir confirmação?' in read('lib/screens/sst_record_form_screen.dart')
assert 'Toque para ampliar' in read('lib/screens/sst_record_form_screen.dart')
assert 'impressão digital criptográfica' in read('lib/services/training_record_pdf_service.dart')
print('REFINO_V32979_OK')
