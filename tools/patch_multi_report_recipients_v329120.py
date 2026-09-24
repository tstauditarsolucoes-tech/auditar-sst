#!/usr/bin/env python3
"""Per-company multiple report recipients; no DB migration, no GS/sync/AI changes.

Each manually requested report is delivered individually to each authorized
recipient using the proven single-recipient Central route. Each request gets a
unique request ID and its own success/failure row in the existing history.
Automatic weekly/monthly recipients retain the existing Gmail CC list field.
"""
from pathlib import Path
import sys

root=Path(sys.argv[1]); platform=sys.argv[2]
assert platform in ('android','windows')
source=Path(__file__).resolve().parents[1]/'feature_sources/report_recipients_v329120.dart'
assert source.exists()
(root/'lib/services/report_recipients.dart').write_bytes(source.read_bytes())
test=Path(__file__).resolve().parents[1]/'feature_sources/report_recipients_test_v329120.dart'
assert test.exists()
(root/'test/report_recipients_test.dart').write_bytes(test.read_bytes())

def one(rel,old,new,label):
 p=root/rel
 s=p.read_text(encoding='utf-8')
 count=s.count(old)
 if count!=1:raise RuntimeError('%s: expected 1, found %d'%(label,count))
 p.write_text(s.replace(old,new,1),encoding='utf-8',newline='\n')

# Add a multiline group on the existing company record. The additional list
# stays in secondary_report_email TEXT so existing clients sync it automatically.
companies='lib/screens/companies_screen.dart'
one(companies,
"import '../models.dart';",
"import '../models.dart';\nimport '../services/report_recipients.dart';",
'company recipient import')
one(companies,
"""                          controller: secondaryReportEmail,
                          keyboardType: TextInputType.emailAddress,
                          decoration: const InputDecoration(
                            labelText: 'E-mail adicional (opcional)',
                            prefixIcon: Icon(Icons.alternate_email),
                          ),""",
"""                          controller: secondaryReportEmail,
                          keyboardType: TextInputType.multiline,
                          minLines: 2,
                          maxLines: 4,
                          onChanged: (_) => setDialogState(() {}),
                          decoration: const InputDecoration(
                            labelText: 'Outros destinatários (até 9)',
                            hintText: 'Um e-mail por linha, ou separados por vírgula',
                            helperText: 'Todos recebem o PDF. É possível adicionar e remover endereços.',
                            helperMaxLines: 2,
                            prefixIcon: Icon(Icons.alternate_email),
                          ),""",
'multiline recipients')
one(companies,
"""                        SwitchListTile(
                          contentPadding: EdgeInsets.zero,
                          title: const Text('Enviar relatório mensal'),""",
"""                        const SizedBox(height: 4),
                        Align(
                          alignment: Alignment.centerLeft,
                          child: Text(
                            '${ReportRecipients.parse(reportEmail.text, secondaryReportEmail.text).length}/10 destinatários cadastrados',
                            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
                          ),
                        ),
                        SwitchListTile(
                          contentPadding: EdgeInsets.zero,
                          title: const Text('Enviar relatório mensal'),""",
'recipient count')
one(companies,
"""    final secondaryEmail = secondaryReportEmail.text.trim();
    bool validEmail(String value) =>
        value.isEmpty || RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$').hasMatch(value);
    if (!validEmail(primaryEmail) || !validEmail(secondaryEmail)) {""",
"""    final secondaryEmail =
        ReportRecipients.normalizedAdditional(primaryEmail, secondaryReportEmail.text);
    final emailError =
        ReportRecipients.validationError(primaryEmail, secondaryReportEmail.text);
    if (emailError != null) {""",
'recipient validation')
one(companies,
"content: Text('Confira o endereço de e-mail informado.'),",
"content: Text(emailError),",
'precise recipient validation')
# Multi-address record must always have a primary.
one(companies,
"""    if ((monthlyReportEnabled ||
            weeklyReportEnabled ||
            trainingAlertsEnabled) &&
        primaryEmail.isEmpty) {""",
"""    if (((monthlyReportEnabled ||
            weeklyReportEnabled ||
            trainingAlertsEnabled) ||
            secondaryEmail.isNotEmpty) &&
        primaryEmail.isEmpty) {""",
'primary required if extras exist')

