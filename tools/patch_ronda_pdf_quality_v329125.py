#!/usr/bin/env python3
"""Client-facing Ronda PDF fixes only; sync, media, database, GS and AI are protected."""
from pathlib import Path
import hashlib
import sys

root=Path(sys.argv[1])
target=root/'lib/services/express_round_pdf_service.dart'
protected=[
    'lib/database.dart',
    'lib/services/device_sync_service.dart',
    'lib/services/sync_coordinator.dart',
    'lib/services/media_sync_service.dart',
    'lib/services/drive_service.dart',
    'lib/services/apps_script_http.dart',
    'lib/services/ai_assistant_service.dart',
    'painel_web_google_apps_script/Code.gs',
    'painel_web_google_apps_script/MultiUser.gs',
    'painel_web_google_apps_script/ClientPortal.gs',
]
baseline={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in protected}
s=target.read_text(encoding='utf-8')

def once(a,b,label):
    global s
    if s.count(a)!=1: raise RuntimeError('RONDA_PDF_QUALITY missing/ambiguous '+label+': '+str(s.count(a)))
    s=s.replace(a,b,1)

# Show visit date separately from date of report issuance.
once('              _companyTable(company),',
     '              _companyTable(company, sorted.isEmpty ? null : sorted.first.date),',
     'visit-date call')
once('  static pw.Widget _companyTable(Company company) => pw.Table(',
     '  static pw.Widget _companyTable(Company company, DateTime? visitDate) => pw.Table(',
     'visit-date method')
once("      _tableRow('EMPRESA', company.name),",
     "      _tableRow('EMPRESA', company.name),\n"
     "      if (visitDate != null)\n"
     "        _tableRow('DATA DA VISTORIA', DateFormat('dd/MM/yyyy').format(visitDate)),",
     'visit-date row')

# No unsupported assumption that every source record was collected onsite.
once("'VISTORIA PRESENCIAL DE SEGURANÇA DO TRABALHO'",
     "'SEGURANÇA E SAÚDE NO TRABALHO'",'cover subtitle')
once("'Constatações e evidências da vistoria presencial'",
     "'Constatações e evidências registradas na vistoria'",'body subtitle')
once("'Documentar as situações verificadas presencialmente, com registros fotográficos, descrição das constatações e recomendações de correção ou manutenção.'",
     "'Documentar as situações registradas na vistoria, com evidências fotográficas disponíveis e recomendações correspondentes.'",
     'objective')
once("'Na vistoria presencial foram registrados ${sorted.length} item(ns), sem não conformidades nos registros apresentados. Recomenda-se manter os controles e acompanhar as condições observadas.'",
     "'Nos registros desta vistoria constam ${sorted.length} item(ns), sem não conformidades registradas. Recomenda-se manter os controles observados e acompanhar suas condições.'",
     'no-findings conclusion')
once("'Na vistoria presencial foram registrados ${sorted.length} item(ns), sendo ${nonConformities} não conformidade(s) e ${conformities} conformidade(s). Recomenda-se executar as correções descritas, priorizar os itens classificados como alta ou crítica e verificar a eficácia das ações em acompanhamento posterior.'",
     "'Nos registros desta vistoria constam ${sorted.length} item(ns), sendo ${nonConformities} não conformidade(s) e ${conformities} conformidade(s). Recomenda-se programar as correções descritas e verificar sua execução em acompanhamento posterior.'",
     'findings conclusion')

# The optional photographic technical appendix repeated every finding, its
# description and recommendation; keep just the original photo+description.
begin="              if (style == ExpressRoundReportStyle.photographic &&\n                  template?.showChecklistDetails == true) ...["
end="              pw.SizedBox(height: 14),\n              pw.Text(\n                'CONCLUSÃO',"
a=s.find(begin); b=s.find(end,a)
if a<0 or b<0 or s.count(begin)!=1: raise RuntimeError('RONDA_PDF_QUALITY repeated appendix')
s=s[:a]+s[b:]

