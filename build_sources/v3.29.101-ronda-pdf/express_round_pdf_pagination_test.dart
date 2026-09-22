import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:image/image.dart' as img;
import 'package:auditar_sst/models.dart';
import 'package:auditar_sst/services/express_round_pdf_service.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  final company = Company(id: 'company-test', name: 'Empresa de Teste SST');
  final sectors = [Sector(id: 'sector-test', companyId: 'company-test', name: 'Produção')];

  test('ronda com quatro registros, foto e conclusão IA gera ambos PDFs', () async {
    final temp = await Directory.systemTemp.createTemp('auditar_ronda_pdf_test_');
    try {
      final photo = File('${temp.path}/evidencia.png');
      await photo.writeAsBytes(img.encodePng(img.Image(width: 640, height: 400)));
      final records = List.generate(4, (i) => SstRecord(
        id: 'record-$i',
        companyId: company.id,
        sectorId: 'sector-test',
        type: 'OBSERVACAO_SEGURANCA',
        title: 'Achado $i',
        date: DateTime(2026, 9, 22),
        priority: i.isEven ? 'Alta' : 'Média',
        payload: {
          'photoPath': photo.path,
          'categories': ['Incêndio', 'Máquinas', 'Elétrica'],
          'description': 'Proteção insuficiente no equipamento. ' * 8,
          'risk': 'Contato mecânico e projeção de partículas. ' * 7,
          'possibleConsequence': 'Possível lesão durante a operação. ' * 6,
          'recommendation': 'Corrigir e verificar antes da retomada. ' * 8,
          'immediateAction': 'Sinalizar e restringir acesso. ' * 6,
          'likelyReferences': ['NR-01', 'NR-12', 'NR-23'],
          'location': 'Produção',
        },
      ));
      for (final style in ExpressRoundReportStyle.values) {
        final bytes = await ExpressRoundPdfService.generate(
          company: company,
          sectors: sectors,
          records: records,
          style: style,
          aiReview: {'riskAssessment': 'Revisão da IA para cada registro. ' * 12},
          aiConclusion: 'Conclusão revisada pelo responsável técnico. ' * 15,
        );
        expect(bytes.length, greaterThan(2000));
        expect(ascii.decode(bytes.take(5).toList()), '%PDF-');
      }
    } finally {
      await temp.delete(recursive: true);
    }
  });

  test('textos extensos são paginados sem Infinity ou perda por corte', () async {
    final records = List.generate(4, (i) => SstRecord(
      id: 'long-$i',
      companyId: company.id,
      type: 'OBSERVACAO_SEGURANCA',
      title: 'Ocorrência $i',
      date: DateTime(2026, 9, 22),
      payload: {
        'description': 'Descrição técnica detalhada, incluindo cenário e evidência. ' * 20,
        'risk': 'Risco identificado na avaliação em campo. ' * 14,
        'recommendation': 'Recomendação de melhoria e acompanhamento da correção. ' * 20,
        'possibleConsequence': 'Consequência potencial do achado. ' * 12,
        'likelyReferences': ['NR-01', 'NR-12'],
      },
    ));
    for (final style in ExpressRoundReportStyle.values) {
      final bytes = await ExpressRoundPdfService.generate(
        company: company,
        sectors: sectors,
        records: records,
        style: style,
        aiReview: {
          'situacoes': 'Revisão técnica detalhada para o relatório. ' * 60,
          'recomendacoes': 'Acompanhamento das ações corretivas. ' * 45,
        },
        aiConclusion: 'Conclusão revisada pela equipe técnica. ' * 85,
      );
      expect(bytes.length, greaterThan(2000));
      expect(ascii.decode(bytes.take(5).toList()), '%PDF-');
    }
  });
}
