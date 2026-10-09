#!/usr/bin/env python3
"""Client-facing report cleanup + Performance default + direct registered-email delivery."""
from pathlib import Path
import re,sys
root=Path(sys.argv[1]); platform=sys.argv[2]
assert platform in ('android','windows')

def read(rel): return (root/rel).read_text(encoding='utf-8')
def write(rel,s): (root/rel).write_text(s,encoding='utf-8',newline='\n')
def one(s,a,b,label):
    n=s.count(a)
    if n!=1: raise RuntimeError(f'{label}: expected 1 got {n}')
    return s.replace(a,b,1)

rel='lib/services/report_template_service.dart'; s=read(rel)
s=one(s,"fallback: currentTemplateId,","fallback: performanceTemplateId,",'default performance fallback')
s=one(s,"orElse: () => currentTemplate,","orElse: () => builtIns.firstWhere((e) => e.id == performanceTemplateId),",'default performance object')
s=s.replace("description: 'Modelo institucional equilibrado para apresentação à gerência, com resumo, evidências, prioridades, conclusão e anexo técnico.',",
            "description: 'Relatório gerencial com resumo, evidências, conclusão e assinaturas.',")
s=s.replace("'Modelo gerencial fotográfico: evidência em destaque, situação encontrada, risco, correção e prioridade.',",
            "'Modelo fotográfico com evidência, situação encontrada e correção recomendada.',")
s=s.replace("'Modelo gerencial em duas colunas: evidência à esquerda e síntese técnica à direita, com prioridade, conclusão e assinatura.',",
            "'Modelo em duas colunas: evidência à esquerda e descrição técnica à direita, com conclusão e assinaturas.',")
write(rel,s)

rel='lib/services/styled_report_pdf_service.dart'; s=read(rel)
s=re.sub(r"\n    final reportFineValues = answers[\s\S]*?\n    if \(template\.showCover\)",
         "\n\n    if (template.showCover)", s, count=1)
s=re.sub(r"\n        if \(reportFineValues\.isNotEmpty\) \.\.\.\[[\s\S]*?\n        \],\n        pw\.SizedBox\(height: 16\),",
         "\n        pw.SizedBox(height: 16),", s, count=1)
s=re.sub(r"\n    final risk = a\.riskIdentified\.trim\(\)\.isNotEmpty[\s\S]*?\n    final recommendation =",
         "\n    final recommendation =", s, count=1)
s=s.replace("          _labelValue('Risco', risk),\n","")
s=s.replace("              pw.SizedBox(width: 6),\n              _priorityChip(priority),\n","")
write(rel,s)

rel='lib/services/performance_report_pdf_service.dart'; s=read(rel)
s=one(s,"""    final techSignature = await _fileImage(
      '${header['technician_signature_path'] ?? ''}',
    );
""","""    final techSignature = await _fileImage(
      '${header['technician_signature_path'] ?? ''}',
    );
    final responsibleSignature = await _fileImage(
      '${header['responsible_signature_path'] ?? ''}',
    );
    final companyCnpj = '${header['company_cnpj'] ?? ''}'.trim();
    final companyAddress = '${header['worksite_address'] ?? ''}'.trim();
""",'performance signatures/company')
s=one(s,"""      _technicalSignature(
        header: header,
        image: techSignature,
        signatureStyle: template.signatureStyle,
      ),
""","""      _signatures(
        header: header,
        techSignature: techSignature,
        responsibleSignature: responsibleSignature,
        signatureStyle: template.signatureStyle,
      ),
""",'performance dual signatures')
s=one(s,"""          dateText: dateText,
          location: location,
        ),""","""          dateText: dateText,
          location: location,
          cnpj: companyCnpj,
          address: companyAddress,
        ),""",'performance header args')
s=one(s,"""    required String dateText,
    required String location,
  }) {""","""    required String dateText,
    required String location,
    required String cnpj,
    required String address,
  }) {""",'performance header signature')
