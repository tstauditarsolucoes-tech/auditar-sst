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
          'Este mini tutorial aparece somente na primeira vez que cada área for aberta. As dicas são curtas e você pode pular quando quiser.',
      tips: [
        'Use “Nova vistoria” para iniciar uma inspeção completa.',
        'Use “Vistoria rápida” quando precisar registrar achados rapidamente em campo.',
        'Os demais recursos ficam organizados nos módulos da tela inicial.',
      ],
      icon: Icons.waving_hand_rounded,
      welcome: true,
    ),
    'companies': TutorialContent(
      title: 'Empresas',
      description:
          'Aqui ficam as empresas atendidas e os dados usados nas vistorias, relatórios e controles.',
      tips: [
        'Cadastre ou pesquise uma empresa pelo nome, CNPJ ou cidade.',
        'Toque na empresa para abrir setores, vistorias, pendências e recursos próprios dela.',
        'Mantenha os setores atualizados para facilitar o preenchimento em campo.',
      ],
      icon: Icons.business_outlined,
    ),
    'company_detail': TutorialContent(
      title: 'Área da empresa',
      description:
          'Esta tela reúne tudo o que está acontecendo nesta empresa em um só lugar.',
      tips: [
        'Visão geral: resumo e atalhos principais.',
        'Vistorias, NCs e Ações: acompanhe problemas e correções.',
        'PGR + IA: consulte e trabalhe os riscos do PGR com apoio da IA.',
      ],
      icon: Icons.domain_outlined,
    ),
    'field_quick': TutorialContent(
      title: 'Vistoria rápida',
      description:
          'Use para registrar vários problemas durante uma ronda sem precisar montar uma vistoria completa antes.',
      tips: [
        'Escolha empresa e setor.',
        'Registre o problema, foto, prioridade e recomendação.',
        'Continue adicionando achados conforme anda pela empresa.',
      ],
      icon: Icons.flash_on_rounded,
    ),
    'history': TutorialContent(
      title: 'Vistorias',
      description:
          'Aqui você encontra vistorias em andamento e já finalizadas.',
      tips: [
        'Retome uma vistoria que ainda não terminou.',
        'Abra uma vistoria finalizada para consultar os registros.',
        'Use os relatórios para entregar o resultado à empresa.',
      ],
      icon: Icons.fact_check_outlined,
    ),
    'non_conformities': TutorialContent(
      title: 'Problemas encontrados',
      description:
          'Esta área concentra as não conformidades registradas nas inspeções.',
      tips: [
        'Veja o que ainda está em aberto e o que já foi resolvido.',
        'Abra o registro para consultar fotos, risco, recomendação e histórico.',
        'Atualize o status quando a empresa corrigir o problema.',
      ],
      icon: Icons.warning_amber_rounded,
    ),
    'action_plan': TutorialContent(
      title: 'Planos de ação',
      description:
          'Aqui você acompanha quem ficou responsável por cada correção e qual é o prazo.',
      tips: [
        'Defina responsável e data para conclusão.',
        'Acompanhe ações abertas, atrasadas e concluídas.',
        'Use esta tela para cobrar e registrar o andamento das correções.',
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
        'Pesquise por equipamento, atividade, setor ou NR.',
        'Ative os modelos que mais usa e personalize quando necessário.',
        'Na Nova vistoria, você pode procurar e adicionar os checklists diretamente.',
      ],
      icon: Icons.library_add_check_outlined,
    ),
    'routine': TutorialContent(
      title: 'Rotina SST',
      description:
          'Reúne registros do dia a dia que não precisam virar uma vistoria completa.',
      tips: [
        'Registre DDS, APR/PT, incidentes e controles de equipamentos.',
        'Use a agenda para lembrar atividades e compromissos.',
        'Mantenha a rotina registrada para facilitar o acompanhamento da empresa.',
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
        'Use filtros para analisar uma empresa ou período específico.',
        'Observe pendências, evolução e setores que mais precisam de atenção.',
        'Os indicadores ajudam a definir prioridades de trabalho.',
      ],
      icon: Icons.bar_chart_rounded,
    ),
    'new_inspection': TutorialContent(
      title: 'Nova vistoria',
      description:
          'Aqui você monta e executa uma inspeção completa passo a passo.',
      tips: [
        'Escolha empresa, setor e os checklists que serão usados.',
        'Durante a inspeção, marque a situação de cada item e registre fotos quando necessário.',
        'Você pode salvar e continuar depois antes de finalizar o relatório.',
      ],
      icon: Icons.add_a_photo_outlined,
    ),
    'settings': TutorialContent(
      title: 'Configurações',
      description:
          'Aqui ficam sua conta, sincronização, backup, Google Drive e preferências do aplicativo.',
      tips: [
        'No Windows, confira a sincronização com o celular.',
        'Use backup e Drive para aumentar a segurança dos dados.',
        'Nesta tela você também pode reiniciar este mini tutorial.',
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

class TutorialCoach {
  TutorialCoach._();

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
                constraints: const BoxConstraints(maxWidth: 540),
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
                            ...content.tips.map(
                              (tip) => Padding(
                                padding: const EdgeInsets.only(bottom: 8),
                                child: Row(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Container(
                                      margin: const EdgeInsets.only(top: 6),
                                      width: 7,
                                      height: 7,
                                      decoration: const BoxDecoration(
                                        color: AuditarBrand.greenDark,
                                        shape: BoxShape.circle,
                                      ),
                                    ),
                                    const SizedBox(width: 9),
                                    Expanded(
                                      child: Text(
                                        tip,
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
                                          ? 'Pular tutorial'
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
