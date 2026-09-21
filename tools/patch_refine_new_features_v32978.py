#!/usr/bin/env python3
from pathlib import Path
import re, shutil, sys

root=Path(sys.argv[1])
repo_root=Path(__file__).resolve().parents[1] if '/tools/' in str(Path(__file__)) else Path.cwd()

def read(rel):
    return (root/rel).read_text(encoding='utf-8')

def write(rel, text):
    (root/rel).write_text(text,encoding='utf-8',newline='\n')

def replace_once(text, old, new, label):
    if old not in text:
        raise RuntimeError(f'Marcador não localizado: {label}')
    return text.replace(old,new,1)

# Versão
pub=read('pubspec.yaml')
pub,n=re.subn(r'^version:\s*[^\n]+','version: 3.29.78+220',pub,count=1,flags=re.M)
if n!=1: raise RuntimeError('Versão não localizada')
write('pubspec.yaml',pub)

# Tela facial refinada
src=Path.cwd()/'build_sources/v3.29.78-refine-new-features/facial_confirmation_screen.dart'
if not src.exists():
    src=repo_root/'build_sources/v3.29.78-refine-new-features/facial_confirmation_screen.dart'
if not src.exists():
    raise RuntimeError('Fonte facial refinada não localizada')
shutil.copyfile(src, root/'lib/screens/facial_confirmation_screen.dart')

# Checklist: multa mais profissional e estruturada
rel='lib/screens/checklist_screen.dart'
c=read(rel)
if "import 'package:flutter/services.dart';" not in c:
    c=replace_once(c,"import 'package:flutter/material.dart';\n","import 'package:flutter/material.dart';\nimport 'package:flutter/services.dart';\n",'import services')

c=replace_once(
    c,
    "  final Map<String, TextEditingController> fineAmounts = {};\n  final Map<String, bool> fineShowInReport = {};",
    "  final Map<String, TextEditingController> fineAmounts = {};\n  final Map<String, TextEditingController> fineBases = {};\n  final Map<String, bool> fineShowInReport = {};",
    'mapa multa base',
)
c=replace_once(
    c,
    "      fineAmounts[item.id] = TextEditingController();\n      fineShowInReport[item.id] = false;",
    "      fineAmounts[item.id] = TextEditingController();\n      fineBases[item.id] = TextEditingController();\n      fineShowInReport[item.id] = false;",
    'init multa base',
)
c=replace_once(
    c,
    "      fineAmounts[item.id]!.addListener(_scheduleDraftSave);",
    "      fineAmounts[item.id]!.addListener(_scheduleDraftSave);\n      fineBases[item.id]!.addListener(_scheduleDraftSave);",
    'listener multa base',
)
load_pattern = re.compile(
    r"fineAmounts\[answer\.questionId\]!\.text\s*=\s*'\$\{fine\['amount'\]\s*\?\?\s*''\}';\s*"
    r"fineShowInReport\[answer\.questionId\]\s*=\s*fine\['showInReport'\]\s*==\s*true;",
    re.S,
)
load_replacement = """final cents = fine['amountCents'];
              if (cents is num && cents > 0) {
                fineAmounts[answer.questionId]!.text =
                    _formatFineCents(cents.round());
              } else {
                fineAmounts[answer.questionId]!.text =
                    '${fine['amount'] ?? ''}';
              }
              fineBases[answer.questionId]!.text =
                  '${fine['basis'] ?? ''}';
              fineShowInReport[answer.questionId] =
                  fine['showInReport'] == true;"""
c,n=load_pattern.subn(load_replacement,c,count=1)
if n!=1:
    raise RuntimeError('Marcador não localizado: load multa')
old_payload="""  String _occurrencesPayload(String itemId) {
    return jsonEncode({
      'version': 2,
      'fine': {
        'amount': fineAmounts[itemId]?.text.trim() ?? '',
        'showInReport': fineShowInReport[itemId] ?? false,
      },
"""
new_payload="""  int? _fineAmountCents(String itemId) {
    var raw = fineAmounts[itemId]?.text.trim() ?? '';
    raw = raw.replaceAll(RegExp(r'[^0-9,.]'), '');
    if (raw.isEmpty) return null;
    if (raw.contains(',')) {
      raw = raw.replaceAll('.', '').replaceAll(',', '.');
    } else {
      final parts = raw.split('.');
      if (parts.length > 2) {
        final last = parts.removeLast();
        raw = '${parts.join()}.$last';
      } else if (parts.length == 2 && parts.last.length == 3) {
        raw = parts.join();
      }
    }
    final value = double.tryParse(raw);
    if (value == null || value <= 0) return null;
    return (value * 100).round();
  }

  String _formatFineCents(int cents) {
    return NumberFormat.currency(
      locale: 'pt_BR',
      symbol: '',
      decimalDigits: 2,
    ).format(cents / 100).trim();
  }

  String _occurrencesPayload(String itemId) {
    final fineCents = _fineAmountCents(itemId);
    return jsonEncode({
      'version': 3,
      'fine': {
        'amountCents': fineCents,
        'amount': fineCents == null ? '' : (fineCents / 100).toStringAsFixed(2),
        'basis': fineBases[itemId]?.text.trim() ?? '',
        'referenceOnly': true,
        'showInReport': fineCents != null && (fineShowInReport[itemId] ?? false),
      },
"""
c=replace_once(c,old_payload,new_payload,'payload multa')

