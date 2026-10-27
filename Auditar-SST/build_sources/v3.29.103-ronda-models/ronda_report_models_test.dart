import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:image/image.dart' as img;
import 'package:auditar_sst/models.dart';
import 'package:auditar_sst/services/express_round_pdf_service.dart';
import 'package:auditar_sst/services/report_template_service.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('Ronda accepts Checklist preset and custom layouts with four photos', () async {
    final dir = await Directory.systemTemp.createTemp('ronda_modelos_');
    try {
      final photo = File('${dir.path}/evidencia.png');
      await photo.writeAsBytes(img.encodePng(img.Image(width: 500, height: 330)));
      final company = Company(id: 'empresa-1', name: 'Empresa de Teste SST');
      final sector = Sector(id: 'setor-1', companyId: company.id, name: 'Produção');
      final records = List.generate(4, (index) => SstRecord(
        id: 'achado-$index',
        companyId: company.id,
        sectorId: sector.id,
        type: 'OBSERVACAO_SEGURANCA',
        title: 'Registro $index',
        date: DateTime(2026, 9, 22),
        priority: 'Alta',
        payload: {
          'photoPath': photo.path,
          'description': 'Descrição identificada pelo técnico em campo. ' * 17,
          'risk': 'Risco a ser verificado presencialmente. ' * 12,
          'recommendation': 'Verificar e corrigir a situação observada. ' * 15,
          'likelyReferences': ['NR-01', 'NR-12'],
        },
      ));
      final presets = <ReportTemplateDefinition>[
        ReportTemplateService.currentTemplate,
        ReportTemplateService.currentTemplate.copyWith(
          id: 'modelo-customizado',
          name: 'Modelo personalizado',
          headerTitle: 'MEU RELATÓRIO DE CAMPO',
          photoColumns: 3,
          showCover: false,
          showChecklistDetails: true,
          signatureStyle: 'manual',
          logoMode: 'nenhuma',
          primaryColor: '#2C4B72',
          secondaryColor: '#157A46',
        ),
      ];
      for (final preset in presets) {
        for (final style in ExpressRoundReportStyle.values) {
          final pdf = await ExpressRoundPdfService.generate(
            company: company,
            sectors: [sector],
            records: records,
            style: style,
            template: preset,
            aiReview: {'summary': 'Revisão técnica da IA. ' * 25},
            aiConclusion: 'Conclusão aprovada pelo técnico. ' * 50,
          );
          expect(pdf.length, greaterThan(2200));
          expect(ascii.decode(pdf.take(5).toList()), '%PDF-');
        }
      }
    } finally {
      await dir.delete(recursive: true);
    }
  });
}