s=one(s,"""          pw.Text(
            'Vistoria realizada em $dateText  |  $location',
            style: pw.TextStyle(
              fontSize: 7.8,
              fontWeight: pw.FontWeight.bold,
            ),
            textAlign: pw.TextAlign.center,
          ),
          pw.SizedBox(height: 7),""","""          pw.Text(
            'Vistoria realizada em $dateText  |  $location',
            style: pw.TextStyle(
              fontSize: 7.8,
              fontWeight: pw.FontWeight.bold,
            ),
            textAlign: pw.TextAlign.center,
          ),
          if (cnpj.isNotEmpty || address.isNotEmpty) ...[
            pw.SizedBox(height: 2),
            pw.Text(
              [
                if (cnpj.isNotEmpty) 'CNPJ: $cnpj',
                if (address.isNotEmpty) 'Endereço: $address',
              ].join('  |  '),
              style: const pw.TextStyle(fontSize: 7.1, color: PdfColors.grey700),
              textAlign: pw.TextAlign.center,
            ),
          ],
          pw.SizedBox(height: 7),""",'performance company identity')
s=s.replace("    final risk = _riskFor(issue);\n","")
s=s.replace("    final fine = _fineForReport(issue.answer);\n","")
s=s.replace("                  _technicalLine('Risco', risk),\n","")
s=re.sub(r"\n                  if \(fine\.isNotEmpty\)\n                    _technicalLine\('Multa \(referência\)', fine, labelColor: _orange\),",
         "", s, count=1)
start=s.index('  static pw.Widget _technicalSignature({')
end=s.index('  static pw.Widget _footer(',start)
new=r'''  static pw.Widget _signatures({
    required Map<String, Object?> header,
    required pw.MemoryImage? techSignature,
    required pw.MemoryImage? responsibleSignature,
    required String signatureStyle,
  }) {
    final techName = _firstNonEmpty([
      header['technician_name'],
      'Responsável técnico',
    ]);
    final registration = _firstNonEmpty([
      header['technician_registration'],
      header['professional_registration'],
      header['technician_registry'],
      '',
    ]);
    final responsibleName = _firstNonEmpty([
      header['responsible_name'],
      'Responsável pela empresa',
    ]);

    pw.Widget block({
      required String label,
      required String name,
      required pw.MemoryImage? image,
    }) {
      return pw.Expanded(
        child: pw.Column(
          children: [
            if (signatureStyle == 'app' && image != null)
              pw.SizedBox(
                height: 42,
                child: pw.Image(image, fit: pw.BoxFit.contain),
              )
            else
              pw.SizedBox(height: 30),
            pw.Container(height: .7, color: PdfColors.grey700),
            pw.SizedBox(height: 4),
            pw.Text(
              label,
              style: pw.TextStyle(fontSize: 8.2, fontWeight: pw.FontWeight.bold),
            ),
            pw.Text(
              name,
              textAlign: pw.TextAlign.center,
              style: const pw.TextStyle(fontSize: 7.3),
            ),
          ],
        ),
      );
    }

    return pw.Row(
      crossAxisAlignment: pw.CrossAxisAlignment.start,
      children: [
        block(
          label: 'RESPONSÁVEL TÉCNICO',
          name: registration.isEmpty ? techName : '$techName - $registration',
          image: techSignature,
        ),
        pw.SizedBox(width: 24),
        block(
          label: 'RESPONSÁVEL PELA EMPRESA',
          name: responsibleName,
          image: responsibleSignature,
        ),
      ],
    );
  }

'''
s=s[:start]+new+s[end:]
write(rel,s)

rel='lib/services/pdf_service.dart'; s=read(rel)
s=re.sub(r"    final reportFineValues = answers[\s\S]*?    final reportFineTotalCents = reportFineValues\.fold<int>\([\s\S]*?\n    \);",
         "    final reportFineValues = <int>[];\n    const reportFineTotalCents = 0;", s, count=1)
s=re.sub(r"\n          if \(answer\.riskIdentified\.isNotEmpty\)\n            _detailLine\([\s\S]*?answer\.riskIdentified,\n            \),", "", s)
s=re.sub(r"\n          if \(_fineForReport\(answer\)\.isNotEmpty\)\n            _detailLine\([\s\S]*?_fineForReport\(answer\),\n            \),", "", s)
s=s.replace("            _detailLine('Classificação', nc.classification),\n","")
s=re.sub(r"\n            if \(answer\.riskIdentified\.isNotEmpty\)\n              _detailLine\('Risco', answer\.riskIdentified\),", "", s)
s=re.sub(r"\n            if \(_fineForReport\(answer\)\.isNotEmpty\)\n              _detailLine\('Multa \(valor de referência\)', _fineForReport\(answer\)\),", "", s)
s=one(s,"""            if (responsibleName.isNotEmpty) ...[
              pw.SizedBox(width: 24),
              pw.Expanded(
                child: _signatureBlock(
                  title: 'Responsável da empresa',
                  name: responsibleName,
                  signature: responsibleSignature,
                ),
              ),
            ],""","""            pw.SizedBox(width: 24),
            pw.Expanded(
              child: _signatureBlock(
                title: 'Responsável da empresa',
                name: responsibleName.isEmpty
                    ? 'Responsável pela empresa'
                    : responsibleName,
                signature: responsibleSignature,
              ),
            ),""",'legacy company signature')
