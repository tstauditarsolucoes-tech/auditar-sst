class OfflineFieldRuleResult {
  const OfflineFieldRuleResult({
    required this.nrs,
    required this.priority,
    required this.score,
    required this.actionPlan,
    required this.responsibleSuggestion,
    required this.deadlineSuggestion,
    required this.possibleRecurrence,
  });

  final List<String> nrs;
  final String priority;
  final int score;
  final String actionPlan;
  final String responsibleSuggestion;
  final String deadlineSuggestion;
  final bool possibleRecurrence;
}

class OfflineFieldRulesService {
  const OfflineFieldRulesService._();

  static OfflineFieldRuleResult analyze({
    required String text,
    required int probability,
    required int severity,
    bool recurring = false,
    bool learnedHistoryMatch = false,
  }) {
    final normalized = _normalize(text);
    final nrs = suggestNrs(normalized);
    final priority = priorityFromMatrix(
      probability,
      severity,
      recurring: recurring,
    );
    return OfflineFieldRuleResult(
      nrs: nrs,
      priority: priority,
      score: matrixScore(probability, severity, recurring: recurring),
      actionPlan: buildActionPlan(normalized, priority),
      responsibleSuggestion: suggestResponsible(normalized),
      deadlineSuggestion: suggestDeadline(priority),
      possibleRecurrence: recurring || learnedHistoryMatch,
    );
  }

  static int matrixScore(
    int probability,
    int severity, {
    bool recurring = false,
  }) {
    final p = probability < 1 ? 1 : (probability > 5 ? 5 : probability);
    final s = severity < 1 ? 1 : (severity > 5 ? 5 : severity);
    final total = (p * s) + (recurring ? 2 : 0);
    return total > 25 ? 25 : total;
  }

  static String priorityFromMatrix(
    int probability,
    int severity, {
    bool recurring = false,
  }) {
    final score = matrixScore(probability, severity, recurring: recurring);
    if (score <= 4) return 'Baixa';
    if (score <= 9) return 'Média';
    if (score <= 16) return 'Alta';
    return 'Crítica';
  }

  static List<String> suggestNrs(String text) {
    final value = _normalize(text);
    final out = <String>{};

    void add(String nr, Iterable<String> terms) {
      if (terms.any(value.contains)) out.add(nr);
    }

    add('NR-01', const [
      'risco', 'perigo', 'nao conform', 'condicao insegura', 'ato inseguro',
    ]);
    add('NR-06', const [
      'epi', 'capacete', 'luva', 'oculos', 'protetor auricular',
      'respirador', 'mascara', 'botina', 'perneira', 'avental',
    ]);
    add('NR-10', const [
      'eletric', 'painel', 'fiacao', 'cabo energ', 'aterramento', 'choque',
    ]);
    add('NR-11', const [
      'empilhadeira', 'movimentacao de carga', 'transporte de materiais',
      'armazenamento', 'empilhamento',
    ]);
    add('NR-12', const [
      'maquina', 'sensor', 'botoeira', 'emergencia', 'protecao',
      'parte movel', 'prensa', 'esteira', 'betoneira',
    ]);
    add('NR-15', const [
      'ruido', 'calor', 'agente quimico', 'poeira', 'poeira mineral',
    ]);
    add('NR-17', const [
      'ergonom', 'postura', 'levantamento manual', 'peso',
      'sobrecarga', 'repetitiv',
    ]);
    add('NR-18', const [
      'obra', 'construcao', 'andaime', 'escavacao', 'canteiro',
    ]);
    add('NR-20', const [
      'inflamavel', 'combustivel', 'gasolina', 'diesel', 'glp',
    ]);
    add('NR-23', const [
      'extintor', 'incendio', 'hidrante', 'rota de fuga',
    ]);
    add('NR-24', const [
      'refeitorio', 'banheiro', 'sanitario', 'vestiario', 'agua potavel',
    ]);
    add('NR-26', const [
      'sinalizacao', 'placa', 'rotulagem', 'identificacao',
    ]);
    add('NR-33', const ['espaco confinado']);
    add('NR-35', const [
      'altura', 'linha de vida', 'cinto paraquedista',
      'queda de nivel', 'telhado',
    ]);

    return out.toList()..sort(_nrSort);
  }

