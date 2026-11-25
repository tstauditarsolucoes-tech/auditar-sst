import 'dart:convert';

/// Modelos educacionais; sugestões não demonstram controles implantados.
class SstActivityRiskHint {
  const SstActivityRiskHint(this.step, this.hazard, this.consequence,
      this.controlToVerify);
  final String step, hazard, consequence, controlToVerify;
}

class SstActivityTemplate {
  const SstActivityTemplate({
    required this.code, required this.title, required this.defaultActivity,
    required this.docs, required this.hints, required this.questions,
  });
  final String code, title, defaultActivity;
  final List<String> docs;
  final List<SstActivityRiskHint> hints;
  final List<String> questions;
}

class SstActivityTemplates {
  const SstActivityTemplates._();
  static const values = <SstActivityTemplate>[
    SstActivityTemplate(
      code: 'altura', title: 'Trabalho em altura',
      defaultActivity: 'Atividade em altura',
      docs: ['APR', 'AR', 'PT (quando aplicável)'],
      hints: [
        SstActivityRiskHint('Preparação e acesso',
          'Queda de altura / acesso inseguro', 'Queda com lesão grave',
          'Conferir proteções coletivas e sistema de acesso conforme AR'),
        SstActivityRiskHint('Execução da tarefa',
          'Queda de materiais ou ferramentas', 'Atingimento de pessoas',
          'Verificar isolamento inferior e retenção de ferramentas'),
      ],
      questions: [
        'A AR específica e o procedimento aplicável foram verificados?',
        'As proteções coletivas, ancoragens e sistemas de acesso foram conferidos?',
        'Existe plano de resgate e equipe com meios adequados?',
        'A PT é exigida para esta atividade conforme NR-35 e procedimento?',
      ],
    ),
    SstActivityTemplate(
      code: 'confinado', title: 'Entrada em espaço confinado',
      defaultActivity: 'Entrada e atividade em espaço confinado',
      docs: ['APR', 'AR', 'PET NR-33 obrigatória'],
      hints: [
        SstActivityRiskHint('Planejamento da entrada',
          'Atmosfera perigosa e deficiência/enriquecimento de O₂',
          'Asfixia, intoxicação, incêndio ou explosão',
          'Verificar avaliação de riscos, controle atmosférico e monitoramento'),
        SstActivityRiskHint('Entrada e permanência',
          'Dificuldade de comunicação e resgate',
          'Atraso na resposta a emergências',
          'Verificar vigia, supervisor, comunicação e recursos de resgate'),
      ],
      questions: [
        'O local atende à definição de espaço confinado da NR-33?',
        'A avaliação atmosférica inicial foi feita de fora, com equipamento adequado?',
        'Há monitoramento contínuo durante a entrada e plano de resgate?',
        'PET efetivamente emitida e assinada, com acesso permanente pelo vigia?',
      ],
    ),
    SstActivityTemplate(
      code: 'maquinas', title: 'Manutenção de máquinas',
      defaultActivity: 'Inspeção ou manutenção de máquina',
      docs: ['APR', 'AR', 'PT (quando exigida)'],
      hints: [
        SstActivityRiskHint('Preparação',
          'Energias perigosas e partida inesperada',
          'Aprisionamento, choque ou esmagamento',
          'Conferir desenergização, bloqueio, sinalização e controle de acesso'),
        SstActivityRiskHint('Intervenção',
          'Exposição a componentes móveis e ferramentas',
          'Corte, projeção e contato mecânico',
          'Verificar proteções e método de intervenção segura'),
      ],
      questions: [
        'Fontes de energia e estado seguro foram identificados?',
        'Procedimentos de bloqueio e pessoal autorizado foram conferidos?',
        'Proteções e comandos foram avaliados conforme NR-12?',
      ],
    ),
    SstActivityTemplate(
      code: 'soldagem', title: 'Soldagem ou corte',
      defaultActivity: 'Soldagem ou corte de material',
      docs: ['APR', 'AR', 'PT (quando exigida)'],
      hints: [
        SstActivityRiskHint('Preparação do local',
          'Materiais combustíveis ou atmosfera perigosa',
          'Incêndio ou explosão',
          'Verificar afastamento de combustíveis, controle de ignição e prevenção'),
        SstActivityRiskHint('Execução',
          'Radiação, fumos e partículas quentes',
          'Queimaduras e exposição respiratória',
          'Verificar ventilação, proteção facial/ocular e proteção coletiva'),
      ],
      questions: [
        'Há materiais inflamáveis, gases ou poeiras próximos?',
        'As medidas de combate a incêndio e ventilação foram conferidas?',
        'O local é espaço confinado? Nesse caso, também requer PET NR-33.',
      ],
    ),
    SstActivityTemplate(
      code: 'escavacao', title: 'Escavação ou vala',
      defaultActivity: 'Escavação e serviço próximo a vala',
      docs: ['APR', 'AR', 'PT (quando exigida)'],
      hints: [
        SstActivityRiskHint('Preparação',
          'Instabilidade e soterramento',
          'Esmagamento ou asfixia traumática',
          'Verificar avaliação do solo, proteção coletiva e acesso seguro'),
        SstActivityRiskHint('Trabalho próximo a máquinas',
          'Atropelamento e contato com equipamento',
          'Lesão grave por máquina em movimento',
          'Conferir separação de pessoas/máquinas e sinalização'),
      ],
      questions: [
        'Há análise de estabilidade, contenção e interferências enterradas?',
        'A circulação de máquinas e o acesso à vala foram controlados?',
      ],
    ),
    SstActivityTemplate(
      code: 'eletrica', title: 'Atividade elétrica',
      defaultActivity: 'Serviço em instalação elétrica',
      docs: ['APR', 'AR', 'PT (quando exigida)'],
      hints: [
        SstActivityRiskHint('Preparação',
          'Contato elétrico e energização inesperada',
          'Choque, arco elétrico e queimaduras',
          'Verificar autorização, procedimentos, seccionamento e bloqueio'),
      ],
      questions: [
        'As pessoas possuem autorização e capacitação pertinentes à NR-10?',
        'O procedimento e as medidas de proteção foram conferidos?',
      ],
    ),
    SstActivityTemplate(
      code: 'forno', title: 'Inspeção de forno ou equipamento quente',
      defaultActivity: 'Inspeção em equipamento ou ambiente quente',
      docs: ['APR', 'AR', 'PT (quando exigida)', 'PET se espaço confinado'],
      hints: [
        SstActivityRiskHint('Planejamento de acesso',
          'Calor, superfícies quentes e energia residual',
          'Queimaduras e estresse térmico',
          'Verificar isolamento de fontes de energia e avaliação do calor'),
        SstActivityRiskHint('Entrada e saída',
          'Dificuldade de retirada e emergência',
          'Atraso no resgate e agravamento de lesões',
          'Conferir acesso, comunicação, tempo de exposição e resgate'),
      ],
      questions: [
        'A temperatura e as condições reais permitem acesso seguro?',
        'O local também se caracteriza como espaço confinado?',
        'Há medidas de resgate adequadas à configuração do equipamento?',
      ],
    ),
  ];

