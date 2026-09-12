import 'package:flutter/material.dart';

import 'accessibility_survey_screen.dart';
import 'levantamento_eso_screen.dart';

class TechnicalSurveysScreen extends StatelessWidget {
  const TechnicalSurveysScreen({super.key});

  Future<void> _open(BuildContext context, Widget screen) async {
    await Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => screen),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Levantamentos técnicos'),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Coleta técnica em campo',
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(
                          fontWeight: FontWeight.w800,
                        ),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Use fluxos guiados para coletar as informações necessárias durante a visita, reduzir esquecimentos e deixar os dados prontos para elaboração dos documentos.',
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 12),
          _SurveyCard(
            icon: Icons.assignment_outlined,
            title: 'Levantamento ESO',
            subtitle:
                'Empresa, ambientes, cargos, atividades, riscos, EPI/EPC, medições e pendências para lançamento no ESO.',
            badge: 'SST',
            onTap: () => _open(context, const LevantamentoEsoScreen()),
          ),
          _SurveyCard(
            icon: Icons.accessible_forward_rounded,
            title: 'Laudo de Acessibilidade',
            subtitle:
                'Medidas, fotos, barreiras, rotas, portas, rampas, sanitários, sinalização e Assistente IA.',
            badge: 'IA',
            onTap: () => _open(context, const AccessibilitySurveyScreen()),
          ),
        ],
      ),
    );
  }
}

class _SurveyCard extends StatelessWidget {
  const _SurveyCard({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.badge,
    required this.onTap,
  });

  final IconData icon;
  final String title;
  final String subtitle;
  final String badge;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              CircleAvatar(
                backgroundColor: scheme.primaryContainer,
                foregroundColor: scheme.onPrimaryContainer,
                child: Icon(icon),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            title,
                            style:
                                Theme.of(context).textTheme.titleMedium?.copyWith(
                                      fontWeight: FontWeight.w800,
                                    ),
                          ),
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 8,
                            vertical: 3,
                          ),
                          decoration: BoxDecoration(
                            color: scheme.secondaryContainer,
                            borderRadius: BorderRadius.circular(999),
                          ),
                          child: Text(
                            badge,
                            style: TextStyle(
                              color: scheme.onSecondaryContainer,
                              fontSize: 11,
                              fontWeight: FontWeight.w800,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 5),
                    Text(subtitle),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              const Padding(
                padding: EdgeInsets.only(top: 8),
                child: Icon(Icons.chevron_right_rounded),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
