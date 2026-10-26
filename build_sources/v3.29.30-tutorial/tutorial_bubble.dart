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
          'O mini tutorial é opcional: aparece quando você abre uma área pela primeira vez. Você pode pular, parar as dicas ou reiniciá-las nas Configurações.',
      tips: [
        'Iniciar visita: escolha a empresa/obra antes de registrar Ronda, Vistoria ou NC.',
        'Continuar rascunho: retome o que faltou. Pendências: veja primeiro os riscos críticos e os prazos vencidos.',
        'Relatórios: confira as fotos e o PDF antes de compartilhar com a empresa.',
      ],
      icon: Icons.waving_hand_rounded,
      welcome: true,
    ),
    'companies': TutorialContent(
      title: 'Empresas e obras',
      description:
          'Escolha a empresa certa para manter os registros organizados e separados.',
      tips: [
        'Pesquise a empresa e confirme seu nome ou obra antes de abrir uma visita.',
        'Use setores, empresas recentes e favoritos quando disponíveis na sua versão.',
        'Revise o contexto antes de registrar NC, foto ou relatório para evitar misturar empresas.',
      ],
      icon: Icons.business_outlined,
    ),
    'company_detail': TutorialContent(
      title: 'Área da empresa',
      description:
          'Veja os registros, atividades e pendências vinculados à empresa escolhida.',
      tips: [
        'Consulte vistorias, não conformidades, ações, treinamentos e documentos.',
        'Na Visita Rápida, o atalho Linha do tempo da empresa pode mostrar o histórico de atividades.',
        'Mensagens e confirmação de correções pelo cliente dependem do Painel do Cliente e das permissões.',
      ],
      icon: Icons.domain_outlined,
    ),
    'field_quick': TutorialContent(
      title: 'Visita rápida',
      description:
          'Registre os achados em campo sem perder a empresa/obra selecionada.',
      tips: [
        'Selecione empresa e, quando necessário, obra e setor antes de começar.',
        'Escolha Ronda, Vistoria ou NC, descreva o que observou e acrescente foto e prioridade.',
        'Salve o registro e confira no histórico; continue a visita na mesma empresa.',
      ],
      icon: Icons.flash_on_rounded,
    ),
    'history': TutorialContent(
      title: 'Vistorias e rascunhos',
      description:
          'Retome inspeções, confira os resultados e prepare a entrega.',
      tips: [
        'Abra Continuar rascunho quando precisar terminar uma vistoria iniciada.',
        'Em uma vistoria concluída, confira fotos, descrição do risco, recomendação e histórico.',
        'Gere o PDF, abra a prévia e verifique o documento antes de compartilhar.',
      ],
      icon: Icons.fact_check_outlined,
    ),
    'non_conformities': TutorialContent(
      title: 'Não conformidades (NCs)',
      description:
          'Esta área reúne os problemas encontrados e o acompanhamento das correções.',
      tips: [
        'Priorize as NCs críticas, pendentes ou vencidas da empresa selecionada.',
        'Abra cada NC para conferir descrição, fotos, prazo, status e código oficial.',
        'Descreva claramente o problema, como Proteção removida ou Extintor vencido; nome editável depende da versão homologada.',
      ],
      icon: Icons.warning_amber_rounded,
    ),
    'action_plan': TutorialContent(
      title: 'Plano de ação e correções',
      description:
          'Acompanhe a responsabilidade, o prazo e a validação técnica das correções.',
      tips: [
        'Defina e acompanhe o responsável e o prazo para tratar cada problema.',
        'Quando o Painel do Cliente estiver habilitado, o cliente poderá informar uma correção e anexar evidências.',
        'O técnico deve confirmar ou rejeitar a correção, justificando quando a evidência for insuficiente.',
      ],
      icon: Icons.assignment_turned_in_outlined,
    ),
    'workers': TutorialContent(
      title: 'Trabalhadores',
      description:
          'Organize os dados dos trabalhadores para os controles de SST.',
      tips: [
        'Confira nome, função, setor e vínculo com a empresa correta.',
        'Use a importação quando tiver uma lista maior e a função estiver disponível.',
        'Revise os dados antes de utilizar em treinamentos e demais controles.',
      ],
      icon: Icons.groups_rounded,
    ),
    'trainings': TutorialContent(
      title: 'Treinamentos e DDS',
      description:
          'Acompanhe capacitações e registros de participação.',
      tips: [
        'Verifique quais treinamentos estão realizados, pendentes ou próximos do vencimento.',
        'Registre data, participantes e evidências conforme o tipo de treinamento.',
        'Consulte o histórico antes de emitir ou compartilhar comprovantes.',
      ],
      icon: Icons.school_outlined,
    ),
    'compliance_alerts': TutorialContent(
      title: 'Alertas e obrigações',
      description:
          'Identifique prazos e obrigações que exigem atenção.',
      tips: [
        'Comece pelos itens vencidos e pelos que estão próximos do prazo.',
        'Abra cada alerta e confira empresa, obrigação e responsável.',
        'Após o atendimento, revise o status para manter o acompanhamento confiável.',
      ],
      icon: Icons.notification_important_outlined,
    ),
    'cipa': TutorialContent(
      title: 'CIPA',
      description:
          'Acompanhe as atividades e etapas de gestão da CIPA.',
      tips: [
        'Consulte a eleição, os candidatos e as etapas disponíveis.',
        'Quando aplicável, use o QR Code da votação conforme o procedimento adotado.',
        'Confira o resultado, os registros e o histórico antes de finalizar.',
      ],
      icon: Icons.how_to_vote_outlined,
    ),
    'checklists': TutorialContent(
      title: 'Checklists e apoio técnico',
      description:
          'Encontre modelos para inspecionar as situações de SST.',
      tips: [
        'Pesquise por NR, setor, equipamento ou atividade e escolha somente os itens aplicáveis.',
        'Durante a vistoria, responda os quesitos e registre evidências dos achados.',
        'Biblioteca e sugestões offline são apoio: o julgamento técnico continua com o profissional.',
      ],
      icon: Icons.library_add_check_outlined,
    ),
    'routine': TutorialContent(
      title: 'Rotina SST e agenda',
      description:
          'Registre atividades do dia a dia e acompanhe compromissos.',
      tips: [
        'Use a rotina para DDS, APR/PT, incidentes e demais registros disponíveis.',
        'Confira a agenda e os responsáveis antes de marcar uma atividade como realizada.',
        'Em obras, acompanhe etapas e verificações NR-18 conforme os módulos disponíveis.',
      ],
      icon: Icons.dashboard_customize_outlined,
    ),
    'improvements': TutorialContent(
      title: 'Melhorias e Antes × Depois',
      description:
          'Demonstre as correções e avanços observados na empresa.',
      tips: [
        'Registre a situação inicial e a melhoria implantada.',
        'Inclua fotos Antes e Depois quando houver evidência verificável.',
        'Consulte o histórico e use a comparação para acompanhar a evolução.',
      ],
      icon: Icons.auto_awesome_outlined,
    ),
    'dashboard': TutorialContent(
      title: 'Indicadores e visão gerencial',
      description:
          'Use os indicadores para identificar prioridades de atuação.',
      tips: [
        'Filtre empresa e período e veja pendências, riscos e prazos vencidos.',
        'No Windows, a gestão/ADM pode acompanhar atividades dos técnicos conforme permissões.',
        'Último contato mostra um registro de atividade, não presença online em tempo real.',
      ],
      icon: Icons.bar_chart_rounded,
    ),
    'new_inspection': TutorialContent(
      title: 'Nova vistoria',
      description:
          'Faça uma inspeção completa, com checklist e evidências.',
      tips: [
        'Escolha empresa, setor e checklist adequado ao serviço.',
        'Marque cada item, descreva o achado e confira as fotos antes de salvar.',
        'Se interromper a visita, salve um rascunho. Depois revise o relatório e gere o PDF.',
      ],
      icon: Icons.add_a_photo_outlined,
    ),
    'settings': TutorialContent(
      title: 'Configurações e mini tutorial',
      description:
          'Aqui ficam as preferências e os controles de ajuda e sincronização.',
      tips: [
        'Para rever dicas, use Ajuda e mini tutorial > Reiniciar mini tutorial.',
        'Confira a fila de sincronização sem apagar registros locais ou pendências de envio.',
        'Antes de atualizar o app, preserve seus registros e fotos; não desinstale sem backup.',
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
