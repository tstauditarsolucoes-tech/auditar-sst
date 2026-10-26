import 'dart:async';
import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../brand.dart';
import '../services/tutorial_service.dart';

class TutorialContent {
  final String title;
  final String description;
  final List<String> tips;
  final IconData icon;
  final bool welcome;

  const TutorialContent({
    required this.title,
    required this.description,
    required this.tips,
    required this.icon,
    this.welcome = false,
  });
}

class TutorialCatalog {
  TutorialCatalog._();

  static const Map<String, TutorialContent> items = {
    'home': TutorialContent(
      title: 'Bem-vindo ao Auditar SST',
      description:
          'As dicas orientam cada etapa. Abra Guia de uso na tela inicial para consultar qualquer assunto quando precisar.',
      tips: [
        'Iniciar visita: selecione empresa/obra e escolha Ronda, Vistoria ou NC.',
        'Continuar rascunho: retome o serviço; Pendências: comece pelo mais urgente.',
        'Relatórios: confira o PDF antes de entregar; a opção Novidades explica recursos recentes.',
      ],
      icon: Icons.waving_hand_rounded,
      welcome: true,
    ),
    'companies': TutorialContent(
      title: 'Empresas',
      description:
          'Aqui ficam as empresas atendidas e os dados usados nas vistorias, relatórios e controles.',
      tips: [
        'Pesquise empresa, obra ou grupo e confirme o contexto antes de trabalhar.',
        'Use recentes/favoritos quando a versão oferecer essas opções.',
        'Mantenha registros separados por empresa e respeite as permissões da conta.',
      ],
      icon: Icons.business_outlined,
    ),
    'company_detail': TutorialContent(
      title: 'Área da empresa',
      description:
          'Esta tela reúne tudo o que está acontecendo nesta empresa em um só lugar.',
      tips: [
        'Consulte vistorias, NCs, ações e relatórios vinculados à empresa.',
        'Confira a Linha do Tempo quando o atalho estiver disponível na sua versão.',
        'O histórico da empresa é diferente das mensagens de tratativa do cliente.',
      ],
      icon: Icons.domain_outlined,
    ),
    'field_quick': TutorialContent(
      title: 'Vistoria rápida',
      description:
          'Use para registrar vários problemas durante uma ronda sem precisar montar uma vistoria completa antes.',
      tips: [
        'Selecione empresa/obra, confira setor e entre em Ronda, Vistoria ou NC.',
        'Registre situação, foto, prioridade e recomendação técnica; salve.',
        'Reabra para conferir o registro e use a Linha do Tempo se estiver disponível.',
      ],
      icon: Icons.flash_on_rounded,
    ),
    'history': TutorialContent(
      title: 'Vistorias',
      description:
          'Aqui você encontra vistorias em andamento e já finalizadas.',
      tips: [
        'Retome uma vistoria em rascunho sem trocar o contexto da empresa.',
        'Revise texto, fotos e recomendações antes de concluir.',
        'Gere o PDF, abra a prévia e teste compartilhamento com contato de teste.',
      ],
      icon: Icons.fact_check_outlined,
    ),
    'non_conformities': TutorialContent(
      title: 'Problemas encontrados',
      description:
          'Esta área concentra as não conformidades registradas nas inspeções.',
      tips: [
        'Priorize NCs críticas e vencidas e abra o detalhe da empresa correta.',
        'Confira fotos, recomendações, prazo, status, histórico e código oficial.',
        'Títulos amigáveis editáveis ainda exigem integração e homologação; preserve o ID.',
      ],
      icon: Icons.warning_amber_rounded,
    ),
    'action_plan': TutorialContent(
      title: 'Planos de ação',
      description:
          'Aqui você acompanha quem ficou responsável por cada correção e qual é o prazo.',
      tips: [
        'Confira responsável e prazo para cada correção.',
        'Cliente pode informar a solução em tratativas habilitadas, sem encerrar a NC sozinho.',
        'Confirme ou rejeite tecnicamente a evidência, registrando justificativa curta.',
      ],
      icon: Icons.assignment_turned_in_outlined,
    ),
    'workers': TutorialContent(
      title: 'Trabalhadores',
      description:
          'Cadastre ou importe os trabalhadores para usar nos controles de SST.',
      tips: [
        'Informe nome, função e setor.',
        'Use a importação para cadastrar listas maiores com mais rapidez.',
        'Os dados ajudam nos treinamentos e demais controles por função.',
      ],
      icon: Icons.groups_rounded,
    ),
    'trainings': TutorialContent(
      title: 'Treinamentos',
      description:
          'Veja quais treinamentos estão em dia e quais precisam de atenção.',
      tips: [
        'Consulte pendências por trabalhador, função ou NR.',
        'Registre treinamentos realizados e suas datas.',
        'Use os alertas para não deixar vencimentos passarem.',
      ],
      icon: Icons.school_outlined,
    ),
    'compliance_alerts': TutorialContent(
      title: 'Alertas e obrigações',
      description:
          'Esta tela reúne prazos e obrigações que precisam ser acompanhados.',
      tips: [
        'Comece pelos itens vencidos ou próximos do vencimento.',
        'Abra o item para identificar a empresa e o que precisa ser feito.',
        'Use a tela como uma lista diária de acompanhamento.',
      ],
      icon: Icons.notification_important_outlined,
    ),
    'cipa': TutorialContent(
      title: 'CIPA',
      description:
          'Use esta área para organizar eleições, candidatos e votação da CIPA.',
      tips: [
        'Crie a eleição e cadastre os candidatos.',
        'Gere o QR Code quando for usar votação digital.',
        'Acompanhe os votos e o resultado dentro do processo.',
      ],
      icon: Icons.how_to_vote_outlined,
    ),
    'checklists': TutorialContent(
      title: 'Biblioteca de checklists',
      description:
          'Aqui ficam os modelos prontos para acelerar suas vistorias.',
      tips: [
        'Pesquise modelos por atividade, equipamento, setor ou NR.',
        'Use checklist somente quando aplicável e documente achados com foto.',
        'Sugestões automáticas e biblioteca são apoio, não decisão técnica automática.',
      ],
      icon: Icons.library_add_check_outlined,
    ),
    'routine': TutorialContent(
      title: 'Rotina SST',
      description:
          'Reúne registros do dia a dia que não precisam virar uma vistoria completa.',
      tips: [
        'Registre DDS, treinamentos e demais atividades disponíveis na sua conta.',
        'Confira agenda, empresa/obra e responsável antes de registrar a execução.',
        'Em obra, acompanhe a NR-18 por etapa quando o módulo estiver disponível.',
      ],
      icon: Icons.dashboard_customize_outlined,
    ),
    'improvements': TutorialContent(
      title: 'Melhorias',
      description:
          'Registre mudanças positivas feitas pela empresa e demonstre a evolução do trabalho.',
      tips: [
        'Registre a situação anterior e a melhoria realizada.',
        'Adicione fotos para comprovar o resultado.',
        'Use os registros em acompanhamentos e apresentações gerenciais.',
      ],
      icon: Icons.auto_awesome_outlined,
    ),
    'dashboard': TutorialContent(
      title: 'Indicadores',
      description:
          'Mostra um resumo do desempenho e ajuda a identificar onde concentrar atenção.',
      tips: [
        'Priorize pendências, prazos vencidos e indicadores por empresa.',
        'No PC, use filtros e supervisão ADM conforme sua autorização.',
        'Último contato do técnico não comprova que ele esteja online agora.',
      ],
      icon: Icons.bar_chart_rounded,
    ),
    'new_inspection': TutorialContent(
      title: 'Nova vistoria',
      description:
          'Aqui você monta e executa uma inspeção completa passo a passo.',
      tips: [
        'Selecione empresa/obra, setor e checklist pertinente.',
        'Registre os itens observados com descrição e foto de evidência.',
        'Salve rascunho para continuar depois e valide o PDF ao finalizar.',
      ],
      icon: Icons.add_a_photo_outlined,
    ),
    'latest_features': TutorialContent(
      title: 'Novidades do Auditar SST',
      description: 'Conheça os principais atalhos e confirme o que está habilitado na instalação.',
      tips: [
        'Visita rápida: empresa/obra, NC, rascunho, pendências e Linha do Tempo.',
        'Cliente pode informar correção, mas o técnico deve confirmar ou rejeitar, em Central habilitada.',
        'Agenda, biblioteca offline, relatórios e supervisão ADM variam por perfil e versão.',
      ],
      icon: Icons.auto_awesome_rounded,
    ),
    'client_treatments': TutorialContent(
      title: 'Comunicação e tratativas',
      description: 'Cliente e técnico acompanham a correção com evidências.',
      tips: [
        'Cliente envia pedido de apoio ou sinaliza correção no painel habilitado.',
        'Técnico analisa evidência e responde validando ou rejeitando com justificativa.',
        'A Central Online deve estar publicada e a permissão tratativas habilitada.',
      ],
      icon: Icons.forum_outlined,
    ),
    'company_timeline': TutorialContent(
      title: 'Linha do tempo da empresa',
      description: 'Histórico consolidado da empresa selecionada.',
      tips: [
        'Em Iniciar visita, escolha empresa/obra e procure Linha do Tempo.',
        'Consulte vistorias, DDS, treinamentos e correções.',
        'A linha do tempo histórica não substitui o chat de tratativas.',
      ],
      icon: Icons.timeline_rounded,
    ),
    'offline_knowledge': TutorialContent(
      title: 'Biblioteca técnica offline',
      description: 'Referências e sugestões para avaliação profissional.',
      tips: [
        'Pesquise por atividade, NR ou equipamento.',
        'Reveja a pertinência antes de aplicar a sugestão à ocorrência.',
        'A biblioteca não substitui avaliação técnica nem determina infração automaticamente.',
      ],
      icon: Icons.menu_book_outlined,
    ),
    'admin_supervision': TutorialContent(
      title: 'Supervisão ADM',
      description: 'Acompanhe atividades e contas conforme permissões.',
      tips: [
        'No Windows, use filtros por técnico, empresa e período.',
        'Último contato não equivale a presença online instantânea.',
        'Criação de contas e permissões exige autorização administrativa.',
      ],
      icon: Icons.admin_panel_settings_outlined,
    ),
    'technician_agenda': TutorialContent(
      title: 'Agenda dos técnicos',
      description: 'Consulte compromissos e acompanhamento por empresa/obra.',
      tips: [
        'Confira data, responsável e empresa/obra.',
        'Atualize o compromisso conforme o procedimento da empresa.',
        'Verifique sincronização e permissões antes de considerar a agenda atualizada.',
      ],
      icon: Icons.calendar_month_rounded,
    ),
    'nr18': TutorialContent(
      title: 'NR-18 por obra',
      description: 'Registros e verificações de segurança na obra.',
      tips: [
        'Selecione a empresa e a obra correta.',
        'Registre a etapa ou atividade e anexe evidências pertinentes.',
        'Acompanhe pendências sem misturar registros de obras diferentes.',
      ],
      icon: Icons.construction_rounded,
    ),
    'ronda': TutorialContent(
      title: 'Ronda de segurança',
      description: 'Registro rápido de observações e fotos.',
      tips: [
        'Abra Iniciar visita e selecione a empresa e a obra corretas.',
        'Entre em Ronda e informe o local, o problema e a evidência fotográfica.',
        'Salve e reabra o histórico para confirmar que os dados foram registrados.',
      ],
      icon: Icons.directions_walk_rounded,
    ),
    'field_operational': TutorialContent(
      title: 'Pendências em destaque',
      description: 'Saiba o que precisa de atenção primeiro.',
      tips: [
        'Escolha a empresa e entre em Pendências ou Central Operacional.',
        'Confira primeiro NCs críticas, itens vencidos e outras prioridades.',
        'Abra o registro e verifique situação, responsável, prazo e histórico.',
      ],
      icon: Icons.priority_high_rounded,
    ),
    'reports_pdf': TutorialContent(
      title: 'Relatórios e PDF',
      description: 'Confira os dados antes de compartilhar.',
      tips: [
        'Abra Relatórios ou o histórico da vistoria/ronda da empresa.',
        'Confira título, setor, foto, risco, recomendação e conclusão.',
        'Gere e abra o PDF para revisar as páginas antes de enviar.',
      ],
      icon: Icons.picture_as_pdf_outlined,
    ),
    'offline_sync': TutorialContent(
      title: 'Uso offline e sincronização',
      description: 'Registre atividades mesmo quando não há internet.',
      tips: [
        'Antes da visita, entre na conta autorizada e confirme os dados disponíveis.',
        'Sem internet, salve os registros e não apague rascunhos nem a fila.',
        'Com internet novamente, confira o envio e a presença dos registros.',
      ],
      icon: Icons.cloud_off_outlined,
    ),
    'nc_names': TutorialContent(
      title: 'Identificação de uma NC',
      description: 'Use nomes claros e preserve o código oficial.',
      tips: [
        'Exemplo: Proteção removida ou Extintor vencido.',
        'Enquanto o nome editável não estiver homologado, use descrição clara.',
        'O código e o ID oficiais continuam sendo a referência do registro.',
      ],
      icon: Icons.drive_file_rename_outline,
    ),
    'photo_evidence': TutorialContent(
      title: 'Fotos e evidências',
      description: 'Registre imagens úteis para demonstrar os riscos.',
      tips: [
        'Fotografe o local e o detalhe do problema, com boa iluminação.',
        'Confira se a foto abre corretamente antes de sair do registro.',
        'Compare Antes e Depois na correção; solicite nova prova quando necessário.',
      ],
      icon: Icons.photo_camera_outlined,
    ),
    'permissions': TutorialContent(
      title: 'Perfis e permissões',
      description: 'Cada perfil vê as empresas e funções autorizadas.',
      tips: [
        'Técnico: registre vistorias, riscos, evidências e recomendações.',
        'Cliente: consulte pendências e informe correções, se habilitado.',
        'ADM: acompanhe a equipe e gerencie contas com a devida permissão.',
      ],
      icon: Icons.manage_accounts_outlined,
    ),
    'settings': TutorialContent(
      title: 'Configurações',
      description:
          'Aqui ficam sua conta, sincronização, backup, Google Drive e preferências do aplicativo.',
      tips: [
        'Use Ajuda rápida e Reiniciar mini tutorial para rever as orientações.',
        'Verifique a fila de sincronização e não apague pendências não enviadas.',
        'Em atualização, preserve dados e fotos; não desinstale sem backup.',
      ],
      icon: Icons.settings_outlined,
    ),
  };
}