  static SstActivityTemplate? find(String code) {
    for (final item in values) {
      if (item.code == code) return item;
    }
    return null;
  }
}

class SstActivityPlan {
  const SstActivityPlan({
    required this.userId, required this.companyId,
    required this.templateCode, required this.activity,
    required this.sector, required this.updatedAt,
  });
  final String userId, companyId, templateCode, activity, sector, updatedAt;

  bool get valid => SstActivityTemplates.find(templateCode) != null &&
      activity.trim().isNotEmpty && sector.trim().isNotEmpty &&
      activity.length <= 220 && sector.length <= 220;

  SstActivityTemplate get template =>
      SstActivityTemplates.find(templateCode)!;

  Map<String, dynamic> toJson() => {
    'version': 1, 'userId': userId, 'companyId': companyId,
    'templateCode': templateCode, 'activity': activity,
    'sector': sector, 'updatedAt': updatedAt,
  };

  factory SstActivityPlan.fromJson(Map<String, dynamic> json, {
    required String expectedUser, required String expectedCompany,
  }) {
    if (json['version'] != 1 || json['userId'] != expectedUser ||
        json['companyId'] != expectedCompany) {
      throw const FormatException('Plano fora deste acesso');
    }
    final plan = SstActivityPlan(
      userId: expectedUser,
      companyId: expectedCompany,
      templateCode: (json['templateCode'] ?? '').toString(),
      activity: (json['activity'] ?? '').toString(),
      sector: (json['sector'] ?? '').toString(),
      updatedAt: (json['updatedAt'] ?? '').toString(),
    );
    if (!plan.valid) throw const FormatException('Plano de atividade inválido');
    return plan;
  }
}

class SstActivityPlanStore {
  const SstActivityPlanStore({required this.read, required this.write});
  final Future<String> Function(String) read;
  final Future<void> Function(String, String) write;

  static String key(String user, String company) =>
      'sst_activity_plan_v1_' + Uri.encodeComponent(user) + '_' +
      Uri.encodeComponent(company);

  Future<SstActivityPlan?> load(String user, String company) async {
    final raw = await read(key(user, company));
    if (raw.trim().isEmpty) return null;
    final json = jsonDecode(raw);
    if (json is! Map) throw const FormatException('Plano inválido');
    return SstActivityPlan.fromJson(Map<String, dynamic>.from(json),
      expectedUser: user, expectedCompany: company);
  }

  Future<void> save(SstActivityPlan plan) async {
    if (!plan.valid) throw StateError('Informe atividade e local.');
    await write(key(plan.userId, plan.companyId), jsonEncode(plan.toJson()));
  }
}