# Existing report/sending screens get the precise destination list.
one('lib/screens/report_screen.dart',
"import '../services/document_delivery_service.dart';",
"import '../services/document_delivery_service.dart';\nimport '../services/report_recipients.dart';",
'report recipient import')
one('lib/screens/report_screen.dart',
"if (cc.isNotEmpty) Text('Cópia: $cc'),",
"if (cc.isNotEmpty) Text('Outros destinatários: ${ReportRecipients.additional(to, cc).join(', ')}'),",
'report send confirmation')
one('lib/widgets/document_dispatch_dialog.dart',
"import '../services/document_delivery_service.dart';",
"import '../services/document_delivery_service.dart';\nimport '../services/report_recipients.dart';",
'dialog recipient import')
one('lib/widgets/document_dispatch_dialog.dart',
"Text('Cópia: ${company.secondaryReportEmail}'),",
"Text('Outros destinatários: ${ReportRecipients.additional(company.reportEmail,company.secondaryReportEmail).join(', ')}'),",
'dialog recipient confirmation')
one('lib/screens/document_dispatch_center_screen.dart',
"import '../services/document_delivery_service.dart';",
"import '../services/document_delivery_service.dart';\nimport '../services/report_recipients.dart';",
'center recipient import')
one('lib/screens/document_dispatch_center_screen.dart',
"""'${c.secondaryReportEmail.trim().isEmpty ? '' : 'Cópia: ${c.secondaryReportEmail}\\n'}'""",
"""'${c.secondaryReportEmail.trim().isEmpty ? '' : 'Outros destinatários: ${ReportRecipients.additional(c.reportEmail,c.secondaryReportEmail).join(', ')}\\n'}'""",
'center recipient confirmation')

# Same PDF, individual email and log for EACH recipient. The deployed
# ReportEmail.gs currently validates a single address in its cc field; this
# avoids touching or redeploying it and avoids leaking addresses to each other.
delivery='lib/services/document_delivery_service.dart'
p=root/delivery
s=p.read_text(encoding='utf-8')
needle="import 'report_email_service.dart';"
assert s.count(needle)==1
s=s.replace(needle,needle+"\nimport 'report_recipients.dart';",1)
start=s.index('  static Future<String> send({')
end=s.index('  static Future<List<Map<String, dynamic>>> history(',start)
new='''  static Future<String> send({
    required String companyId,
    required String companyName,
    required String documentId,
    required String category,
    required String title,
    required String to,
    required String cc,
    required String fileName,
    required Uint8List bytes,
  }) async {
    if (to.trim().isEmpty) {
      throw StateError('Cadastre o e-mail principal na ficha da empresa.');
    }
    final validation = ReportRecipients.validationError(to, cc);
    if (validation != null) throw StateError(validation);
    final recipients = ReportRecipients.parse(to, cc);
    if (recipients.isEmpty) {
      throw StateError('Nenhum destinatário cadastrado.');
    }

    final failed = <String>[];
    var sent = 0;
    for (final recipient in recipients) {
      final requestId = const Uuid().v4();
      final record = <String, dynamic>{
        'requestId': requestId,
        'companyId': companyId,
        'documentId': documentId,
        'category': category,
        'title': title,
        'to': recipient,
        'cc': '',
        'fileName': fileName,
        'createdAt': DateTime.now().toIso8601String(),
        'status': 'SENDING',
        'error': '',
      };
      try { await _remember(companyId, record); } catch (_) {}
      try {
        await ReportEmailService.send(
          companyId: companyId,
          companyName: companyName,
          inspectionId: documentId,
          requestId: requestId,
          to: recipient,
          cc: '',
          fileName: fileName,
          bytes: bytes,
        );
        record['status'] = 'SENT';
        record['sentAt'] = DateTime.now().toIso8601String();
        sent++;
      } catch (error) {
        record['status'] = 'FAILED';
        record['error'] = '$error';
        failed.add(recipient);
      }
      try { await _remember(companyId, record); } catch (_) {}
    }
    if (sent == 0) {
      throw StateError(
        'Nenhum envio confirmado pela Central. Confira o histórico de envios por destinatário.'
      );
    }
    if (failed.isNotEmpty) {
      return '$sent de ${recipients.length} envio(s) confirmados. '
        'Não confirmados: ${failed.join(', ')}. Confira o histórico antes de reenviar.';
    }
    return '$sent de ${recipients.length} envio(s) confirmados pela Central. '
      'Cada endereço recebeu um e-mail individual com o PDF.';
  }

'''
s=s[:start]+new+s[end:]
p.write_text(s,encoding='utf-8',newline='\n')

# Label the existing automated email preview without changing the backend
# which already forwards the additional comma-separated list as Gmail CC.
one('lib/screens/management_panel_screen.dart',
"' e cópia para ${widget.company.secondaryReportEmail}'",
"' e para ${widget.company.secondaryReportEmail}'",
'automatic email target label')

version=root/'pubspec.yaml';s=version.read_text(encoding='utf-8')
old,new=('3.29.119+261','3.29.120+262') if platform=='android' else ('3.30.43+230','3.30.44+231')
assert s.count('version: '+old)==1,[x for x in s.splitlines() if x.startswith('version:')]
version.write_text(s.replace('version: '+old,'version: '+new,1),encoding='utf-8',newline='\n')
assert 'ReportRecipients.parse(to, cc)' in p.read_text(encoding='utf-8')
print('MULTI_REPORT_RECIPIENTS_OK',platform,new)