c=replace_once(
    c,
    "    for (final controller in fineAmounts.values) {\n      controller.dispose();\n    }",
    "    for (final controller in fineAmounts.values) {\n      controller.dispose();\n    }\n    for (final controller in fineBases.values) {\n      controller.dispose();\n    }",
    'dispose multa base',
)
c=replace_once(
    c,
    "          (fineAmounts[item.id]?.text.trim().isNotEmpty ?? false) ||\n          evidence.isNotEmpty;",
    "          (fineAmounts[item.id]?.text.trim().isNotEmpty ?? false) ||\n          (fineBases[item.id]?.text.trim().isNotEmpty ?? false) ||\n          evidence.isNotEmpty;",
    'draft multa base',
)

old_ui="""                                    const SizedBox(height: 10),
                                    TextField(
                                      controller: fineAmounts[item.id],
                                      keyboardType:
                                          const TextInputType.numberWithOptions(
                                            decimal: true,
                                          ),
                                      decoration: const InputDecoration(
                                        labelText:
                                            'Valor da multa por descumprimento (opcional)',
                                        prefixText: 'R\\$ ',
                                        helperText:
                                            'Informe o valor apenas quando quiser registrar a referência da multa.',
                                      ),
                                    ),
                                    SwitchListTile(
                                      contentPadding: EdgeInsets.zero,
                                      value: fineShowInReport[item.id] ?? false,
                                      title: const Text(
                                        'Mostrar valor da multa no relatório',
                                      ),
                                      subtitle: const Text(
                                        'Se desmarcado, o valor fica salvo no checklist e não aparece no PDF.',
                                      ),
                                      onChanged: (value) {
                                        setState(
                                          () =>
                                              fineShowInReport[item.id] = value,
                                        );
                                        _scheduleDraftSave();
                                      },
                                    ),
                                    if (isNc) ...[
"""
new_ui="""                                    if (isNc) ...[
                                      const SizedBox(height: 12),
                                      Container(
                                        width: double.infinity,
                                        padding: const EdgeInsets.all(12),
                                        decoration: BoxDecoration(
                                          color: const Color(0xFFFFFBF1),
                                          borderRadius: BorderRadius.circular(12),
                                          border: Border.all(
                                            color: const Color(0xFFF0DFC0),
                                          ),
                                        ),
                                        child: Column(
                                          crossAxisAlignment:
                                              CrossAxisAlignment.start,
                                          children: [
                                            const Row(
                                              children: [
                                                Icon(
                                                  Icons.gavel_outlined,
                                                  size: 20,
                                                  color: Color(0xFF8A6418),
                                                ),
                                                SizedBox(width: 7),
                                                Expanded(
                                                  child: Text(
                                                    'Multa por descumprimento • opcional',
                                                    style: TextStyle(
                                                      fontWeight:
                                                          FontWeight.w800,
                                                    ),
                                                  ),
                                                ),
                                              ],
                                            ),
                                            const SizedBox(height: 9),
                                            TextField(
                                              controller: fineAmounts[item.id],
                                              keyboardType:
                                                  const TextInputType
                                                      .numberWithOptions(
                                                decimal: true,
                                              ),
                                              inputFormatters: [
                                                FilteringTextInputFormatter.allow(
                                                  RegExp(r'[0-9.,]'),
                                                ),
                                              ],
                                              decoration:
                                                  const InputDecoration(
                                                labelText:
                                                    'Valor de referência',
                                                prefixText: 'R\\$ ',
                                                hintText: 'Ex.: 1.500,00',
                                              ),
                                              onChanged: (_) {
                                                if (_fineAmountCents(item.id) ==
                                                        null &&
                                                    (fineShowInReport[item.id] ??
                                                        false)) {
                                                  setState(
                                                    () => fineShowInReport[
                                                        item.id] = false,
                                                  );
                                                }
                                              },
                                              onEditingComplete: () {
                                                final cents =
                                                    _fineAmountCents(item.id);
                                                if (cents != null) {
                                                  fineAmounts[item.id]!.text =
                                                      _formatFineCents(cents);
                                                }
                                                FocusScope.of(context).unfocus();
                                              },
                                            ),
                                            const SizedBox(height: 9),
                                            TextField(
                                              controller: fineBases[item.id],
                                              maxLines: 2,
                                              decoration:
                                                  const InputDecoration(
                                                labelText:
                                                    'Base / observação do valor',
                                                hintText:
                                                    'Ex.: NR-28, auto de infração ou valor informado pelo cliente',
                                              ),
                                            ),
                                            SwitchListTile(
                                              contentPadding: EdgeInsets.zero,
                                              value:
                                                  fineShowInReport[item.id] ??
                                                      false,
                                              title: const Text(
                                                'Mostrar no relatório',
                                              ),
                                              subtitle: const Text(
                                                'O relatório identificará o valor como referência informada no checklist, e não como cálculo automático da fiscalização.',
                                              ),
                                              onChanged: (value) {
                                                if (value &&
                                                    _fineAmountCents(item.id) ==
                                                        null) {
                                                  ScaffoldMessenger.of(context)
                                                      .showSnackBar(
                                                    const SnackBar(
                                                      content: Text(
                                                        'Informe um valor válido antes de exibir a multa no relatório.',
                                                      ),
                                                    ),
                                                  );
                                                  return;
                                                }
                                                setState(
                                                  () => fineShowInReport[
                                                      item.id] = value,
                                                );
                                                _scheduleDraftSave();
                                              },
                                            ),
                                          ],
                                        ),
                                      ),
                                      const SizedBox(height: 12),
"""
ui_pattern = re.compile(
    r"\s*const SizedBox\(height:\s*10\),\s*"
    r"TextField\(\s*controller:\s*fineAmounts\[item\.id\],.*?"
    r"SwitchListTile\(.*?fineShowInReport\[item\.id\].*?"
    r"_scheduleDraftSave\(\);\s*\},\s*\),\s*"
    r"if\s*\(isNc\)\s*\.\.\.\[",
    re.S,
)
c,n=ui_pattern.subn("\n"+new_ui.rstrip(),c,count=1)
if n!=1:
    raise RuntimeError('Marcador não localizado: ui multa refinada')
