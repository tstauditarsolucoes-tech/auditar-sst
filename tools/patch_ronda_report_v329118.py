#!/usr/bin/env python3
"""Public-facing field inspection report, using existing PDF renderer/templates.
Do not modify checklist, synchronization, media queue, database schema or GS.
"""
from pathlib import Path
import sys
root=Path(sys.argv[1]); platform=sys.argv[2]
assert platform in ('android','windows')
def p(name):return root/name
def update(name,old,new,label):
 path=p(name);s=path.read_text(encoding='utf-8')
 count=s.count(old)
 if count!=1:raise RuntimeError(f'{label}: expected once, got {count}')
 path.write_text(s.replace(old,new,1),encoding='utf-8',newline='\n')

pdf='lib/services/express_round_pdf_service.dart'
screen='lib/screens/express_round_screen.dart'
for old,new in [
 ("pw.Document(title: 'Relatório de ronda expressa')","pw.Document(title: 'Relatório de vistoria SST')"),
 ("'RELATÓRIO DE RONDA EXPRESSA'","'RELATÓRIO DE VISTORIA SST'"),
 ("'RONDA EXPRESSA DE SEGURANÇA'","'VISTORIA PRESENCIAL DE SEGURANÇA DO TRABALHO'"),
 ("'Auditar SST - Ronda Expressa'","'Auditar Soluções • Segurança e Saúde no Trabalho'"),
 ("'RELATÓRIO FOTOGRÁFICO DE RONDA DE SEGURANÇA'","'RELATÓRIO FOTOGRÁFICO DE VISTORIA SST'"),
 ("'RELATÓRIO TÉCNICO DE RONDA DE SEGURANÇA'","'RELATÓRIO TÉCNICO DE VISTORIA SST'"),
 ("'ACHADOS DA RONDA'","'CONSTATAÇÕES DA VISTORIA'"),
 ("'SÍNTESE TÉCNICA DA RONDA'","'SÍNTESE TÉCNICA'"),
 ("'CONCLUSÃO GERAL DA RONDA'","'CONCLUSÃO'"),
 ("'Pontos a confirmar presencialmente'","'Verificações complementares recomendadas'"),
 ("'ANEXO TÉCNICO DOS ACHADOS'","'INFORMAÇÕES COMPLEMENTARES'"),
 ("'Conformidades e não conformidades registradas em campo'","'Constatações e evidências da vistoria presencial'"),
]:update(pdf,old,new,'public title: '+old)
# The selected template keeps its branding, colors, cover and optional blocks.
# A photo + description card is clearer than a grid of disconnected pictures and text.
update(pdf,"""    final photographicGrid =
        style == ExpressRoundReportStyle.photographic &&
        template != null &&
        template.photoColumns > 1;""",
"""    // One evidence card per finding. Two-column split inside each card is
    // the Performance model's photo + description, not detached photo tiles.
    final photographicGrid = false;""",'photographic layout')
# The company visit is recorded by a technician onsite; do not insert a
# fabricated "remote/photo-only assessment" disclaimer in the final report.
update(pdf,"""'Registrar evidências observadas durante a ronda de segurança, destacando não conformidades que demandam tratativa e conformidades/boas práticas que devem ser mantidas. As referências normativas apresentadas pela IA são indicativas e devem ser conferidas pelo responsável técnico antes da emissão definitiva.',""",
"""'Documentar as situações verificadas presencialmente, com registros fotográficos, descrição das constatações e recomendações de correção ou manutenção.',""",'field objective')
# Don't publish raw AI draft/limitations or a conclusion that erroneously says
# that an onsite visit did not happen. Keep any approved conclusions in storage.
update(pdf,"""              if (aiReview.isNotEmpty) ...[
                pw.SizedBox(height: 14),
                ..._aiReviewBlocks(aiReview, primary),
              ],
              if (aiConclusion.trim().isNotEmpty) ...[
                pw.SizedBox(height: 14),
                ..._conclusionBlocks(aiConclusion, primary),
              ],""",
"""              pw.SizedBox(height: 14),
              pw.Text('CONCLUSÃO',style:pw.TextStyle(
                fontSize:11,fontWeight:pw.FontWeight.bold,color:primary)),
              pw.SizedBox(height: 5),
              pw.Text(
                nonConformities == 0
                    ? 'Na vistoria presencial foram registrados ${sorted.length} item(ns), sem não conformidades nos registros apresentados. Recomenda-se manter os controles e acompanhar as condições observadas.'
                    : 'Na vistoria presencial foram registrados ${sorted.length} item(ns), sendo ${nonConformities} não conformidade(s) e ${conformities} conformidade(s). Recomenda-se executar as correções descritas, priorizar os itens classificados como alta ou crítica e verificar a eficácia das ações em acompanhamento posterior.',
                style:const pw.TextStyle(fontSize:9,lineSpacing:2)),
""",'field conclusion')
# Avoid duplicate verbose prose in photographic cards; risk/consequence data
# stay in records, but description and recommendation are presented separately.
update(pdf,"""    final narrative = <String>[
      if (description.isNotEmpty) description,
      if (!conform && risk.isNotEmpty) 'Risco identificado: $risk.',
      if (recommendation.isNotEmpty)
        conform
            ? 'Manutenção do padrão: $recommendation'
            : 'Recomendação: $recommendation',
      if (refs.isNotEmpty)
        'Referências prováveis para conferência: ${refs.join(', ')}.',
    ].join('\\n\\n');""",
"""    final narrative = description
        .split(RegExp(r'Risco identificado:|Recomendação:|Referências prováveis',
          caseSensitive:false)).first.trim();""",'clean field narrative')