# When photo is unavailable, retain recommendation and paginate long text.
a=s.index('  static List<pw.Widget> _photographicBlocks(')
b=s.index('  static List<pw.Widget> _technicalBlocks(',a)
p=s[a:b]
old="""              pw.Text(
                narrative.isEmpty ? record.title : narrative,
                style: const pw.TextStyle(fontSize: 8.2, lineSpacing: 1.5),
                textAlign: pw.TextAlign.justify,
              ),"""
new="""              pw.Text(
                parts.isEmpty ? record.title : parts.first,
                style: const pw.TextStyle(fontSize: 8.2, lineSpacing: 1.5),
                textAlign: pw.TextAlign.justify,
              ),"""
if p.count(old)!=1: raise RuntimeError('RONDA_PDF_QUALITY missing-image paragraph')
p=p.replace(old,new,1)
old="""          ),
        ),
      ];
    }
    return [
      pw.Container(
        margin: const pw.EdgeInsets.only(bottom: 3),"""
new="""          ),
        ),
        for (var i = 1; i < parts.length; i++)
          pw.Padding(
            padding: const pw.EdgeInsets.fromLTRB(8, 2, 8, 3),
            child: pw.Text(parts[i], style: const pw.TextStyle(fontSize: 8.4, lineSpacing: 1.4)),
          ),
        if (recommendation.isNotEmpty)
          ..._pagedLabel(conform ? 'Manter boa prática' : 'Recomendação', recommendation, primary),
      ];
    }
    return [
      pw.Container(
        margin: const pw.EdgeInsets.only(bottom: 3),"""
if p.count(old)!=1: raise RuntimeError('RONDA_PDF_QUALITY missing-image recommendation')
s=s[:a]+p.replace(old,new,1)+s[b:]

# Deduplicate sector and local labels (e.g. PRODUÇÃO - PRODUÇÃO).
a=s.index('  static String _locationLine(')
b=s.index('  static pw.MemoryImage? _secondPhoto(',a)
p=s[a:b]
old="""    return [
      sector,
      location,
      date,
    ].where((value) => value.isNotEmpty).join('  -  ');"""
new="""    final places = <String>[];
    for (final value in [sector, location]) {
      final cleaned = value.trim();
      if (cleaned.isNotEmpty &&
          !places.any((other) => other.toLowerCase() == cleaned.toLowerCase())) {
        places.add(cleaned);
      }
    }
    return [...places, date].join('  -  ');"""
if p.count(old)!=1: raise RuntimeError('RONDA_PDF_QUALITY location')
s=s[:a]+p.replace(old,new,1)+s[b:]

# Technical report must label photos that were referenced but cannot be read.
a=s.index('  static List<pw.Widget> _technicalBlocks(')
b=s.index('  static List<pw.Widget> _aiReviewBlocks(',a)
p=s[a:b]
old="""      ],
      pw.SizedBox(height: 7),
      ..._pagedLabel(
        conform ? 'Boa prática observada' : 'Situação encontrada',"""
new="""      ],
      if (includePhoto && (photo == null && photo2 == null) &&
          ('${p['photoPath'] ?? ''}'.trim().isNotEmpty ||
           '${p['photoPath2'] ?? ''}'.trim().isNotEmpty))
        pw.Text('Evidência fotográfica indisponível neste arquivo.',
          style: const pw.TextStyle(fontSize: 7.5, color: PdfColors.grey700)),
      pw.SizedBox(height: 7),
      ..._pagedLabel(
        conform ? 'Boa prática observada' : 'Situação encontrada',"""
if p.count(old)!=1: raise RuntimeError('RONDA_PDF_QUALITY technical missing-image')
s=s[:a]+p.replace(old,new,1)+s[b:]
target.write_text(s,encoding='utf-8',newline='\n')
changed=[p for p,h in baseline.items() if hashlib.sha256((root/p).read_bytes()).hexdigest()!=h]
if changed: raise SystemExit('PROTECTED SYNC/MEDIA/DB/GS/AI MODIFIED: '+repr(changed))
print('RONDA_PDF_QUALITY_ISOLATED_OK')