write(rel,s)

email_service=r'''import 'dart:convert';
import 'dart:typed_data';

import '../database.dart';
import '../models.dart';
import 'apps_script_http.dart';
import 'auth_service.dart';

class ReportEmailTarget {
  final Company company;
  final String to;
  final String cc;

  const ReportEmailTarget({
    required this.company,
    required this.to,
    required this.cc,
  });

  String get label => [to, if (cc.isNotEmpty) cc].join(', ');
}

class ReportEmailResult {
  final bool success;
  final String message;
  const ReportEmailResult(this.success, this.message);
}

class ReportEmailService {
  static Future<ReportEmailTarget> targetForInspection(
    String inspectionId,
  ) async {
    final db = AppDatabase.instance;
    final header = await db.getInspectionHeader(inspectionId);
    if (header == null) throw StateError('Vistoria não encontrada.');

    final companyId = '${header['company_id'] ?? ''}'.trim();
    final companies = await db.getCompanies(onlyActive: false);
    Company? company;
    for (final item in companies) {
      if (item.id == companyId) {
        company = item;
        break;
      }
    }
    if (company == null) {
      throw StateError('Empresa da vistoria não encontrada.');
    }

    final to = company.reportEmail.trim();
    final secondary = company.secondaryReportEmail.trim();
    if (to.isEmpty) {
      throw StateError(
        'Cadastre o e-mail principal da empresa antes do envio.',
      );
    }
    return ReportEmailTarget(
      company: company,
      to: to,
      cc: secondary.isNotEmpty &&
              secondary.toLowerCase() != to.toLowerCase()
          ? secondary
          : '',
    );
  }

  static Future<ReportEmailResult> send({
    required String inspectionId,
    required Uint8List pdfBytes,
    required String fileName,
    required ReportEmailTarget target,
  }) async {
    if (pdfBytes.isEmpty) {
      return const ReportEmailResult(false, 'O PDF está vazio.');
    }
    if (pdfBytes.length > 15 * 1024 * 1024) {
      return const ReportEmailResult(
        false,
        'O PDF ultrapassa 15 MB e não pode ser enviado por e-mail.',
      );
    }

    final db = AppDatabase.instance;
    final endpoint = (await db.getSetting(
      'management_panel_endpoint',
      fallback: '',
    )).trim();
    final syncKey = (await db.getSetting(
      'management_panel_sync_key',
      fallback: '',
    )).trim();
    if (endpoint.isEmpty || syncKey.isEmpty) {
      return const ReportEmailResult(
        false,
        'Configure primeiro a Central Online / Painel Gerencial.',
      );
    }

    final header = await db.getInspectionHeader(inspectionId);
    final response = await AppsScriptHttp.postJson(
      Uri.parse(endpoint),
      {
        'action': 'send_report_email',
        'syncKey': syncKey,
        'authToken': AuthService.sessionToken,
        'companyId': target.company.id,
        'companyName': target.company.name,
        'to': target.to,
        'cc': target.cc,
        'recipientName': target.company.reportRecipient,
        'reportNumber': '${header?['report_number'] ?? ''}'.trim(),
        'fileName': fileName,
        'mimeType': 'application/pdf',
        'contentBase64': base64Encode(pdfBytes),
      },
      timeout: const Duration(seconds: 60),
      allowLongAndroidRequest: true,
    );

    dynamic decoded;
    try {
      decoded = jsonDecode(response.body);
    } catch (_) {}

    if (response.statusCode < 200 ||
        response.statusCode >= 300 ||
        decoded is! Map ||
        decoded['ok'] != true) {
      return ReportEmailResult(
        false,
        decoded is Map
            ? '${decoded['message'] ?? 'Não foi possível enviar o relatório.'}'
            : 'Resposta inválida da Central.',
      );
    }
    return ReportEmailResult(
      true,
      '${decoded['message'] ?? 'Relatório enviado por e-mail.'}',
    );
  }
}
'''
write('lib/services/report_email_service.dart',email_service)

