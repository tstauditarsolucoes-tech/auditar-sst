#!/usr/bin/env python3
"""Regression for approved client-facing PDF presentation and email delivery."""
from pathlib import Path
import sys
root=Path(sys.argv[1]);expected=sys.argv[2]
pub=(root/'pubspec.yaml').read_text(encoding='utf-8')
assert 'version: '+expected in pub
get=lambda name:(root/'lib/services'/name).read_text(encoding='utf-8')
templates=get('report_template_service.dart')
styled=get('styled_report_pdf_service.dart')
performance=get('performance_report_pdf_service.dart')
legacy=get('pdf_service.dart')
screen=(root/'lib/screens/report_screen.dart').read_text(encoding='utf-8')
backend=(root/'painel_web_google_apps_script/Code.gs').read_text(encoding='utf-8')
mail=(root/'painel_web_google_apps_script/ReportEmail.gs').read_text(encoding='utf-8')
for marker in ['Auditar Executivo','Performance - Foto + Descrição','Auditar Fotográfico',
 'Auditar Obra','Auditar Técnico Clean','Auditar NR-12','Auditar Gerencial Padrão',
 'fallback: performanceTemplateId']:
 assert marker in templates,marker
assert 'PerformanceReportPdfService.generateInspectionPdf' in styled
assert 'Resumo da vistoria' in styled and 'Pontos de atenção' in styled
assert 'Anexo técnico — Checklist detalhado' in styled
assert 'não constitui confirmação de regularização posterior' in styled
assert '_managementSummary' in performance and 'CONCLUSÃO' in performance
assert 'não representa confirmação de regularização posterior' in performance
assert "if (companyCnpj.trim().isNotEmpty)" in performance
assert "_coverLine('CNPJ', companyCnpj)" in styled
assert "_coverLine('Endereço', companyAddress)" in styled
assert 'RESPONSÁVEL PELA EMPRESA' in performance
assert "box(responsible, 'Responsável da empresa'" in styled
assert "'Multa por descumprimento'" not in legacy
assert "'Multa (valor de referência)'" not in legacy
assert "_fineSummaryCard(" in legacy and legacy.count('_fineSummaryCard(')==1
assert "_fineSummaryCard(" in styled and styled.count('_fineSummaryCard(')==1
assert '_fineForReport(issue.answer)' not in performance
assert "_labelValue('Risco', risk)" not in styled
assert "_technicalLine('Risco', risk)" not in performance
assert "_priorityChip(priority)" not in styled
assert "'PRIORIDADE: ${priority.toUpperCase()}'" not in performance
assert 'template.description,' not in styled
assert "report_email_send" in backend and "reportEmailSend_(request)" in backend
assert "Enviar PDF ao e-mail cadastrado" in screen
assert "class ReportEmailService" in get('report_email_service.dart')
assert 'MailApp.sendEmail(' in mail and 'userCanAccessCompany_' in mail
for fragment in ['DeviceSyncService','MediaSyncService','AppsScriptHttp','WebServiceConfig']:
 assert fragment not in templates+styled+performance
print('REPORT_DELIVERY_V329111_REGRESSION_OK',expected)
