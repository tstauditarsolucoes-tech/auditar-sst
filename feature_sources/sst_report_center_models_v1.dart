/// Central única de relatórios SST: modelos orientativos para uso em campo.
/// NRs são referências temáticas, não avaliação jurídica automatizada.
enum SstFieldReportKind { nr12, nr18, nr10, nr35, incident, monthly }
extension SstFieldReportKindLabel on SstFieldReportKind {
  String get code => name;
}

class SstFieldQuestion {
  const SstFieldQuestion(this.id,this.group,this.title,this.prompt);
  final String id,group,title,prompt;
}

class SstFieldTemplate {
  const SstFieldTemplate({
    required this.kind,required this.title,required this.subtitle,
    required this.reference,required this.questions,
  });
  final SstFieldReportKind kind;
  final String title,subtitle,reference;
  final List<SstFieldQuestion> questions;
}

class SstFieldTemplates {
  static const models=<SstFieldTemplate>[
    SstFieldTemplate(
      kind:SstFieldReportKind.nr12,
      title:"Máquinas e equipamentos",
      subtitle:"Proteções, comandos, energia e acesso às zonas perigosas.",
      reference:"NR-12",
      questions:<SstFieldQuestion>[
        SstFieldQuestion("nr12-01","Identificação","Equipamento e localização","Identificar máquina, setor, função e componentes inspecionados."),
        SstFieldQuestion("nr12-02","Proteções","Partes móveis e transmissões","Observar correias, engrenagens, eixos, roletes e acesso à zona perigosa."),
        SstFieldQuestion("nr12-03","Proteções","Proteções fixas e móveis","Verificar integridade, fixação e ausência de retirada indevida de proteções."),
        SstFieldQuestion("nr12-04","Comandos","Parada de emergência","Observar identificação, acessibilidade e evidências de condição do comando; registrar teste apenas se efetivamente realizado."),
        SstFieldQuestion("nr12-05","Comandos","Intertravamentos e sensores","Registrar situação de intertravamentos, sensores e possibilidade de burla observada."),
        SstFieldQuestion("nr12-06","Operação","Partida inesperada e rearme","Verificar indícios de acionamento involuntário ou retorno automático perigoso."),
        SstFieldQuestion("nr12-07","Manutenção","Isolamento e bloqueio de energias","Conferir procedimento, possibilidade de bloqueio e registros disponíveis, sem executar intervenção insegura."),
        SstFieldQuestion("nr12-08","Operação","Alimentação, retirada e limpeza","Observar aproximação das mãos, utensílios, acesso e formas de limpeza da máquina."),
        SstFieldQuestion("nr12-09","Sinalização","Identificação e instruções","Verificar avisos, identificação e instruções acessíveis à operação."),
        SstFieldQuestion("nr12-10","Ações","Conservação e providências","Registrar falhas constatadas e controles recomendados sem declarar conformidade automática."),
      ],
    ),
    SstFieldTemplate(
      kind:SstFieldReportKind.nr18,
      title:"Obras e canteiros",
      subtitle:"Andaimes, aberturas, escadas, organização e proteções coletivas.",
      reference:"NR-18",
      questions:<SstFieldQuestion>[
        SstFieldQuestion("nr18-01","Documentos","Planejamento preventivo da obra","Conferir existência e disponibilidade dos documentos aplicáveis à etapa e frente de trabalho."),
        SstFieldQuestion("nr18-02","Áreas de apoio","Instalações sanitárias e água","Verificar condições de acesso, conservação e disponibilidade dos recursos de vivência."),
        SstFieldQuestion("nr18-03","Proteção coletiva","Bordas, aberturas e vãos","Observar presença, continuidade e integridade de guarda-corpos, fechamentos e isolamento."),
        SstFieldQuestion("nr18-04","Acessos","Escadas, rampas e passarelas","Verificar estabilidade, condições de circulação, proteção e apoio."),
        SstFieldQuestion("nr18-05","Andaimes","Base, sapatas e estabilidade","Registrar apoio, nivelamento, estabilidade e evidências da montagem conforme tipo de andaime."),
        SstFieldQuestion("nr18-06","Andaimes","Piso, diagonais e proteção lateral","Conferir piso, acesso, travamentos e proteções, registrando o que foi efetivamente observado."),
        SstFieldQuestion("nr18-07","Escavações","Escavações e bordas","Observar isolamento, acesso, condições visíveis e medidas de prevenção relacionadas ao solo."),
        SstFieldQuestion("nr18-08","Instalações","Quadros e ligações temporárias","Inspeção visual de quadros, cabos, proteção e acesso a componentes elétricos."),
        SstFieldQuestion("nr18-09","Equipamentos","Betoneiras, serras e ferramentas","Registrar proteção, estado visual, instalação e uso adequado de equipamentos presentes."),
        SstFieldQuestion("nr18-10","Organização","Limpeza e circulação","Verificar entulho, armazenagem, bloqueios de passagem e sinalização das frentes."),
      ],
    ),
    SstFieldTemplate(
      kind:SstFieldReportKind.nr10,
      title:"Inspeção visual elétrica",
      subtitle:"Quadros, cabos e proteções, sem substituir ensaio ou laudo.",
      reference:"NR-10",
      questions:<SstFieldQuestion>[
        SstFieldQuestion("nr10-01","Documentação","Responsabilidade e documentos elétricos","Conferir disponibilidade dos registros, projeto e informações aplicáveis; não afirmar existência sem consulta."),
        SstFieldQuestion("nr10-02","Distribuição","Quadro elétrico e fechamento","Observar integridade das portas, tampas, identificação e acessibilidade não autorizada."),
        SstFieldQuestion("nr10-03","Distribuição","Proteção contra contato elétrico","Registrar apenas condições visualmente verificáveis, sem expor o inspetor à energia."),
        SstFieldQuestion("nr10-04","Condutores","Cabos e extensões","Observar emendas, isolamento, roteamento, conexões e danos aparentes."),
        SstFieldQuestion("nr10-05","Equipamentos","Condições visuais de equipamentos","Verificar plugues, carcaças, alimentação e indícios de improvisação."),
        SstFieldQuestion("nr10-06","Proteções","Dispositivos de proteção","Conferir identificação e documentação de proteções; não declarar testes que não ocorreram."),
        SstFieldQuestion("nr10-07","Aterramento","Informações sobre aterramento","Registrar evidências documentais e conexões visuais; medição somente em procedimento próprio."),
        SstFieldQuestion("nr10-08","Instalações temporárias","Ligaçōes de obra","Conferir quadros temporários, uso de dispositivos e proteção de circuitos."),
        SstFieldQuestion("nr10-09","Gestão","Sinalização e acesso controlado","Observar identificação, restrição de acesso e comunicação de riscos."),
        SstFieldQuestion("nr10-10","Conclusão","Providências e necessidade de avaliação elétrica","Indicar encaminhamento a profissional autorizado quando houver indício de falha."),
      ],
    ),
    SstFieldTemplate(
      kind:SstFieldReportKind.nr35,
      title:"Trabalho em altura",
      subtitle:"Planejamento, acesso, ancoragem e prevenção de quedas.",
      reference:"NR-35",
      questions:<SstFieldQuestion>[
        SstFieldQuestion("nr35-01","Planejamento","Análise de risco da atividade","Conferir planejamento, condições do trabalho e medidas de prevenção aplicáveis."),
        SstFieldQuestion("nr35-02","Planejamento","Autorização e capacitação","Consultar evidências disponíveis de autorização, treinamento e aptidão exigíveis."),
        SstFieldQuestion("nr35-03","Acesso","Escadas e meios de acesso","Observar estabilidade, integridade, adequação e condições de circulação."),
        SstFieldQuestion("nr35-04","Proteção coletiva","Guarda-corpos e proteções","Verificar proteções coletivas nas bordas, aberturas e áreas de circulação."),
        SstFieldQuestion("nr35-05","Proteção individual","Cinturão e conexões","Registrar conservação, adequação e presença de dispositivos previstos, sem afirmar eficácia sem avaliação."),
        SstFieldQuestion("nr35-06","Ancoragem","Sistema de ancoragem","Conferir identificação e evidências disponíveis de adequação/inspeção, sem emitir laudo de ancoragem."),
        SstFieldQuestion("nr35-07","Condições","Clima, interferências e materiais","Verificar condições ambientais e isolamento de pessoas abaixo da frente de trabalho."),
        SstFieldQuestion("nr35-08","Emergência","Resgate e resposta a emergências","Conferir planejamento de resposta e recursos previstos para ocorrência de queda."),
        SstFieldQuestion("nr35-09","Gestão","Inspeções, retirada de uso e providências","Registrar achados concretos e encaminhamento sem liberar atividade automaticamente."),
      ],
    ),
    SstFieldTemplate(
      kind:SstFieldReportKind.incident,
      title:"Investigação de acidente/incidente",
      subtitle:"Fatos, fontes, fatores contribuintes e medidas preventivas.",
      reference:"NR-01 (referência temática)",
      questions:<SstFieldQuestion>[
        SstFieldQuestion("incident-01","Identificação","Local, data e atividade no momento","Registrar dados confirmados de local, data, atividade e condição operacional."),
        SstFieldQuestion("incident-02","Cronologia","Sequência factual do evento","Descrever o que ocorreu em ordem, distinguindo relato de fato verificado."),
        SstFieldQuestion("incident-03","Evidências","Fontes documentais e fotografias","Relacionar registros existentes, imagens e informações obtidas; não inventar depoimentos."),
        SstFieldQuestion("incident-04","Condições","Condições do ambiente ou equipamento","Descrever condições efetivamente observadas no local ou nos registros."),
        SstFieldQuestion("incident-05","Organização","Procedimento e orientação disponíveis","Conferir documentos, instruções e recursos efetivamente disponibilizados."),
        SstFieldQuestion("incident-06","Medidas imediatas","Providências adotadas após o evento","Registrar ações já executadas com fonte e data, sem presumir execução."),
        SstFieldQuestion("incident-07","Fatores","Hipóteses e fatores contribuintes","Separar hipóteses de fatores apurados; evitar atribuição automática de culpa."),
        SstFieldQuestion("incident-08","Prevenção","Medidas preventivas propostas","Indicar ação, responsável proposto e evidências necessárias para acompanhamento."),
        SstFieldQuestion("incident-09","Acompanhamento","Status das medidas e evidências","Conferir retorno, registros e necessidade de validação posterior."),
      ],
    ),
  ];
  static SstFieldTemplate of(SstFieldReportKind kind) =>
      models.firstWhere((model)=>model.kind==kind);
}