rel='lib/screens/report_screen.dart'; s=read(rel)
s=one(s,"import '../services/report_file_service.dart';",
      "import '../services/report_file_service.dart';\nimport '../services/report_email_service.dart';",'email import')
s=one(s,"  bool executivePdfBusy = false;",
      "  bool executivePdfBusy = false;\n  bool emailBusy = false;",'email busy')
insert=r'''  Future<void> _emailPdf({required bool executive}) async {
    if (emailBusy) return;
    try {
      final target = await ReportEmailService.targetForInspection(
        widget.inspectionId,
      );
      if (!mounted) return;
      final confirmed = await showDialog<bool>(
        context: context,
        builder: (dialogContext) => AlertDialog(
          title: const Text('Enviar relatório por e-mail'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                target.company.name,
                style: const TextStyle(fontWeight: FontWeight.w800),
              ),
              const SizedBox(height: 10),
              Text('Para: ${target.to}'),
              if (target.cc.isNotEmpty) Text('Cópia: ${target.cc}'),
              const SizedBox(height: 10),
              Text(
                executive
                    ? 'Anexo: Relatório Executivo PDF'
                    : 'Anexo: Relatório Completo PDF',
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogContext, false),
              child: const Text('Cancelar'),
            ),
            FilledButton.icon(
              onPressed: () => Navigator.pop(dialogContext, true),
              icon: const Icon(Icons.send_outlined),
              label: const Text('Confirmar envio'),
            ),
          ],
        ),
      ) ?? false;
      if (!confirmed || !mounted) return;

      setState(() => emailBusy = true);
      final bytes = await PdfService.generateInspectionPdf(
        widget.inspectionId,
        executive: executive,
        includeActionPlan: includeActionPlan,
      );
      final fileName = executive
          ? 'Relatorio_Executivo_Auditar_SST.pdf'
          : 'Relatorio_Completo_Auditar_SST.pdf';
      final result = await ReportEmailService.send(
        inspectionId: widget.inspectionId,
        pdfBytes: bytes,
        fileName: fileName,
        target: target,
      );

      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(result.message),
          backgroundColor:
              result.success ? Colors.green.shade700 : Colors.red.shade700,
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            e.toString().replaceFirst('Bad state: ', ''),
          ),
        ),
      );
    } finally {
      if (mounted) setState(() => emailBusy = false);
    }
  }

'''
anchor='  Future<void> _saveLocal({required bool executive}) async {'
s=one(s,anchor,insert+anchor,'email method')
s=s.replace("            onSave: () => _saveLocal(executive: false),\n",
            "            onSave: () => _saveLocal(executive: false),\n            onEmail: () => _emailPdf(executive: false),\n",1)
s=s.replace("            onSave: () => _saveLocal(executive: true),\n",
            "            onSave: () => _saveLocal(executive: true),\n            onEmail: () => _emailPdf(executive: true),\n",1)
s=one(s,"""    required VoidCallback onSave,
    required bool busy,""","""    required VoidCallback onSave,
    required VoidCallback onEmail,
    required bool busy,""",'report email param')
s=one(s,"""                IconButton.outlined(
                  tooltip: 'Salvar no aparelho',
                  onPressed: onSave,
                  icon: const Icon(Icons.download_outlined),
                ),""","""                IconButton.outlined(
                  tooltip: 'Salvar no aparelho',
                  onPressed: onSave,
                  icon: const Icon(Icons.download_outlined),
                ),
                const SizedBox(width: 6),
                IconButton.outlined(
                  tooltip: 'Enviar para o e-mail cadastrado',
                  onPressed: emailBusy ? null : onEmail,
                  icon: emailBusy
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.email_outlined),
                ),""",'report email button')
write(rel,s)