  static String buildActionPlan(String text, String priority) {
    final value = _normalize(text);
    String action;
    if (value.contains('extintor')) {
      action =
          'Regularizar o ponto do extintor, manter acesso livre, identificação visível e conferir a condição do equipamento.';
    } else if (value.contains('painel') ||
        value.contains('eletric') ||
        value.contains('fiacao')) {
      action =
          'Isolar a condição quando houver exposição elétrica e encaminhar a regularização a profissional autorizado antes da liberação.';
    } else if (value.contains('maquina') ||
        value.contains('sensor') ||
        value.contains('botoeira') ||
        value.contains('protecao')) {
      action =
          'Interromper a condição insegura quando houver acesso à zona de perigo, corrigir o dispositivo ou proteção e testar antes da liberação.';
    } else if (value.contains('epi') ||
        value.contains('capacete') ||
        value.contains('luva') ||
        value.contains('protetor auricular') ||
        value.contains('botina')) {
      action =
          'Regularizar o EPI adequado, orientar o trabalhador e reforçar a supervisão do uso durante a atividade e circulação em área de risco.';
    } else if (value.contains('altura') ||
        value.contains('andaime') ||
        value.contains('linha de vida')) {
      action =
          'Restringir a atividade até a regularização das medidas de proteção contra quedas e somente liberar após verificação das condições seguras.';
    } else if (value.contains('organiz') ||
        value.contains('obstru') ||
        value.contains('material')) {
      action =
          'Organizar a área, remover obstruções e definir local adequado para materiais, mantendo circulação e acessos livres.';
    } else {
      action =
          'Corrigir a condição registrada, definir responsável, comprovar a regularização com evidência e verificar a eficácia no acompanhamento.';
    }

    if (priority == 'Crítica') {
      return action +
          ' Tratamento imediato recomendado antes da continuidade da condição de risco.';
    }
    if (priority == 'Alta') {
      return action + ' Priorizar a correção e acompanhar até a conclusão.';
    }
    return action;
  }

  static String suggestResponsible(String text) {
    final value = _normalize(text);
    if (value.contains('eletric') ||
        value.contains('maquina') ||
        value.contains('sensor') ||
        value.contains('botoeira') ||
        value.contains('manutencao')) {
      return 'Manutenção / responsável técnico';
    }
    if (value.contains('epi') ||
        value.contains('treinamento') ||
        value.contains('procedimento')) {
      return 'Supervisão da área / SST';
    }
    if (value.contains('extintor') || value.contains('sinalizacao')) {
      return 'Gestão da unidade / responsável da área';
    }
    return 'Responsável da área a definir';
  }

  static String suggestDeadline(String priority) {
    switch (priority) {
      case 'Crítica':
        return 'Imediato / antes da continuidade da condição de risco';
      case 'Alta':
        return 'Prioritário — sugerido até 7 dias, conforme viabilidade e risco';
      case 'Média':
        return 'Programar correção — sugerido até 30 dias';
      default:
        return 'Programar melhoria — sugerido até 60 dias';
    }
  }

  static int _nrSort(String a, String b) {
    int value(String nr) =>
        int.tryParse(nr.replaceAll(RegExp(r'[^0-9]'), '')) ?? 999;
    return value(a).compareTo(value(b));
  }

  static String _normalize(String input) {
    var value = input.toLowerCase().trim();
    const accents = <String, String>{
      'á': 'a', 'à': 'a', 'â': 'a', 'ã': 'a', 'ä': 'a',
      'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
      'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
      'ó': 'o', 'ò': 'o', 'ô': 'o', 'õ': 'o', 'ö': 'o',
      'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
      'ç': 'c',
    };
    accents.forEach((from, to) => value = value.replaceAll(from, to));
    return value
        .replaceAll(RegExp(r'[^a-z0-9]+'), ' ')
        .replaceAll(RegExp(r'\s+'), ' ')
        .trim();
  }
}