class TutorialScreenShell extends StatefulWidget {
  final String tutorialId;
  final Widget child;

  const TutorialScreenShell({
    super.key,
    required this.tutorialId,
    required this.child,
  });

  @override
  State<TutorialScreenShell> createState() => _TutorialScreenShellState();
}

class _TutorialScreenShellState extends State<TutorialScreenShell> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      Future<void>.delayed(const Duration(milliseconds: 280), () async {
        if (!mounted) return;
        await TutorialCoach.showIfNeeded(context, widget.tutorialId);
      });
    });
  }

  @override
  Widget build(BuildContext context) => widget.child;
}


class _TutorialGuideCenter extends StatefulWidget {
  const _TutorialGuideCenter();

  @override
  State<_TutorialGuideCenter> createState() => _TutorialGuideCenterState();
}

class _TutorialGuideCenterState extends State<_TutorialGuideCenter> {
  String search = '';

  static const Map<String, List<String>> groups = {
    'Comece por aqui': ['home', 'companies', 'company_detail', 'field_quick', 'new_inspection', 'ronda', 'history'],
    'NCs e evidências': ['field_operational', 'non_conformities', 'nc_names', 'photo_evidence', 'action_plan', 'company_timeline', 'client_treatments', 'improvements'],
    'Documentos e rotinas SST': ['reports_pdf', 'checklists', 'offline_knowledge', 'nr18', 'workers', 'trainings', 'routine', 'cipa'],
    'Agenda, gestão e acesso': ['technician_agenda', 'dashboard', 'admin_supervision', 'permissions', 'compliance_alerts'],
    'Ajuda e segurança': ['latest_features', 'offline_sync', 'settings'],
  };

