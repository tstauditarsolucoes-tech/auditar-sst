/// Conclusão padrão da vistoria Auditar SST.
/// Texto técnico inicial; o responsável sempre deve revisar antes de salvar.
/// Não usa IA, não altera relatórios existentes nem persiste registros.
class AuditarUnifiedConclusion {
  static String fromRound({
    required String companyName,
    required int findings,
    required int conformities,
    required int nonConformities,
    int highPriority = 0,
    int possibleRecurrences = 0,
  }) {
    if (findings <= 0) {
      return 'Não há registros suficientes para estabelecer uma conclusão '
          'técnica. Confira as constatações e a aplicabilidade antes da emissão.';
    }
    final parts = <String>[
      'A vistoria na empresa ${companyName.trim()} registrou $findings '
          'achado(s): $conformities conformidade(s) ou boa(s) prática(s) '
          'e $nonConformities não conformidade(s).',
      'A análise se limita às áreas, condições e evidências efetivamente '
          'verificadas; a ausência de registro não comprova ausência de riscos.',
      if (nonConformities > 0)
        'As $nonConformities não conformidade(s) exigem tratamento conforme '
            'as recomendações e prioridades de cada constatação.',
      if (highPriority > 0)
        'Foram identificados $highPriority registro(s) com prioridade alta '
            'ou crítica, que demandam avaliação e tratamento prioritários.',
      if (possibleRecurrences > 0)
        'Existem $possibleRecurrences indicação(ões) de possível recorrência, '
            'cuja confirmação depende de verificar as medidas anteriores.',
      if (nonConformities == 0)
        'Não foram registradas não conformidades nos achados apresentados. '
            'As boas práticas identificadas devem ser mantidas.',
      if (nonConformities > 0)
        'Recomenda-se estabelecer responsáveis, prazos e evidências para '
            'realizar as correções e verificar posteriormente sua eficácia.',
      'Esta conclusão se limita à data e aos dados registrados e deve ser '
          'revisada pelo técnico antes da emissão do relatório.',
    ];
    return parts.join(' ');
  }
}