update(pdf,"""      limit: 260,
    );""","""      limit: 135,
    );""",'card excerpt')
update(pdf,"""      pw.Padding(
        padding: const pw.EdgeInsets.fromLTRB(8, 3, 8, 8),
        child: pw.Text(
          _locationLine(record, sectors),""",
"""      if (recommendation.isNotEmpty)
        ..._pagedLabel(conform ? 'Manter boa prática' : 'Recomendação',
          recommendation,primary),
      pw.Padding(
        padding: const pw.EdgeInsets.fromLTRB(8, 3, 8, 8),
        child: pw.Text(
          _locationLine(record, sectors),""",'recommendation after photo')
# Show two signatures, without implying company signed.
update(pdf,"""              pw.SizedBox(height: 12),
            ],
      ),""",
"""              pw.SizedBox(height: 14),
              pw.Center(child:pw.Column(children:[
                pw.Container(width:230,decoration:const pw.BoxDecoration(
                    border:pw.Border(bottom:pw.BorderSide()))),
                pw.SizedBox(height:4),
                pw.Text('Responsável pela empresa / assinatura',
                    style:const pw.TextStyle(fontSize:9)),
              ])),
              pw.SizedBox(height: 12),
            ],
      ),""",'company signature')
# Template grid itself remains available for checklist; only Ronda renders
# a single compact card at a time. AI meta map never goes into client PDF.

# Start visual feedback immediately; do not force a long AI review before PDF.
update(screen,"""    if (roundRecords.isEmpty || generatingReport) return;
    if (roundAiConclusion.trim().isEmpty) {
      final prepared = await _prepareRoundConclusion();
      if (!prepared || !mounted) return;
    }
    setState(() => generatingReport = true);
    try {""",
"""    if (roundRecords.isEmpty || generatingReport) return;
    setState(() => generatingReport = true);
    _message('Preparando o relatório de vistoria em PDF...');
    await Future<void>.delayed(Duration.zero);
    try {""",'visible generation')
# Need not attempt remote media restoration if local evidence is present.
update(screen,"""      try {
        await MediaSyncService.restoreRoundMedia(
          companyId: widget.company.id,
          roundId: roundId,
        ).timeout(const Duration(seconds: 18));
        await _reloadRoundRecords();
      } catch (_) {}""",
"""      if (roundRecords.any((r) {
        final path='${r.payload['photoPath'] ?? ''}'.trim();
        return path.isNotEmpty && !File(path).existsSync();
      })) {
        try {
          await MediaSyncService.restoreRoundMedia(
            companyId: widget.company.id, roundId: roundId,
          ).timeout(const Duration(seconds: 7));
          await _reloadRoundRecords();
        } catch (_) {}
      }
      if (mounted) _message('Montando páginas e evidências do PDF...');""",'conditional media restore')
for old,new in [
 ("title: const Text('Documento da Ronda Expressa')","title: const Text('Relatório de vistoria pronto')"),
 ("title: 'Ronda Expressa',","title: 'Relatório de vistoria SST',"),
 ("fileName: 'Ronda_Expressa_${widget.company.id}.pdf',","fileName: 'Relatorio_Vistoria_${widget.company.id}.pdf',"),
 ("'Ronda_${styleName}_${safeModel}_${safeCompany.isEmpty ? 'Empresa' : safeCompany}.pdf'","'Vistoria_${styleName}_${safeModel}_${safeCompany.isEmpty ? 'Empresa' : safeCompany}.pdf'"),
]:update(screen,old,new,'delivery label '+old)
# UI: don't suggest unreviewed generated conclusion automatically gets included.
update(screen,"'Os registros e a conclusão revisada da IA serão mantidos.'",
      "'Os registros, fotos e recomendações disponíveis serão preservados.'",
      'model selection description')
print('FIELD_REPORT_PROFESSIONAL_LAYOUT_OK',platform)