  @override
  Widget build(BuildContext context) {
    final size = MediaQuery.sizeOf(context);
    final value = search.trim().toLowerCase();
    bool contains(String id) {
      final topic = TutorialCatalog.items[id];
      if (topic == null) return false;
      return value.isEmpty ||
          topic.title.toLowerCase().contains(value) ||
          topic.description.toLowerCase().contains(value) ||
          topic.tips.any((tip) => tip.toLowerCase().contains(value));
    }
    final matches = groups.values.expand((ids) => ids).where(contains).length;

    return Dialog(
      insetPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 18),
      child: SizedBox(
        width: math.min(size.width - 28, 680.0),
        height: math.min(size.height * 0.84, 720.0),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const Icon(Icons.help_outline_rounded, color: AuditarBrand.greenDark),
                  const SizedBox(width: 10),
                  const Expanded(
                    child: Text('Guia de uso do Auditar SST',
                        style: TextStyle(fontWeight: FontWeight.w800,
                            fontSize: 18, color: AuditarBrand.navy)),
                  ),
                  IconButton(
                    tooltip: 'Fechar guia',
                    onPressed: () => Navigator.pop(context),
                    icon: const Icon(Icons.close_rounded),
                  ),
                ],
              ),
              const Text('Escolha um assunto para ver os passos. Você pode consultar este guia sempre que precisar.',
                style: TextStyle(fontSize: 13, height: 1.35)),
              const SizedBox(height: 12),
              TextField(
                onChanged: (v) => setState(() => search = v),
                decoration: const InputDecoration(
                  prefixIcon: Icon(Icons.search),
                  labelText: 'Pesquisar função ou dúvida',
                  hintText: 'NC, ronda, PDF, cliente...',
                  border: OutlineInputBorder(),
                  isDense: true,
                ),
              ),
              const SizedBox(height: 10),
              Text('$matches assuntos encontrados',
                  style: const TextStyle(fontSize: 12, color: AuditarBrand.neutral)),
              const SizedBox(height: 6),
              Expanded(
                child: ListView(
                  children: [
                    for (final group in groups.entries)
                      if (group.value.any(contains)) ...[
                        Padding(
                          padding: const EdgeInsets.only(top: 12, bottom: 5),
                          child: Text(group.key, style: const TextStyle(
                              fontWeight: FontWeight.w800, color: AuditarBrand.navy)),
                        ),
                        for (final id in group.value.where(contains))
                          ListTile(
                            contentPadding: const EdgeInsets.symmetric(horizontal: 4),
                            leading: Icon(TutorialCatalog.items[id]!.icon,
                                color: AuditarBrand.greenDark),
                            title: Text(TutorialCatalog.items[id]!.title),
                            subtitle: Text(TutorialCatalog.items[id]!.description,
                                maxLines: 2, overflow: TextOverflow.ellipsis),
                            trailing: const Icon(Icons.chevron_right_rounded),
                            onTap: () => TutorialCoach.show(context, id, force: true),
                          ),
                      ],
                    if (matches == 0)
                      const Padding(
                        padding: EdgeInsets.all(20),
                        child: Text('Nenhum assunto encontrado. Pesquise por empresa, NC, vistoria, PDF ou cliente.',
                          textAlign: TextAlign.center),
                      ),
                  ],
                ),
              ),
              const SizedBox(height: 6),
              const Text('Recursos podem depender da versão instalada, perfil e homologação da Central Online.',
                  style: TextStyle(fontSize: 11, height: 1.3,
                      color: AuditarBrand.neutral)),
            ],
          ),
        ),
      ),
    );
  }
}

