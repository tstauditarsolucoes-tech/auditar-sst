class OfflineFieldRuleResult {
  const OfflineFieldRuleResult({
    required this.nrs,
    required this.priority,
    required this.score,
    required this.actionPlan,
    required this.responsibleSuggestion,
    required this.deadlineSuggestion,
    required this.possibleRecurrence,
    this.category = 'Risco ocupacional',
    this.riskSummary = '',
    this.consequenceSummary = '',
    this.evidenceSuggestion = '',
    this.technicalReason = '',
    this.nrDetails = const <String>[],
    this.suggestedProbability = 3,
    this.suggestedSeverity = 3,
  });

  final List<String> nrs;
  final String priority;
  final int score;
  final String actionPlan;
  final String responsibleSuggestion;
  final String deadlineSuggestion;
  final bool possibleRecurrence;
  final String category;
  final String riskSummary;
  final String consequenceSummary;
  final String evidenceSuggestion;
  final String technicalReason;
  final List<String> nrDetails;
  final int suggestedProbability;
  final int suggestedSeverity;
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
    final profile = _bestProfile(normalized);
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
      actionPlan: _withPriority(profile.action, priority),
      responsibleSuggestion: profile.responsible,
      deadlineSuggestion: suggestDeadline(priority),
      possibleRecurrence: recurring || learnedHistoryMatch,
      category: profile.category,
      riskSummary: profile.risk,
      consequenceSummary: profile.consequence,
      evidenceSuggestion: profile.evidence,
      technicalReason: profile.reason,
      nrDetails: nrs.map(_nrDetail).toList(growable: false),
      suggestedProbability: profile.probability,
      suggestedSeverity: profile.severity,
    );
  }

  static int suggestedProbabilityForText(String text) =>
      _bestProfile(_normalize(text)).probability;

  static int suggestedSeverityForText(String text) =>
      _bestProfile(_normalize(text)).severity;

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

    bool any(List<String> terms) => terms.any(value.contains);
    void addIf(String nr, List<String> terms) {
      if (any(terms)) out.add(nr);
    }

    addIf('NR-01', const [
      'risco', 'perigo', 'nao conform', 'condicao insegura', 'ato inseguro',
      'recorrente', 'plano de acao',
    ]);
    addIf('NR-06', const [
      'epi', 'capacete', 'luva', 'oculos', 'protetor auricular',
      'respirador', 'mascara', 'botina', 'perneira', 'avental',
      'cinto paraquedista',
    ]);
    addIf('NR-10', const [
      'painel eletrico', 'eletric', 'fiacao', 'cabo energ', 'cabo eletrico',
      'aterramento', 'choque', 'tomada', 'plugue', 'quadro eletrico',
    ]);
    addIf('NR-11', const [
      'empilhadeira', 'movimentacao de carga', 'transporte de materiais',
      'armazenamento', 'empilhamento', 'pallet', 'carga suspensa',
    ]);
    addIf('NR-12', const [
      'maquina', 'sensor', 'intertravamento', 'botoeira', 'botao',
      'parada de emergencia', 'protecao de maquina', 'parte movel',
      'zona de perigo', 'prensa', 'esteira', 'betoneira', 'polia',
      'correia', 'engrenagem',
    ]);
    addIf('NR-13', const [
      'caldeira', 'vaso de pressao', 'compressor', 'tubulacao pressurizada',
      'tanque metalico',
    ]);
    addIf('NR-15', const [
      'ruido', 'calor', 'agente quimico', 'poeira', 'poeira mineral',
      'fumaca', 'fumo metalico',
    ]);
    addIf('NR-17', const [
      'ergonom', 'postura', 'levantamento manual', 'peso', 'sobrecarga',
      'repetitiv', 'movimentacao manual',
    ]);
    addIf('NR-18', const [
      'obra', 'construcao', 'andaime', 'escavacao', 'canteiro',
      'abertura no piso', 'guarda corpo',
    ]);
    addIf('NR-20', const [
      'inflamavel', 'combustivel', 'gasolina', 'diesel', 'glp', 'solvente',
    ]);
    addIf('NR-23', const [
      'extintor', 'incendio', 'hidrante', 'rota de fuga', 'saida de emergencia',
    ]);
    addIf('NR-24', const [
      'refeitorio', 'banheiro', 'sanitario', 'vestiario', 'agua potavel',
    ]);
    addIf('NR-26', const [
      'sinalizacao', 'placa', 'rotulagem', 'identificacao',
      'produto quimico', 'recipiente sem identificacao',
    ]);
    addIf('NR-33', const [
      'espaco confinado', 'entrada em tanque', 'entrada em silo',
    ]);
    addIf('NR-35', const [
      'trabalho em altura', 'altura', 'linha de vida', 'ancoragem',
      'cinto paraquedista', 'queda de nivel', 'telhado', 'andaime',
      'guarda corpo',
    ]);

    return out.toList()..sort(_nrSort);
  }

  static String buildActionPlan(String text, String priority) {
    final profile = _bestProfile(_normalize(text));
    return _withPriority(profile.action, priority);
  }

  static String suggestResponsible(String text) =>
      _bestProfile(_normalize(text)).responsible;

  static String suggestDeadline(String priority) {
    switch (priority) {
      case 'Crítica':
        return 'Imediato / antes da continuidade da condição de risco';
      case 'Alta':
        return 'Prioritário — sugerido até 7 dias, conforme risco e viabilidade';
      case 'Média':
        return 'Programar correção — sugerido até 30 dias';
      default:
        return 'Programar melhoria — sugerido até 60 dias';
    }
  }

  static String _withPriority(String action, String priority) {
    if (priority == 'Crítica') {
      return '$action Tratamento imediato recomendado antes da continuidade da condição de risco.';
    }
    if (priority == 'Alta') {
      return '$action Priorizar a correção e acompanhar até a conclusão.';
    }
    return action;
  }

  static String _nrDetail(String nr) {
    const names = <String, String>{
      'NR-01': 'Gerenciamento de riscos ocupacionais',
      'NR-06': 'Equipamento de Proteção Individual',
      'NR-10': 'Segurança em instalações e serviços em eletricidade',
      'NR-11': 'Transporte, movimentação, armazenagem e manuseio de materiais',
      'NR-12': 'Segurança no trabalho em máquinas e equipamentos',
      'NR-13': 'Caldeiras, vasos de pressão, tubulações e tanques metálicos',
      'NR-15': 'Atividades e operações insalubres',
      'NR-17': 'Ergonomia',
      'NR-18': 'Segurança e saúde na indústria da construção',
      'NR-20': 'Inflamáveis e combustíveis',
      'NR-23': 'Proteção contra incêndios',
      'NR-24': 'Condições sanitárias e de conforto',
      'NR-26': 'Sinalização de segurança',
      'NR-33': 'Segurança e saúde em espaços confinados',
      'NR-35': 'Trabalho em altura',
    };
    final label = names[nr];
    return label == null ? nr : '$nr — $label';
  }

  static _RuleProfile _bestProfile(String value) {
    _RuleProfile best = _generic;
    var bestScore = 0;
    for (final profile in _profiles) {
      var score = 0;
      for (final term in profile.terms) {
        if (value.contains(term)) {
          score += term.contains(' ') ? 5 : 2;
        }
      }
      if (score > bestScore) {
        best = profile;
        bestScore = score;
      }
    }
    return best;
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
      'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u', 'ç': 'c',
    };
    accents.forEach((from, to) => value = value.replaceAll(from, to));
    return value
        .replaceAll(RegExp(r'[^a-z0-9]+'), ' ')
        .replaceAll(RegExp(r'\s+'), ' ')
        .trim();
  }

  static const _generic = _RuleProfile(
    category: 'Risco ocupacional',
    terms: <String>[],
    risk: 'Condição com potencial de exposição a perigo ou falha de controle.',
    consequence: 'Incidente, lesão ou agravamento da condição caso o perigo permaneça sem tratamento.',
    action:
        'Corrigir a condição registrada, definir responsável, comprovar a regularização com evidência e verificar a eficácia no acompanhamento.',
    responsible: 'Responsável da área a definir',
    evidence:
        'Registrar foto após a correção e observação objetiva da medida adotada.',
    reason:
        'A regra local não encontrou um tema específico suficiente; o enquadramento deve ser confirmado pelo TST.',
    probability: 3,
    severity: 3,
  );

  static const _profiles = <_RuleProfile>[
    _RuleProfile(
      category: 'Segurança de máquinas — parada de emergência',
      terms: <String>['parada de emergencia', 'botao de emergencia', 'botoeira de emergencia', 'botao', 'botoeira'],
      risk: 'Impossibilidade ou atraso na parada imediata da máquina diante de uma condição perigosa.',
      consequence: 'Agravamento de acidente por continuidade de movimento, aprisionamento, esmagamento, corte ou outro contato perigoso.',
      action: 'Interromper a operação quando a função de parada de emergência estiver inoperante, solicitar correção pela manutenção e testar o dispositivo antes da liberação.',
      responsible: 'Manutenção / responsável técnico da máquina',
      evidence: 'Foto do dispositivo e registro do teste funcional após o reparo.',
      reason: 'Termos associados a comando/parada de emergência e segurança de máquinas foram identificados.',
      probability: 3,
      severity: 5,
    ),
    _RuleProfile(
      category: 'Segurança de máquinas — sensor/intertravamento',
      terms: <String>['sensor', 'intertravamento', 'chave de seguranca', 'micro switch'],
      risk: 'Acesso à zona de perigo sem atuação adequada do sistema de proteção.',
      consequence: 'Aprisionamento, esmagamento, corte ou contato com partes perigosas em movimento.',
      action: 'Suspender o uso quando o dispositivo integrar função de segurança, corrigir o sensor/intertravamento e realizar teste funcional antes da liberação.',
      responsible: 'Manutenção / responsável técnico da máquina',
      evidence: 'Foto do dispositivo e registro do teste funcional após a correção.',
      reason: 'Foram identificados termos associados a sensores e intertravamentos de segurança.',
      probability: 3,
      severity: 5,
    ),
    _RuleProfile(
      category: 'Segurança de máquinas — proteção física',
      terms: <String>['protecao de maquina', 'grade de protecao', 'carter', 'parte movel', 'zona de perigo', 'polia', 'correia', 'engrenagem'],
      risk: 'Contato com partes móveis, pontos de esmagamento, corte, arraste ou aprisionamento.',
      consequence: 'Lesões graves, amputações ou outros traumas por contato com componentes em movimento.',
      action: 'Interromper a condição insegura, reinstalar ou adequar a proteção e somente liberar a máquina após verificação funcional e de acesso à zona de perigo.',
      responsible: 'Manutenção / responsável técnico da máquina',
      evidence: 'Foto da proteção instalada e verificação visual/funcional antes da liberação.',
      reason: 'Foram identificados termos ligados a proteção de partes perigosas de máquinas.',
      probability: 3,
      severity: 5,
    ),
    _RuleProfile(
      category: 'Eletricidade',
      terms: <String>['painel eletrico', 'quadro eletrico', 'fiacao', 'cabo eletrico', 'cabo energ', 'aterramento', 'tomada', 'plugue', 'choque'],
      risk: 'Contato com partes energizadas, falha de isolação, curto-circuito ou energização indevida de partes metálicas.',
      consequence: 'Choque elétrico, queimaduras, incêndio ou acidente grave/fatal.',
      action: 'Isolar a condição quando houver exposição elétrica e encaminhar a regularização a profissional autorizado antes da liberação.',
      responsible: 'Manutenção elétrica / profissional autorizado',
      evidence: 'Foto da correção e confirmação da condição segura pelo responsável autorizado.',
      reason: 'A descrição contém termos associados a instalações ou componentes elétricos.',
      probability: 3,
      severity: 5,
    ),
    _RuleProfile(
      category: 'Proteção contra incêndio',
      terms: <String>['extintor', 'hidrante', 'rota de fuga', 'saida de emergencia', 'incendio'],
      risk: 'Comprometimento do acesso, identificação ou disponibilidade do recurso de emergência.',
      consequence: 'Atraso ou redução da eficiência da resposta inicial em situação de incêndio ou evacuação.',
      action: 'Regularizar imediatamente acesso, sinalização e condição do equipamento ou rota, mantendo o ponto disponível e claramente identificado.',
      responsible: 'Gestão da unidade / responsável da área',
      evidence: 'Foto do ponto regularizado e, quando aplicável, registro de manutenção/inspeção.',
      reason: 'Foram identificados termos relacionados a proteção contra incêndio e resposta a emergência.',
      probability: 3,
      severity: 4,
    ),
    _RuleProfile(
      category: 'Inflamáveis e combustíveis',
      terms: <String>['gasolina', 'diesel', 'combustivel', 'inflamavel', 'glp', 'solvente'],
      risk: 'Vazamento, formação de atmosfera inflamável, contato com fonte de ignição ou armazenamento incompatível.',
      consequence: 'Incêndio, explosão, queimaduras e danos materiais.',
      action: 'Regularizar recipiente, identificação, armazenamento e controle de fontes de ignição, restringindo a condição insegura até a correção.',
      responsible: 'Gestão da área / responsável pelo armazenamento',
      evidence: 'Foto do recipiente/local regularizado e identificação visível do produto.',
      reason: 'Foram identificados termos associados a inflamáveis ou combustíveis.',
      probability: 3,
      severity: 5,
    ),
    _RuleProfile(
      category: 'Trabalho em altura / proteção contra quedas',
      terms: <String>['trabalho em altura', 'linha de vida', 'ancoragem', 'cinto paraquedista', 'guarda corpo', 'telhado', 'queda de nivel'],
      risk: 'Queda de trabalhador para nível inferior por ausência ou falha de proteção coletiva/individual.',
      consequence: 'Traumas graves ou acidente fatal.',
      action: 'Restringir a atividade até a regularização das medidas de proteção contra quedas e liberar somente após verificação das condições seguras.',
      responsible: 'Supervisão da atividade / SST / responsável técnico',
      evidence: 'Foto das proteções regularizadas e registro da liberação da condição de trabalho.',
      reason: 'A descrição indica atividade ou condição com potencial de queda de nível.',
      probability: 3,
      severity: 5,
    ),
    _RuleProfile(
      category: 'Andaimes e plataformas',
      terms: <String>['andaime', 'plataforma de trabalho'],
      risk: 'Queda de trabalhador, queda de materiais ou instabilidade/tombamento da estrutura.',
      consequence: 'Traumas graves, esmagamento ou acidente fatal.',
      action: 'Interromper o uso do andaime inseguro, regularizar estabilidade, acessos, proteções e montagem antes de nova liberação.',
      responsible: 'Responsável da obra / montagem / SST',
      evidence: 'Fotos da base, amarração/ancoragem, acesso e proteções após regularização.',
      reason: 'Foram identificados termos relacionados a andaimes ou plataformas de trabalho.',
      probability: 3,
      severity: 5,
    ),
    _RuleProfile(
      category: 'Escadas e acessos',
      terms: <String>['escada portatil', 'escada fixa', 'escada', 'corrimao'],
      risk: 'Perda de equilíbrio, escorregamento, tombamento ou queda durante acesso e circulação.',
      consequence: 'Contusões, fraturas ou lesões graves.',
      action: 'Retirar de uso acessos inadequados ou restringir a passagem, corrigindo apoio, conservação e proteção antes da liberação.',
      responsible: 'Responsável da área / manutenção',
      evidence: 'Foto do acesso regularizado, incluindo apoio, corrimão ou proteção aplicável.',
      reason: 'A descrição contém termos relacionados a escadas e acessos.',
      probability: 3,
      severity: 4,
    ),
    _RuleProfile(
      category: 'Equipamento de proteção individual',
      terms: <String>['epi', 'capacete', 'luva', 'oculos', 'protetor auricular', 'respirador', 'mascara', 'botina', 'perneira', 'avental'],
      risk: 'Exposição ao perigo existente sem a proteção individual prevista para a atividade ou área.',
      consequence: 'Aumento da possibilidade e da gravidade de lesões ou agravos relacionados à exposição.',
      action: 'Regularizar o EPI adequado, orientar o trabalhador e reforçar a supervisão do uso durante a atividade e circulação em área de risco.',
      responsible: 'Supervisão da área / SST',
      evidence: 'Registro de orientação/entrega quando aplicável e foto da condição regularizada.',
      reason: 'Foram identificados termos de EPI ou proteção individual.',
      probability: 3,
      severity: 4,
    ),
    _RuleProfile(
      category: 'Ruído ocupacional',
      terms: <String>['ruido', 'barulho', 'protetor auricular'],
      risk: 'Exposição a níveis de ruído potencialmente relevantes sem controle suficiente.',
      consequence: 'Danos auditivos, fadiga, dificuldade de comunicação e aumento do risco de acidentes.',
      action: 'Reavaliar controles da fonte/ambiente, reforçar uso de proteção auditiva quando prevista e manter acompanhamento da exposição.',
      responsible: 'Gestão da área / SST',
      evidence: 'Registro da medida adotada, EPI regularizado e avaliação de ruído quando necessária.',
      reason: 'A descrição contém termos associados a exposição ocupacional ao ruído.',
      probability: 3,
      severity: 4,
    ),
    _RuleProfile(
      category: 'Calor ocupacional',
      terms: <String>['calor', 'estresse termico', 'temperatura elevada', 'fonte de calor'],
      risk: 'Sobrecarga térmica durante a execução da atividade.',
      consequence: 'Desidratação, exaustão térmica, redução de atenção e outros agravos relacionados ao calor.',
      action: 'Avaliar a exposição e revisar controles, pausas, hidratação e organização do trabalho conforme o resultado da avaliação ocupacional.',
      responsible: 'Gestão da área / SST',
      evidence: 'Registro dos controles adotados e resultado da avaliação ocupacional quando aplicável.',
      reason: 'Foram identificados termos associados a carga térmica ou fonte de calor.',
      probability: 3,
      severity: 4,
    ),
    _RuleProfile(
      category: 'Poeiras, fumos e particulados',
      terms: <String>['poeira', 'particulado', 'fumaca', 'fumo metalico'],
      risk: 'Inalação de partículas ou contato com olhos e vias respiratórias.',
      consequence: 'Irritação, desconforto respiratório e possíveis agravos relacionados à exposição.',
      action: 'Revisar controles de fonte, ventilação e limpeza e garantir proteção respiratória/ocular quando prevista na avaliação de risco.',
      responsible: 'Gestão da área / SST',
      evidence: 'Foto dos controles implantados e registro da avaliação/medidas de proteção adotadas.',
      reason: 'Foram identificados termos associados a contaminantes particulados no ar.',
      probability: 3,
      severity: 4,
    ),
    _RuleProfile(
      category: 'Produtos químicos',
      terms: <String>['produto quimico', 'quimico', 'recipiente sem identificacao', 'rotulo', 'ficha de seguranca', 'fispq'],
      risk: 'Exposição, uso incorreto ou mistura incompatível por falha de identificação ou controle do produto.',
      consequence: 'Intoxicação, irritação, queimadura química, reação perigosa ou contaminação.',
      action: 'Regularizar identificação, armazenamento, informações de segurança e controles de manuseio antes de manter o produto em uso.',
      responsible: 'Responsável da área / SST / almoxarifado',
      evidence: 'Foto do recipiente identificado e do armazenamento após regularização.',
      reason: 'Foram identificados termos relacionados a produtos químicos e comunicação de perigos.',
      probability: 3,
      severity: 4,
    ),
    _RuleProfile(
      category: 'Ergonomia e movimentação manual',
      terms: <String>['ergonomia', 'postura', 'levantamento manual', 'movimentacao manual', 'sobrecarga', 'repetitiv', 'peso'],
      risk: 'Sobrecarga biomecânica por postura, esforço, repetitividade, alcance ou movimentação manual.',
      consequence: 'Dor, fadiga, distensão e possíveis agravos musculoesqueléticos.',
      action: 'Reorganizar o método, reduzir esforço e alcance, orientar a técnica e avaliar auxílio mecânico, trabalho em dupla ou mudança do processo.',
      responsible: 'Gestão da área / SST',
      evidence: 'Foto do método ajustado e registro da orientação ou medida ergonômica adotada.',
      reason: 'Foram identificados termos associados a ergonomia ou movimentação manual.',
      probability: 3,
      severity: 3,
    ),
    _RuleProfile(
      category: 'Movimentação e armazenamento de materiais',
      terms: <String>['empilhadeira', 'empilhamento', 'armazenamento', 'pallet', 'carga', 'movimentacao de materiais'],
      risk: 'Queda, tombamento, colisão ou atingimento durante movimentação ou armazenamento de materiais.',
      consequence: 'Contusões, esmagamentos, fraturas ou lesões graves.',
      action: 'Reorganizar o armazenamento/movimentação, estabilizar materiais, manter circulação segura e revisar o método e a operação dos equipamentos envolvidos.',
      responsible: 'Logística / almoxarifado / supervisão da área',
      evidence: 'Foto do empilhamento/local regularizado e registro do método adotado.',
      reason: 'A descrição contém termos relacionados a movimentação, empilhamento ou armazenamento.',
      probability: 3,
      severity: 4,
    ),
    _RuleProfile(
      category: 'Organização, circulação e quedas no mesmo nível',
      terms: <String>['organizacao', 'obstrucao', 'corredor', 'passagem', 'piso molhado', 'buraco', 'canaleta', 'tropeco'],
      risk: 'Tropeço, escorregamento, queda no mesmo nível, colisão ou dificuldade de circulação.',
      consequence: 'Contusões, entorses, fraturas ou interferência em rotas e acessos.',
      action: 'Eliminar a condição, organizar a área, proteger aberturas e manter rotas de circulação e acessos livres.',
      responsible: 'Responsável da área / manutenção',
      evidence: 'Foto da área após limpeza, organização, proteção ou reparo.',
      reason: 'Foram identificados termos relacionados a organização, piso ou circulação.',
      probability: 3,
      severity: 3,
    ),
    _RuleProfile(
      category: 'Condições sanitárias e de conforto',
      terms: <String>['refeitorio', 'banheiro', 'sanitario', 'vestiario', 'agua potavel'],
      risk: 'Exposição a condições inadequadas de higiene, conservação ou conforto.',
      consequence: 'Desconforto, contaminação e comprometimento das condições sanitárias do ambiente.',
      action: 'Regularizar higiene, conservação, organização e estrutura do ambiente, mantendo rotina de verificação.',
      responsible: 'Gestão da unidade / serviços gerais',
      evidence: 'Foto do ambiente regularizado e registro da medida adotada.',
      reason: 'Foram identificados termos ligados a instalações sanitárias, refeições ou conforto.',
      probability: 2,
      severity: 3,
    ),
    _RuleProfile(
      category: 'Sinalização e identificação',
      terms: <String>['sinalizacao', 'placa', 'demarcacao', 'identificacao'],
      risk: 'Falha de comunicação do perigo, orientação inadequada ou dificuldade de identificação.',
      consequence: 'Acesso indevido, comportamento inadequado ou atraso na resposta ao risco.',
      action: 'Instalar ou corrigir sinalização e identificação no ponto adequado, garantindo visibilidade e coerência com o perigo existente.',
      responsible: 'Responsável da área / SST',
      evidence: 'Foto da sinalização instalada ou corrigida.',
      reason: 'Foram identificados termos de sinalização, demarcação ou identificação.',
      probability: 2,
      severity: 3,
    ),
    _RuleProfile(
      category: 'Espaço confinado',
      terms: <String>['espaco confinado', 'entrada em tanque', 'entrada em silo'],
      risk: 'Entrada não autorizada e exposição a atmosfera perigosa, deficiência/enriquecimento de oxigênio ou outros perigos do espaço.',
      consequence: 'Intoxicação, asfixia, queda, aprisionamento ou acidente fatal.',
      action: 'Restringir o acesso e verificar caracterização, autorização, avaliação atmosférica, supervisão e controles aplicáveis antes de qualquer entrada.',
      responsible: 'Responsável técnico / supervisor de entrada / SST',
      evidence: 'Registro da identificação do espaço, controle de acesso e documentação aplicável antes da entrada.',
      reason: 'A descrição indica possível situação de espaço confinado.',
      probability: 3,
      severity: 5,
    ),
    _RuleProfile(
      category: 'Equipamentos pressurizados',
      terms: <String>['caldeira', 'vaso de pressao', 'compressor', 'tubulacao pressurizada', 'tanque metalico'],
      risk: 'Falha de integridade, operação inadequada ou perda de controle de equipamento pressurizado.',
      consequence: 'Ruptura, projeção de partes, queimaduras ou acidente grave.',
      action: 'Encaminhar para verificação do responsável técnico, conferindo identificação, integridade, inspeções e controles aplicáveis antes da continuidade insegura.',
      responsible: 'Responsável técnico / manutenção',
      evidence: 'Registro da inspeção/regularização e foto da identificação ou condição corrigida.',
      reason: 'Foram identificados termos relacionados a equipamentos ou sistemas pressurizados.',
      probability: 2,
      severity: 5,
    ),
  ];
}

class _RuleProfile {
  const _RuleProfile({
    required this.category,
    required this.terms,
    required this.risk,
    required this.consequence,
    required this.action,
    required this.responsible,
    required this.evidence,
    required this.reason,
    required this.probability,
    required this.severity,
  });

  final String category;
  final List<String> terms;
  final String risk;
  final String consequence;
  final String action;
  final String responsible;
  final String evidence;
  final String reason;
  final int probability;
  final int severity;
}
