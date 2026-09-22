import 'dart:convert';
import 'dart:io';
import 'package:auditar_sst/models.dart';
import 'package:auditar_sst/services/express_round_pdf_service.dart';
import 'package:auditar_sst/services/report_template_service.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:image/image.dart' as img;

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  test('30 and 50 photo reports with long narrative and custom layout', () async {
    final dir = await Directory.systemTemp.createTemp('auditar_ronda_50_');
    try {
      final company = Company(id: 'company-load', name: 'Empresa exemplo');
      final sector = Sector(id: 'sector-load', companyId: company.id, name: 'Produção');
      final records = <SstRecord>[];
      final raster = img.Image(width: 480, height: 340);
      for (var i = 0; i < 50; i++) {
        raster.setPixelRgb(i * 7 % 480, i * 5 % 340, 50 + i, 30 + i, 20 + i);
        final photo = File('${dir.path}/evidencia_$i.png');
        await photo.writeAsBytes(img.encodePng(raster));
        records.add(SstRecord(
          id: 'registro-$i', companyId: company.id, sectorId: sector.id,
          type: 'OBSERVACAO_SEGURANCA', title: 'NC $i',
          date: DateTime(2026, 9, 22, 9, i),
          priority: i % 8 == 0 ? 'Crítica' : 'Alta',
          payload: {
            'photoPath': photo.path,
            'description': 'Achado constatado pelo técnico no registro $i. ' * 14,
            'risk': 'Risco informado pelo técnico sem inventar medição. ' * 9,
            'recommendation': 'Corrigir a situação e verificar eficácia. ' * 10,
            'likelyReferences': ['NR-01', 'NR-12'],
          },
        ));
      }
      final custom = ReportTemplateService.currentTemplate.copyWith(
        id: 'large-custom', name: 'Fotográfico personalizado',
        showCover: true, photoColumns: 3, showChecklistDetails: true,
        headerTitle: 'RELATÓRIO COMPLETO DA VISTORIA',
      );
      final scenarios = [
        (30, ExpressRoundReportStyle.photographic, null, 'ronda_30_fotografico.pdf'),
        (50, ExpressRoundReportStyle.photographic, custom, 'ronda_50_personalizado.pdf'),
        (50, ExpressRoundReportStyle.technical, custom, 'ronda_50_tecnico.pdf'),
      ];
      final out = Directory('report_stress_samples');
      await out.create(recursive: true);
      for (final scenario in scenarios) {
        final pdf = await ExpressRoundPdfService.generate(
          company: company, sectors: [sector],
          records: records.take(scenario.$1).toList(),
          style: scenario.$2,
          template: scenario.$3,
          aiReview: {
            'summary': 'Síntese baseada nas observações fornecidas. ' * 45,
            'limitations': 'Sem medição quantitativa nesta amostra. ' * 20,
          },
          aiConclusion: 'Conclusão revista pelo responsável técnico. ' * 85,
        );
        expect(pdf.length, greaterThan(4000), reason: scenario.$4);
        expect(ascii.decode(pdf.take(5).toList()), '%PDF-', reason: scenario.$4);
        await File('${out.path}/${scenario.$4}').writeAsBytes(pdf);
      }
    } finally {
      await dir.delete(recursive: true);
    }
  });
}