class TutorialCoach {
  TutorialCoach._();

  static Future<void> showGuide(BuildContext context) async {
    await showDialog<void>(
      context: context,
      builder: (_) => const _TutorialGuideCenter(),
    );
  }

  static Future<void> showIfNeeded(
    BuildContext context,
    String tutorialId,
  ) async {
    try {
      if (!await TutorialService.shouldShow(tutorialId)) return;
      if (!context.mounted) return;
      await show(context, tutorialId);
    } catch (_) {
      // O tutorial nunca deve impedir o uso do aplicativo.
    }
  }

  static Future<void> show(
    BuildContext context,
    String tutorialId, {
    bool force = false,
  }) async {
    final content = TutorialCatalog.items[tutorialId];
    if (content == null) return;
    if (!force && !await TutorialService.shouldShow(tutorialId)) return;
    if (!context.mounted) return;

    final result = await showGeneralDialog<String>(
      context: context,
      barrierDismissible: false,
      barrierLabel: 'Mini tutorial',
      barrierColor: Colors.black.withValues(alpha: .52),
      transitionDuration: const Duration(milliseconds: 220),
      pageBuilder: (dialogContext, animation, secondaryAnimation) {
        final width = MediaQuery.sizeOf(dialogContext).width;
        final bottomPadding = width >= 760 ? 28.0 : 16.0;
        return SafeArea(
          child: Align(
            alignment: Alignment.bottomCenter,
            child: Padding(
              padding: EdgeInsets.fromLTRB(14, 14, 14, bottomPadding),
              child: ConstrainedBox(
                constraints: BoxConstraints(
                  maxWidth: 540,
                  maxHeight: math.min(MediaQuery.sizeOf(dialogContext).height * 0.82, 640.0),
                ),
                child: Material(
                  type: MaterialType.transparency,
                  child: Stack(
                    clipBehavior: Clip.none,
                    children: [
                      Container(
                        padding: const EdgeInsets.fromLTRB(18, 18, 18, 16),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(22),
                          boxShadow: const [
                            BoxShadow(
                              color: Color(0x40000000),
                              blurRadius: 28,
                              offset: Offset(0, 12),
                            ),
                          ],
                        ),
                        child: SingleChildScrollView(
                          child: Column(
                            mainAxisSize: MainAxisSize.min,
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                            Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Container(
                                  width: 46,
                                  height: 46,
                                  decoration: BoxDecoration(
                                    color: AuditarBrand.greenSoft,
                                    borderRadius: BorderRadius.circular(14),
                                  ),
                                  child: Icon(
                                    content.icon,
                                    color: AuditarBrand.greenDark,
                                  ),
                                ),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        content.title,
                                        style: const TextStyle(
                                          color: AuditarBrand.navy,
                                          fontSize: 18,
                                          fontWeight: FontWeight.w900,
                                        ),
                                      ),
                                      const SizedBox(height: 5),
                                      Text(
                                        content.description,
                                        style: const TextStyle(
                                          color: Color(0xFF475467),
                                          fontSize: 13.5,
                                          height: 1.4,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 14),
                            ...content.tips.asMap().entries.map(
                              (entry) => Padding(
                                padding: const EdgeInsets.only(bottom: 8),
                                child: Row(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Container(
                                      width: 24,
                                      height: 24,
                                      alignment: Alignment.center,
                                      decoration: BoxDecoration(
                                        color: AuditarBrand.greenSoft,
                                        borderRadius: BorderRadius.circular(12),
                                      ),
                                      child: Text(
                                        '${entry.key + 1}',
                                        style: const TextStyle(
                                          fontSize: 12,
                                          fontWeight: FontWeight.w800,
                                          color: AuditarBrand.greenDark,
                                        ),
                                      ),
                                    ),
                                    const SizedBox(width: 9),
                                    Expanded(
                                      child: Text(
                                        entry.value,
                                        style: const TextStyle(
                                          fontSize: 13,
                                          height: 1.35,
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                            const SizedBox(height: 5),
                            Text(
                              content.welcome
                                  ? 'As próximas dicas aparecem quando você abrir cada área pela primeira vez.'
                                  : 'Esta dica aparece apenas na primeira vez. Você pode reativar todas em Configurações.',
                              style: const TextStyle(
                                color: AuditarBrand.neutral,
                                fontSize: 11.5,
                                height: 1.3,
                              ),
                            ),
                            const SizedBox(height: 14),
                            Row(
                              children: [
                                Expanded(
                                  child: TextButton(
                                    onPressed: () => Navigator.pop(
                                      dialogContext,
                                      'disable',
                                    ),
                                    child: Text(
                                      content.welcome
                                          ? 'Não mostrar dicas'
                                          : 'Parar dicas',
                                    ),
                                  ),
                                ),
                                const SizedBox(width: 8),
                                Expanded(
                                  child: FilledButton(
                                    onPressed: () => Navigator.pop(
                                      dialogContext,
                                      'seen',
                                    ),
                                    child: Text(
                                      content.welcome ? 'Começar' : 'Entendi',
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ],
                          ),
                        ),
                      ),
                      Positioned(
                        top: -7,
                        left: 34,
                        child: Transform.rotate(
                          angle: math.pi / 4,
                          child: Container(
                            width: 16,
                            height: 16,
                            color: Colors.white,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        );
      },
      transitionBuilder: (context, animation, secondaryAnimation, child) {
        final curved = CurvedAnimation(
          parent: animation,
          curve: Curves.easeOutCubic,
        );
        return FadeTransition(
          opacity: curved,
          child: SlideTransition(
            position: Tween<Offset>(
              begin: const Offset(0, .08),
              end: Offset.zero,
            ).animate(curved),
            child: child,
          ),
        );
      },
    );

    if (result == 'disable') {
      await TutorialService.disableAll();
    } else if (result == 'seen') {
      await TutorialService.markSeen(tutorialId);
    }
  }
}