write(rel,c)

# Relatórios: moeda padronizada e base
for rel in ['lib/services/pdf_service.dart','lib/services/styled_report_pdf_service.dart']:
    c=read(rel)
    c=c.replace("'Multa por descumprimento', _fineForReport(answer)","'Multa (valor de referência)', _fineForReport(answer)")
    c=c.replace("'Multa por descumprimento', _fineForReport(a)","'Multa (valor de referência)', _fineForReport(a)")
    old=re.search(r"  static String _fineForReport\([^\)]*\) \{.*?\n  \}",c,re.S)
    if not old:
        raise RuntimeError(f'Helper multa não localizado em {rel}')
    param='answer' if 'InspectionAnswer answer' in old.group(0) else 'a'
    helper=f"""  static String _fineForReport(InspectionAnswer {param}) {{
    final raw = {param}.occurrencesJson.trim();
    if (raw.isEmpty) return '';
    try {{
      final decoded = jsonDecode(raw);
      if (decoded is! Map) return '';
      final fine = decoded['fine'];
      if (fine is! Map || fine['showInReport'] != true) return '';

      int? cents;
      final rawCents = fine['amountCents'];
      if (rawCents is num && rawCents > 0) {{
        cents = rawCents.round();
      }} else {{
        var legacy = '${{fine['amount'] ?? ''}}'.trim();
        legacy = legacy.replaceAll('R\\$', '').replaceAll(' ', '');
        if (legacy.contains(',')) {{
          legacy = legacy.replaceAll('.', '').replaceAll(',', '.');
        }}
        final value = double.tryParse(legacy);
        if (value != null && value > 0) cents = (value * 100).round();
      }}
      if (cents == null) return '';

      final amount = NumberFormat.currency(
        locale: 'pt_BR',
        symbol: 'R\\$',
        decimalDigits: 2,
      ).format(cents / 100);
      final basis = '${{fine['basis'] ?? ''}}'.trim();
      final parts = <String>[
        amount,
        if (basis.isNotEmpty) 'Base/observação: $basis',
        'valor informado no checklist; sem cálculo automático pelo Auditar',
      ];
      return parts.join(' • ');
    }} catch (_) {{
      return '';
    }}
  }}"""
    c=c[:old.start()]+helper+c[old.end():]
    write(rel,c)

