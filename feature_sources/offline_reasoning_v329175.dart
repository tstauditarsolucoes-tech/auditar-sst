// Regras locais determinísticas. Sem rede, IA, fotos ou persistência.
class OfflineRule {
  const OfflineRule(this.id, this.title, this.entity, this.fault, this.risk,
      this.consequence, this.action, this.reference, this.question,
      {this.exclude = '', this.severe = false});
  final String id, title, entity, fault, risk, consequence, action, reference, question, exclude;
  final bool severe;
}
class OfflineAssessment {
  const OfflineAssessment(this.rule, this.description, this.equipment, this.segment);
  final OfflineRule rule;
  final String description, equipment, segment;
  String get reason => 'Equipamento/tema e falha identificados no texto. Referência temática: ${rule.reference}.';
  String priority(String exposure) => rule.severe && exposure == 'Sim' ? 'Crítica' : 'Alta';
  String priorityReason(String exposure) => exposure == 'Sim' && rule.severe
    ? 'Exposição atual confirmada a uma condição com potencial de lesão grave. Revisar no local.'
    : 'Triagem inicial pela falha descrita; exposição, probabilidade e severidade precisam de avaliação do técnico.';
}
class OfflineReasoning {
  static String normalize(String value) {
    var s = value.toLowerCase();
    const accents = {'á':'a','à':'a','ã':'a','â':'a','é':'e','ê':'e','í':'i','ó':'o','ô':'o','õ':'o','ú':'u','ü':'u','ç':'c'};
    accents.forEach((a,b) => s=s.replaceAll(a,b));
    const corrections = {'botaoo':'botao','botoera':'botoeira','botoiera':'botoeira','extitor':'extintor','extitorr':'extintor','andaimee':'andaime','andaimeis':'andaimes','adaime':'andaime','protecaoo':'protecao','eletricoo':'eletrico','n':'nao','s':'sem','p':'para','ta':'esta'};
    s=s.replaceAll(RegExp(r'[^a-z0-9;,.!?\s]'), ' ').replaceAll(RegExp(r'\s+'),' ').trim();
    return s.split(' ').map((w)=>corrections[w]??w).join(' ');
  }
  static bool has(String pattern, String text) => RegExp('(?:^|\\b)(?:$pattern)(?:\\b|\$)').hasMatch(text);
  static const _objects = 'extintor|hidrante|saida|iluminacao|botao|botoeira|sensor|betoneira|masseira|cilindro|misturador|maquina|correia|polia|andaime|escada|painel|quadro|fio|cabo|tomada|epi|capacete|oculos|luva|protetor|respirador|mascara|trabalhador|talabarte|cinturao|ancoragem|bota|botina|calcado';
  static List<OfflineAssessment> analyze(String query, {List<String> context = const []}) {
    if (query.length > 3000) return const [];
    final normalized=normalize(query);
    if (has('corrigido|corrigida|regularizado|regularizada|reparado|reparada|resolvido|resolvida', normalized)) return const [];
    final clauses=normalized.split(RegExp('[;.!?]|, |,? mas | e (?=(?:$_objects)\\b)'));
    final out=<OfflineAssessment>[];
    final ctx=normalize(context.join(' '));
    final segment=has('obra|construtora|canteiro',ctx+' '+normalized)?'Obra':has('padaria|panificadora|masseira',ctx+' '+normalized)?'Padaria':has('ceramica|telha',ctx+' '+normalized)?'Cerâmica':has('laticinio|leite',ctx+' '+normalized)?'Laticínio':has('oficina',ctx+' '+normalized)?'Oficina':'Geral';
    for(final rule in rules) {
      for(final clause in clauses) {
        if (explicitSafeOrUncertain(clause)) continue;
        if (!has(rule.entity,clause) || !has(rule.fault,clause)) continue;
        if (rule.exclude.isNotEmpty && has(rule.exclude,normalized)) continue;
        // Histórico de correção não é convertido em uma falha atual.
        if (has('corrigido|corrigida|regularizado|regularizada|reparado|reparada|ja resolvido|ja resolvida',clause)) continue;
        final equipment=RegExp(rule.entity).firstMatch(clause)?.group(0)??rule.title;
        out.add(OfflineAssessment(rule,query.trim(),equipment,segment));break;
      }
    }
    return out;
  }
  static bool getSupportedTopic(String query) => has(_objects,normalize(query));
  static bool explicitSafeOrUncertain(String query) {
    final n=normalize(query);
    return has('desobstruido|desobstruida|sem defeito|sem falha|sem obstrucao|funcionando normalmente|funciona normalmente|corrigido|corrigida|regularizado|regularizada|reparado|reparada|resolvido|resolvida|nao testado|nao verificado|talvez|suspeita|verificar se|nao sei', n)
      || RegExp(r'\bnao (?:esta |estava |foi |se encontra |apresenta |ha |tem )?(?:inoperante|defeito|falha|falhou|obstruid[oa]|bloquead[oa]|expost[oa]|quebrad[oa]|danificad[oa]|desativado|burlado)\b').hasMatch(n);
  }
  static const rules=<OfflineRule>[
    OfflineRule('stop','Parada de emergência inoperante','botao de emergencia|botao emergencia|botoeira de emergencia|parada de emergencia','nao funciona|nao funcionou|nao respondeu|inoperante|defeito|falhou|quebrado','Dificuldade de interromper um movimento perigoso.','Aprisionamento, esmagamento ou outras lesões graves.','Impedir o uso inseguro; encaminhar a falha para manutenção autorizada e testar a função de segurança antes da liberação.','NR-12','A máquina está em uso com essa falha?',exclude:'sem defeito|sem falha|funcionando normalmente|funciona normalmente',severe:true),
    OfflineRule('control','Comando de máquina com falha','botao|botoeira','nao funciona|nao funcionou|nao respondeu|inoperante|defeito|falhou|quebrado','Perda ou resposta inadequada do comando.','Movimento inesperado ou dificuldade de operar com segurança, conforme a função do comando.','Identificar a função do comando e impedir operação insegura até avaliação e correção por responsável competente.','NR-12','A falha compromete uma função de segurança?',exclude:'emergencia'),
    OfflineRule('sensor','Sensor de proteção inoperante','sensor de protecao|sensor da porta|sensor porta|sensor de seguranca|intertravamento|chave de seguranca','nao funciona|nao funcionou|inoperante|burlado|desativado|ponte|defeito','Acesso à zona perigosa sem interrupção segura.','Aprisionamento, esmagamento ou amputação.','Impedir a operação insegura e encaminhar para avaliação da proteção e do intertravamento por responsável competente.','NR-12','Há operação com acesso à zona perigosa?',exclude:'sem defeito|funcionando normalmente',severe:true),
    OfflineRule('guard','Proteção de máquina ausente ou inadequada','maquina|betoneira|masseira|misturador|cilindro|correia|polia|engrenagem|eixo','sem protecao|protecao removida|protecao retirada|protecao quebrada|desprotegido|exposto','Contato com partes móveis e pontos de aprisionamento.','Corte, arraste, esmagamento ou amputação.','Impedir acesso ao perigo e solicitar adequação das proteções conforme avaliação técnica e instruções do fabricante.','NR-12','Há pessoas expostas com o equipamento em movimento?',severe:true),
    OfflineRule('lock','Intervenção sem bloqueio de energias','maquina|betoneira|misturador|masseira|manutencao','sem bloqueio|sem desenergizacao|limpeza em movimento','Partida inesperada ou liberação de energia durante intervenção.','Esmagamento, choque ou lesão grave.','Suspender a intervenção insegura e aplicar procedimento de isolamento e bloqueio de energias por pessoal autorizado.','NR-12 / NR-10, conforme a energia','Há intervenção acontecendo agora?',severe:true),
    OfflineRule('scaffold-base','Base de andaime instável','andaime|andaimes','solo desnivelado|sem nivelamento|base instavel|sapata inadequada|sobre tijolo|sobre bloco|afundando','Perda de estabilidade da estrutura.','Queda de pessoas ou materiais e colapso.','Suspender o uso da estrutura afetada e solicitar avaliação do apoio, nivelamento e montagem conforme projeto e fabricante.','NR-18','O andaime está sendo utilizado?',severe:true),
    OfflineRule('scaffold-guard','Proteção de plataforma ausente','andaime|plataforma','sem guarda corpo|sem rodape|piso incompleto|abertura no piso','Queda de pessoas ou materiais.','Trauma grave e lesões em pessoas próximas.','Restringir o uso da plataforma até adequação do piso e das proteções previstas para o sistema.','NR-18','Há trabalho acontecendo na plataforma?',severe:true),
    OfflineRule('scaffold-access','Acesso ao andaime inadequado','andaime|escada','acesso improvisado|sem acesso seguro|escada solta|escada sem fixacao|subindo pela estrutura','Queda durante o acesso.','Fraturas e trauma grave.','Impedir o acesso improvisado e providenciar acesso seguro compatível com a estrutura e as instruções de montagem.','NR-18','Há trabalhadores utilizando esse acesso?',severe:true),
    OfflineRule('anchor','Conexão de proteção contra queda a verificar','talabarte|cinturao|ancoragem|andaime','preso no proprio andaime|preso ao andaime|sem ponto de ancoragem|sem ancoragem|sem conexao','Possível ineficácia do sistema de proteção contra queda.','Queda para nível inferior e trauma grave.','Suspender a exposição e solicitar avaliação do sistema e da ancoragem previstos no projeto; não presumir que qualquer ponto da estrutura é adequado.','NR-18 / NR-35, conforme atividade','Há exposição atual a queda?',severe:true),
    OfflineRule('electric-exposed','Parte elétrica acessível ou danificada','fio|fiacao|cabo|painel|quadro|tomada|plugue','exposto|desencapado|sem tampa|aberto|quebrada|quebrado|emenda improvisada','Possível contato elétrico, arco ou aquecimento.','Choque, queimadura ou incêndio.','Isolar o acesso à condição perigosa e encaminhar para avaliação e correção por trabalhador autorizado; não tocar nem improvisar reparos.','NR-10','Há partes energizadas acessíveis a pessoas?',exclude:'desenergizado e bloqueado',severe:true),
    OfflineRule('electric-label','Painel elétrico sem identificação','painel|quadro eletrico','sem identificacao|sem sinalizacao|sem placa','Dificuldade de identificar circuitos e riscos.','Intervenção equivocada ou atraso em emergência.','Solicitar identificação dos circuitos e sinalização adequada ao risco, conforme avaliação do responsável.','NR-10','A falta de identificação afeta uma intervenção atual?'),
    OfflineRule('electric-access','Acesso ao painel obstruído','painel|quadro eletrico','obstruido|bloqueado por materiais','Dificuldade de acesso e desligamento seguro.','Atraso na resposta a emergência.','Desobstruir o acesso sem intervir na instalação elétrica e manter a área livre.','NR-10','Há necessidade imediata de acesso ao painel?',exclude:'desobstruido|nao obstruido|nao esta obstruido'),
    OfflineRule('extinguisher-access','Extintor com acesso obstruído','extintor','obstruido|bloqueado|atras de materiais','Atraso no acesso ao equipamento de emergência.','Comprometimento da resposta inicial a incêndio.','Desobstruir o acesso e verificar a disposição do equipamento conforme o projeto e as exigências do Corpo de Bombeiros.','NR-23 e regras estaduais de incêndio','O acesso está impedido neste momento?',exclude:'desobstruido|nao obstruido|nao esta obstruido|sem obstrucao'),
    OfflineRule('extinguisher-sign','Extintor sem sinalização','extintor','sem sinalizacao|sem placa|falta de sinalizacao','Dificuldade de localizar o equipamento.','Atraso na resposta inicial a incêndio.','Regularizar a sinalização conforme o projeto de segurança contra incêndio e as exigências locais.','NR-23 e regras estaduais de incêndio','O equipamento é facilmente localizado pelos trabalhadores?'),
    OfflineRule('extinguisher-condition','Extintor com condição a verificar','extintor','sem pressao|manometro no vermelho|lacre rompido|mangueira danificada','Possível indisponibilidade do equipamento.','Falha no combate inicial ao incêndio.','Encaminhar para avaliação por prestador habilitado e manter a proteção prevista durante eventual substituição.','NR-23 e requisitos técnicos aplicáveis','Há outro equipamento adequado disponível para a área?'),
    OfflineRule('exit','Saída de emergência obstruída','saida de emergencia|rota de fuga','obstruida|bloqueada|trancada','Dificuldade de abandono seguro.','Atraso na evacuação e exposição ao perigo.','Liberar a saída e assegurar condições de abandono conforme o projeto e as exigências locais.','NR-23','Há pessoas utilizando a área afetada?',exclude:'desobstruida|nao obstruida|sem obstrucao',severe:true),
    OfflineRule('emergency-light','Iluminação de emergência inoperante','iluminacao de emergencia|luminaria de emergencia','inoperante|nao funciona|nao funcionou|apagada no teste','Redução da orientação durante falta de iluminação.','Desorientação e quedas na evacuação.','Solicitar manutenção e teste do sistema conforme projeto e exigências locais.','NR-23 e regras estaduais de incêndio','A área depende deste ponto para abandono seguro?',exclude:'funcionando normalmente'),
    OfflineRule('hearing','Proteção auditiva não utilizada','protetor auricular|protetor auditivo|abafador','sem protetor|nao usa|nao utiliza|nao utilizado|sem abafador','Exposição ao ruído sem a proteção individual prevista.','Possíveis danos auditivos conforme nível e duração da exposição.','Confirmar a exposição e o EPI selecionado para a atividade; regularizar o uso, orientar e revisar os controles coletivos.','NR-6 / NR-1','O trabalhador está exposto ao ruído agora?'),
    OfflineRule('respirator','Proteção respiratória não utilizada','respirador|mascara','sem mascara|sem respirador|nao usa|nao utiliza|nao utilizada|nao utilizado','Possível inalação de contaminantes.','Irritação ou agravos respiratórios conforme o agente e a exposição.','Verificar o contaminante e os controles existentes; selecionar e orientar a proteção respiratória adequada à avaliação de risco, sem presumir um modelo único.','NR-6 / NR-1','Há exposição ao contaminante durante a atividade?'),
    OfflineRule('eyes','Proteção ocular não utilizada','oculos|protecao ocular','sem oculos|sem protecao ocular|nao usa|nao utiliza','Possível contato com partículas ou respingos.','Lesão ocular conforme o perigo presente.','Confirmar o risco da atividade e regularizar a proteção ocular selecionada, com orientação e supervisão.','NR-6','A atividade apresenta projeção ou respingos?'),
    OfflineRule('helmet','Capacete não utilizado em condição a avaliar','capacete','sem capacete|nao usa|nao utiliza','Possível impacto na cabeça, se presente na atividade.','Traumatismo conforme a exposição.','Confirmar a necessidade na avaliação de risco da atividade e regularizar o uso do capacete quando indicado.','NR-6','Há risco de impacto ou queda de objetos neste local?'),
    OfflineRule('footwear','Calçado de segurança ausente ou inadequado','bota|botina|calcado','sem bota|sem botina|calcado inadequado|sem calcado de seguranca','Possível impacto, perfuração ou escorregamento.','Lesões nos pés ou queda conforme o risco presente.','Verificar o risco e regularizar calçado compatível com a atividade.','NR-6','O risco exige proteção dos pés nesta atividade?'),
    OfflineRule('gloves','Proteção das mãos incompatível a avaliar','luva|luvas','luva inadequada|luva rasgada|luvas rasgadas|sem luva','Possível exposição das mãos ao perigo da atividade.','Cortes, abrasão ou queimadura conforme a exposição.','Avaliar a atividade antes de indicar luvas; junto a partes rotativas, avaliar o risco de arraste e priorizar proteção da máquina e método seguro.','NR-6 / NR-12, conforme atividade','Há contato potencial com partes rotativas?',severe:false),
  ];
}
