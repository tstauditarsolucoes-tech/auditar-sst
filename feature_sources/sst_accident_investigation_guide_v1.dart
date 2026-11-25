import 'package:flutter/material.dart';

/// Guia educativo: não emite CAT, não estabelece nexo e não cria fatos.
class SstAccidentInvestigationGuide extends StatefulWidget {
  const SstAccidentInvestigationGuide({
    super.key,
    required this.onOpenQuestion,
  });

  final ValueChanged<String> onOpenQuestion;

  @override
  State<SstAccidentInvestigationGuide> createState() =>
      _SstAccidentInvestigationGuideState();
}

class _GuideStage {
  const _GuideStage(this.title, this.intro, this.prompts, this.questions);
  final String title;
  final String intro;
  final List<String> prompts;
  final List<(String, String)> questions;
}

class _SstAccidentInvestigationGuideState
    extends State<SstAccidentInvestigationGuide> {
  int selected = 0;

  static const stages = <_GuideStage>[
    _GuideStage(
      '1. Atendimento e segurança',
      'Primeiro, confirme que a pessoa recebeu atendimento e que não há '
          'exposição contínua a uma situação perigosa. Preserve a cena '
          'quando possível, sem prejudicar o socorro.',
      [
        'Houve atendimento e encaminhamento adequado?',
        'A área ou equipamento foi isolado quando necessário?',
        'Quais medidas foram executadas, por quem e quando?',
      ],
      [('incident-06', 'Registrar providências')],
    ),
    _GuideStage(
      '2. Dados e sequência do evento',
      'Registre fatos verificáveis e o trabalho realmente realizado. '
          'Não presuma culpa do trabalhador.',
      [
        'Onde, quando e em qual atividade o evento ocorreu?',
        'O que aconteceu imediatamente antes, durante e depois?',
        'Quais informações são confirmadas e quais ainda são relatos?',
      ],
      [
        ('incident-01', 'Identificação do evento'),
        ('incident-02', 'Cronologia dos fatos'),
      ],
    ),
    _GuideStage(
      '3. Evidências e entrevistas',
      'Identifique a fonte de cada informação. Proteja a privacidade '
          'dos envolvidos e evite dados clínicos desnecessários.',
      [
        'Existem fotografias, registros, documentos ou procedimentos?',
        'Quais pessoas podem relatar o ocorrido sem perguntas sugestivas?',
        'O que ainda precisa ser confirmado?',
      ],
      [('incident-03', 'Registrar evidências')],
    ),
    _GuideStage(
      '4. Ambiente e organização',
      'Compare a atividade real com as proteções e orientações '
          'efetivamente disponibilizadas.',
      [
        'Havia proteção coletiva e ferramenta adequada?',
        'Como eram manutenção, treinamento, supervisão e ritmo de trabalho?',
        'Que condições podem ter contribuído para o evento?',
      ],
      [
        ('incident-04', 'Condições e equipamentos'),
        ('incident-05', 'Organização do trabalho'),
      ],
    ),
    _GuideStage(
      '5. Fatores e cinco porquês',
      'Os cinco porquês orientam a análise: não provam causa raiz '
          'automaticamente. Confirme cada resposta com evidências.',
      [
        'Por que o evento ocorreu segundo os fatos?',
        'Por que a condição perigosa existia?',
        'Por que as barreiras preventivas não evitaram o evento?',
        'Quais fatores continuam sendo apenas hipóteses?',
        'Há outros fatores técnicos e organizacionais envolvidos?',
      ],
      [('incident-07', 'Analisar fatores e causas')],
    ),
    _GuideStage(
      '6. Prevenir e acompanhar',
      'Priorize medidas coletivas e de gestão. Registre responsável, '
          'prazo, evidências e verificação de eficácia.',
      [
        'Qual medida evita a repetição, além de reforçar o uso de EPI?',
        'Quem executará, até quando e com qual comprovação?',
        'Quem verificará eficácia? Deve-se revisar o PGR e o plano de ação?',
      ],
      [
        ('incident-08', 'Plano de prevenção'),
        ('incident-09', 'Verificar as medidas'),
      ],
    ),
  ];

  @override
  Widget build(BuildContext context) {
    final stage = stages[selected];
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                const Icon(Icons.fact_check_outlined),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Assistente de investigação',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 6),
            const Text(
              'Siga as etapas e registre as respostas no formulário abaixo. '
              'O formulário já permite rascunho local, fotos e PDF.',
            ),
            const SizedBox(height: 12),
            Text(
              'Etapa ' + (selected + 1).toString() + ' de ' +
                  stages.length.toString(),
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 4),
            LinearProgressIndicator(value: (selected + 1) / stages.length),
            const SizedBox(height: 12),
            Text(stage.title,
                style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16)),
            const SizedBox(height: 6),
            Text(stage.intro),
            const SizedBox(height: 8),
            for (final prompt in stage.prompts)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 3),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Icon(Icons.help_outline, size: 18),
                    const SizedBox(width: 7),
                    Expanded(child: Text(prompt)),
                  ],
                ),
              ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 6,
              children: [
                for (final question in stage.questions)
                  OutlinedButton.icon(
                    onPressed: () => widget.onOpenQuestion(question.$1),
                    icon: const Icon(Icons.edit_note_outlined),
                    label: Text(question.$2),
                  ),
              ],
            ),
            const SizedBox(height: 10),
            Row(
              children: [
                TextButton(
                  onPressed: selected == 0
                      ? null
                      : () => setState(() => selected--),
                  child: const Text('Anterior'),
                ),
                const Spacer(),
                FilledButton(
                  onPressed: selected == stages.length - 1
                      ? null
                      : () => setState(() => selected++),
                  child: const Text('Próxima etapa'),
                ),
              ],
            ),
            const Divider(),
            const Text(
              'A investigação não substitui atendimento, CAT/eSocial '
              'ou avaliação profissional. A CAT, quando devida, tem prazo '
              'legal: em regra, até o primeiro dia útil seguinte; em caso '
              'de morte, imediatamente. O aplicativo não envia a CAT.',
              style: TextStyle(fontSize: 12),
            ),
          ],
        ),
      ),
    );
  }
}