enum SstFieldStatus { notChecked, conforming, nonConforming, notApplicable, documented }

extension SstFieldStatusLabel on SstFieldStatus {
  String label({bool investigation=false}) {
    if(investigation) {
      switch(this) {
        case SstFieldStatus.notChecked:return 'Não apurado';
        case SstFieldStatus.documented:return 'Apurado/registrado';
        case SstFieldStatus.notApplicable:return 'Não se aplica';
        case SstFieldStatus.conforming:return 'Apurado/registrado';
        case SstFieldStatus.nonConforming:return 'Apurado/registrado';
      }
    }
    switch(this) {
      case SstFieldStatus.notChecked:return 'Não verificado';
      case SstFieldStatus.conforming:return 'Conforme';
      case SstFieldStatus.nonConforming:return 'Não conforme';
      case SstFieldStatus.notApplicable:return 'Não se aplica';
      case SstFieldStatus.documented:return 'Informação registrada';
    }
  }
}

class SstFieldAnswer {
  const SstFieldAnswer({
    this.status=SstFieldStatus.notChecked,
    this.observation='',this.recommendation='',
    this.photoPaths=const <String>[],
  });
  final SstFieldStatus status;
  final String observation,recommendation;
  final List<String> photoPaths;
  bool get isReviewed=>status!=SstFieldStatus.notChecked;
  Map<String,dynamic> toJson()=>{
    'status':status.name,'observation':observation,
    'recommendation':recommendation,'photoPaths':photoPaths,
  };
  factory SstFieldAnswer.fromJson(Map<dynamic,dynamic> map){
    final raw=(map['status']??'').toString();
    final status=SstFieldStatus.values.where((v)=>v.name==raw)
      .firstOrNull??SstFieldStatus.notChecked;
    final photo=map['photoPaths'];
    return SstFieldAnswer(
      status:status,
      observation:(map['observation']??'').toString().substring(
        0,((map['observation']??'').toString().length).clamp(0,1800)),
      recommendation:(map['recommendation']??'').toString().substring(
        0,((map['recommendation']??'').toString().length).clamp(0,1200)),
      photoPaths:photo is List?
        photo.whereType<String>().take(2).toList(growable:false):const [],
    );
  }
  SstFieldAnswer copyWith({
    SstFieldStatus? status,String? observation,
    String? recommendation,List<String>? photoPaths,
  })=>SstFieldAnswer(
    status:status??this.status,
    observation:observation??this.observation,
    recommendation:recommendation??this.recommendation,
    photoPaths:photoPaths??this.photoPaths,
  );
}