# DDS: preservar metadados de prova facial no payload e na tela
rel='lib/screens/sst_record_form_screen.dart'
c=read(rel)
c=replace_once(
    c,
    "              'method': '${item['method'] ?? 'signature'}',",
    "              'method': '${item['method'] ?? 'signature'}',\n              if ('${item['proofCode'] ?? ''}'.trim().isNotEmpty)\n                'proofCode': '${item['proofCode']}',\n              if ('${item['photoSha256'] ?? ''}'.trim().isNotEmpty)\n                'photoSha256': '${item['photoSha256']}',\n              if ('${item['consentVersion'] ?? ''}'.trim().isNotEmpty)\n                'consentVersion': '${item['consentVersion']}',",
    'load dds proof',
)
c=replace_once(
    c,
    "      'method': 'face',\n      if (matchedWorker != null) 'workerId': matchedWorker.id,",
    "      'method': 'face',\n      'proofCode': result.proofCode,\n      'photoSha256': result.photoSha256,\n      'consentVersion': 'facial-photo-v2',\n      if (matchedWorker != null) 'workerId': matchedWorker.id,",
    'save dds proof',
)
c=replace_once(
    c,
    "    final label = method == 'face' ? 'Facial' : 'Assinado';",
    "    final label = method == 'face' ? 'Facial' : 'Assinado';\n    final proof = '${item['proofCode'] ?? ''}'.trim();",
    'dds signed proof var',
)
c=replace_once(
    c,
    "    return '$label em ${DateFormat('dd/MM/yyyy HH:mm').format(parsed)}';",
    "    final when = DateFormat('dd/MM/yyyy HH:mm').format(parsed);\n    return proof.isEmpty ? '$label em $when' : '$label em $when • $proof';",
    'dds signed proof label',
)
write(rel,c)

# Treinamento: metadados de prova facial
rel='lib/screens/training_records_screen.dart'
c=read(rel)
training_pattern = re.compile(
    r"(['\"]confirmationMethod['\"]\s*:\s*['\"]face['\"]\s*,)",
    re.S,
)
training_replacement = r"""\1
            'faceProofCode': result.proofCode,
            'facePhotoSha256': result.photoSha256,
            'faceConsentVersion': 'facial-photo-v2',"""
c,n=training_pattern.subn(training_replacement,c,count=1)
if n!=1:
    raise RuntimeError('Marcador não localizado: training proof payload')
write(rel,c)

# PDF DDS: copiar proofCode para a linha e exibir abaixo da foto
rel='lib/services/dds_pdf_service.dart'
c=read(rel)
c=replace_once(
    c,
    "      row['method'] = '${signature['method'] ?? 'signature'}';",
    "      row['method'] = '${signature['method'] ?? 'signature'}';\n      row['proofCode'] = '${signature['proofCode'] ?? ''}';\n      row['photoSha256'] = '${signature['photoSha256'] ?? ''}';",
    'dds pdf proof copy',
)
c=replace_once(
    c,
    "                              pw.Text(\n                                'FACIAL',\n                                style: pw.TextStyle(\n                                  fontSize: 5.5,\n                                  fontWeight: pw.FontWeight.bold,\n                                ),\n                              ),",
    "                              pw.Text(\n                                'FACIAL',\n                                style: pw.TextStyle(\n                                  fontSize: 5.5,\n                                  fontWeight: pw.FontWeight.bold,\n                                ),\n                              ),\n                              if ('${row['proofCode'] ?? ''}'.trim().isNotEmpty)\n                                pw.Text(\n                                  '${row['proofCode']}',\n                                  style: const pw.TextStyle(\n                                    fontSize: 4.8,\n                                    color: PdfColors.grey700,\n                                  ),\n                                ),",
    'dds pdf proof label',
)
write(rel,c)

# PDF Treinamento: exibir código de prova sob a foto
rel='lib/services/training_record_pdf_service.dart'
c=read(rel)
c=replace_once(
    c,
    "                          pw.Text(\n                            'FACIAL',\n                            style: pw.TextStyle(\n                              fontSize: 5.7,\n                              fontWeight: pw.FontWeight.bold,\n                            ),\n                          ),",
    "                          pw.Text(\n                            'FACIAL',\n                            style: pw.TextStyle(\n                              fontSize: 5.7,\n                              fontWeight: pw.FontWeight.bold,\n                            ),\n                          ),\n                          if ('${person['faceProofCode'] ?? ''}'.trim().isNotEmpty)\n                            pw.Text(\n                              '${person['faceProofCode']}',\n                              style: const pw.TextStyle(\n                                fontSize: 4.8,\n                                color: PdfColors.grey700,\n                              ),\n                            ),",
    'training pdf proof label',
)
write(rel,c)

# Garantias
assert 'version: 3.29.78+220' in read('pubspec.yaml')
assert 'amountCents' in read('lib/screens/checklist_screen.dart')
assert 'Base / observação do valor' in read('lib/screens/checklist_screen.dart')
assert 'valor informado no checklist; sem cálculo automático pelo Auditar' in read('lib/services/pdf_service.dart')
assert 'proofCode' in read('lib/screens/sst_record_form_screen.dart')
assert 'faceProofCode' in read('lib/screens/training_records_screen.dart')
assert 'FAC-' in read('lib/screens/facial_confirmation_screen.dart')
print('REFINO_V32978_OK')