rel='painel_web_google_apps_script/Code.gs'; s=read(rel)
anchor="""    if (request.action === 'test_notifications') {
      if (request.syncKey !== expectedKey) return jsonResponse_({ok: false, message: 'Chave de sincronização inválida.'});
      return jsonResponse_(sendTestNotification_(request.payload || {}));
    }
"""
s=one(s,anchor,anchor+"""
    if (request.action === 'send_report_email') {
      if (request.syncKey !== expectedKey) return jsonResponse_({ok: false, message: 'Chave de sincronização inválida.'});
      return jsonResponse_(sendReportEmail_(request));
    }
""",'backend email route')
marker='function sendTestNotification_(payload) {'
helper=r'''function sendReportEmail_(request) {
  const to = String(request.to || '').trim();
  const cc = String(request.cc || '').trim();
  const companyId = String(request.companyId || '').trim();
  const companyName = String(request.companyName || 'Empresa').trim().substring(0, 160);
  const recipientName = String(request.recipientName || '').trim().substring(0, 160);
  const reportNumber = String(request.reportNumber || '').trim().substring(0, 120);
  const fileName = safeDriveName_(request.fileName, 'Relatorio_Auditar_SST.pdf');
  const mimeType = String(request.mimeType || '').trim().toLowerCase();
  const encoded = String(request.contentBase64 || '').trim();
  const emailPattern = /^[^s@]+@[^s@]+.[^s@]+$/;

  if (!to || !emailPattern.test(to) || (cc && !emailPattern.test(cc))) {
    return {ok: false, message: 'O e-mail cadastrado é inválido.'};
  }
  if (mimeType !== 'application/pdf' || !/.pdf$/i.test(fileName) || !encoded) {
    return {ok: false, message: 'Relatório PDF inválido.'};
  }

  let bytes;
  try {
    bytes = Utilities.base64Decode(encoded);
  } catch (_) {
    return {ok: false, message: 'Não foi possível ler o PDF.'};
  }
  if (!bytes.length || bytes.length > 15 * 1024 * 1024) {
    return {
      ok: false,
      message: 'O relatório deve ter no máximo 15 MB para envio por e-mail.'
    };
  }

  const blob = Utilities.newBlob(bytes, 'application/pdf', fileName);
  const greeting = recipientName
    ? 'Olá, ' + escapeHtml_(recipientName) + '.'
    : 'Olá.';
  const numberLine = reportNumber
    ? '<p><strong>Relatório:</strong> ' + escapeHtml_(reportNumber) + '</p>'
    : '';
  const html = '<div style="font-family:Arial,sans-serif;color:#20242c">' +
    '<h2 style="color:#1d2e6c">Relatório de SST - Auditar</h2><p>' + greeting + '</p>' +
    '<p>Segue em anexo o relatório de Segurança e Saúde no Trabalho da empresa <strong>' +
    escapeHtml_(companyName) + '</strong>.</p>' + numberLine +
    '<p style="color:#667085;font-size:12px">Enviado pelo Auditar SST.</p></div>';

  GmailApp.sendEmail(
    to,
    'Relatório SST - ' + companyName + (reportNumber ? ' - ' + reportNumber : ''),
    'Segue em anexo o relatório de SST.',
    {
      htmlBody: html,
      cc: cc || undefined,
      attachments: [blob],
      name: 'Auditar SST'
    }
  );

  const recipients = [to, cc].filter(Boolean).join(', ');
  markEmailEvent_(
    'manual-report-' + Utilities.getUuid(),
    companyId,
    'Relatório enviado manualmente',
    recipients
  );
  return {
    ok: true,
    message: 'Relatório enviado para ' + recipients + '.'
  };
}

'''
s=one(s,marker,helper+marker,'backend email helper')
write(rel,s)

rel='pubspec.yaml'; s=read(rel)
old,new={
  'android':('3.29.110+252','3.29.111+253'),
  'windows':('3.30.34+221','3.30.35+222'),
}[platform]
if s.count('version: '+old)!=1:
    raise RuntimeError('version mismatch '+old)
write(rel,s.replace('version: '+old,'version: '+new,1))

assert "fallback: performanceTemplateId" in read('lib/services/report_template_service.dart')
assert "Enviar para o e-mail cadastrado" in read('lib/screens/report_screen.dart')
assert "send_report_email" in read('painel_web_google_apps_script/Code.gs')
assert "Multa (referência)" not in read('lib/services/performance_report_pdf_service.dart')
assert "_technicalLine('Risco'" not in read('lib/services/performance_report_pdf_service.dart')
assert "_labelValue('Risco', risk)" not in read('lib/services/styled_report_pdf_service.dart')
assert "RESPONSÁVEL PELA EMPRESA" in read('lib/services/performance_report_pdf_service.dart')
print('REPORT_CLIENT_REQUESTS_EMAIL_OK',platform,new)