class SstFieldDraft {
  const SstFieldDraft({
    required this.kind,required this.companyId,
    this.location='',this.asset='',this.technician='',
    this.date='',this.eventNarrative='',this.eventTime='',
    this.reviewedAt='',this.signaturePath='',
    this.answers=const {},
  });
  final SstFieldReportKind kind;
  final String companyId,location,asset,technician,date,eventNarrative,
      eventTime,reviewedAt,signaturePath;
  final Map<String,SstFieldAnswer> answers;
  SstFieldAnswer answer(String id)=>answers[id]??const SstFieldAnswer();
  int get reviewed=>SstFieldTemplates.of(kind).questions
      .where((q)=>answer(q.id).isReviewed).length;
  int get nonConformities=>SstFieldTemplates.of(kind).questions
      .where((q)=>answer(q.id).status==SstFieldStatus.nonConforming).length;
  bool get hasEnoughForPdf {
    if(kind==SstFieldReportKind.monthly)return false;
    if(technician.trim().isEmpty||date.trim().isEmpty)return false;
    if(kind==SstFieldReportKind.incident &&
       (eventNarrative.trim().length<20||eventTime.trim().isEmpty))return false;
    if(reviewed==0)return false;
    for(final q in SstFieldTemplates.of(kind).questions){
      final a=answer(q.id);
      if(a.status==SstFieldStatus.nonConforming &&
         a.observation.trim().length<8)return false;
      if(kind==SstFieldReportKind.incident &&
         a.status==SstFieldStatus.documented &&
         a.observation.trim().length<8)return false;
    }
    return true;
  }
  bool get isPartial=>reviewed<SstFieldTemplates.of(kind).questions.length;
  SstFieldDraft copyWith({
    String? location,String? asset,String? technician,String? date,
    String? eventNarrative,String? eventTime,String? reviewedAt,
    String? signaturePath,Map<String,SstFieldAnswer>? answers,
  })=>SstFieldDraft(
    kind:kind,companyId:companyId,
    location:location??this.location,asset:asset??this.asset,
    technician:technician??this.technician,date:date??this.date,
    eventNarrative:eventNarrative??this.eventNarrative,
    eventTime:eventTime??this.eventTime,
    reviewedAt:reviewedAt??this.reviewedAt,
    signaturePath:signaturePath??this.signaturePath,
    answers:answers??this.answers,
  );
  SstFieldDraft update(String id,SstFieldAnswer value){
    final next=Map<String,SstFieldAnswer>.of(answers);
    next[id]=value;
    return copyWith(answers:next,reviewedAt:DateTime.now().toIso8601String());
  }
  Map<String,dynamic> toJson()=>{
    'version':1,'kind':kind.name,'companyId':companyId,
    'location':location,'asset':asset,'technician':technician,
    'date':date,'eventNarrative':eventNarrative,
    'eventTime':eventTime,'reviewedAt':reviewedAt,
    'signaturePath':signaturePath,
    'answers':{for(final item in answers.entries)item.key:item.value.toJson()},
  };
  factory SstFieldDraft.fromJson(Map<String,dynamic> map,{
    required SstFieldReportKind expectedKind,
    required String expectedCompanyId,
  }){
    if(map['version']!=1 ||
       map['kind']!=expectedKind.name ||
       map['companyId']!=expectedCompanyId) {
      throw const FormatException('Rascunho pertence a outra empresa ou tipo.');
    }
    final allowed=SstFieldTemplates.of(expectedKind)
        .questions.map((q)=>q.id).toSet();
    final saved=<String,SstFieldAnswer>{};
    final input=map['answers'];
    if(input is Map){
      for(final e in input.entries){
        if(allowed.contains(e.key)&&e.value is Map) {
          saved[e.key.toString()]=SstFieldAnswer.fromJson(e.value as Map);
        }
      }
    }
    String get(String key,int max) {
      final str=(map[key]??'').toString();
      return str.length<=max?str:str.substring(0,max);
    }
    return SstFieldDraft(
      kind:expectedKind,companyId:expectedCompanyId,
      location:get('location',200),asset:get('asset',200),
      technician:get('technician',140),date:get('date',40),
      eventNarrative:get('eventNarrative',2400),
      eventTime:get('eventTime',50),reviewedAt:get('reviewedAt',60),
      signaturePath:get('signaturePath',400),
      answers:saved,
    );
  }
}
