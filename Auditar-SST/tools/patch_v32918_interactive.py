#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
APP = REPO / 'app' / 'Auditar_SST_v1_5_dashboard'


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f'Trecho esperado não encontrado: {label}')
    return text.replace(old, new, 1)


def patch_ai_chat() -> None:
    path = APP / 'lib/screens/ai_report_chat_screen.dart'
    text = path.read_text(encoding='utf-8')

    text = replace_once(
        text,
        """class AiReportChatScreen extends StatefulWidget {\n  final String inspectionId;\n  final String reportTitle;\n\n  const AiReportChatScreen({\n    super.key,\n    required this.inspectionId,\n    required this.reportTitle,\n  });""",
        """class AiReportChatScreen extends StatefulWidget {\n  final String inspectionId;\n  final String reportTitle;\n  final bool executiveMode;\n\n  const AiReportChatScreen({\n    super.key,\n    required this.inspectionId,\n    required this.reportTitle,\n    this.executiveMode = false,\n  });""",
        'modo executivo no construtor do chat',
    )

    text = replace_once(
        text,
        """  static const _initialPrompt =\n      'Faça uma auditoria crítica inicial deste relatório antes da emissão. '\n      'Procure ativamente erros, contradições, informações frágeis, lacunas, '\n      'duplicidades, prioridades ou prazos questionáveis e conclusões mais fortes '\n      'do que os dados permitem. Não valide o relatório por padrão.';""",
        """  static const _criticalInitialPrompt =\n      'Faça uma auditoria crítica inicial deste relatório antes da emissão. '\n      'Procure ativamente erros, contradições, informações frágeis, lacunas, '\n      'duplicidades, prioridades ou prazos questionáveis e conclusões mais fortes '\n      'do que os dados permitem. Não valide o relatório por padrão.';\n\n  static const _executiveInitialPrompt =\n      'Atue como assistente gerencial do Relatório Executivo. Use somente os dados '\n      'registrados nesta vistoria. Comece destacando o que merece atenção, o que a '\n      'empresa precisa providenciar e quais ações devem ser priorizadas. Não invente '\n      'quantidades, status, prazos, responsáveis, normas ou fatos ausentes. Quando '\n      'um dado não estiver disponível, diga claramente que precisa ser confirmado.';\n\n  String get _initialPrompt =>\n      widget.executiveMode ? _executiveInitialPrompt : _criticalInitialPrompt;""",
        'prompts dos dois modos',
    )

    text = replace_once(
        text,
        """    final history = _historyForApi();\n    setState(() {""",
        """    final history = _historyForApi();\n    final apiQuestion = widget.executiveMode\n        ? 'MODO EXECUTIVO GERENCIAL. Responda com foco prático para decisão da gestão, '\n            'usando exclusivamente os dados do relatório. Não invente quantidades, '\n            'status, prazos, responsáveis ou obrigações. Se faltar informação, indique '\n            'o que deve ser confirmado. Pergunta do usuário: $question'\n        : question;\n    setState(() {""",
        'contexto executivo em cada pergunta',
    )

    text = replace_once(
        text,
        """      question: question,\n      history: history,""",
        """      question: apiQuestion,\n      history: history,""",
        'pergunta contextualizada enviada ao backend',
    )

    text = replace_once(
        text,
        """          verdict: '${result['verdict'] ?? 'Revisão concluída'}'.trim(),""",
        """          verdict: '${result['verdict'] ?? (widget.executiveMode ? 'Análise gerencial' : 'Revisão concluída')}'.trim(),""",
        'título padrão da resposta',
    )

    text = replace_once(
        text,
        """                    message.verdict.isEmpty ? 'Revisor crítico' : message.verdict,""",
        """                    message.verdict.isEmpty\n                        ? (widget.executiveMode\n                            ? 'IA do Relatório Executivo'\n                            : 'Revisor crítico')\n                        : message.verdict,""",
        'identidade da resposta',
    )

    text = replace_once(
        text,
        """        title: const Text('Revisor crítico do relatório'),""",
        """        title: Text(\n          widget.executiveMode\n              ? 'IA do Relatório Executivo'\n              : 'Revisor crítico do relatório',\n        ),""",
        'título da tela',
    )

    text = replace_once(
        text,
        """                color: Colors.orange.shade50,\n                borderRadius: BorderRadius.circular(12),\n                border: Border.all(color: Colors.orange.shade200),\n              ),\n              child: const Text(\n                'Modo crítico: a IA deve procurar problemas e questionar o relatório, '\n                'não apenas confirmar o que já foi escrito. Ela não altera nenhum '\n                'dado automaticamente; a decisão final continua sendo do TST.',\n                style: TextStyle(height: 1.35, fontWeight: FontWeight.w600),\n              ),""",
        """                color: widget.executiveMode\n                    ? Colors.blue.shade50\n                    : Colors.orange.shade50,\n                borderRadius: BorderRadius.circular(12),\n                border: Border.all(\n                  color: widget.executiveMode\n                      ? Colors.blue.shade200\n                      : Colors.orange.shade200,\n                ),\n              ),\n              child: Text(\n                widget.executiveMode\n                    ? 'Modo Executivo: converse com a IA sobre prioridades, compras, '\n                        'manutenção, sinalização, treinamentos, ações atrasadas e o que '\n                        'levar para a gestão. A IA não altera os registros e não deve '\n                        'inventar quantidades, prazos ou responsáveis.'\n                    : 'Modo crítico: a IA deve procurar problemas e questionar o relatório, '\n                        'não apenas confirmar o que já foi escrito. Ela não altera nenhum '\n                        'dado automaticamente; a decisão final continua sendo do TST.',\n                style: const TextStyle(\n                  height: 1.35,\n                  fontWeight: FontWeight.w600,\n                ),\n              ),""",
        'cartão explicativo dos modos',
    )

    text = replace_once(
        text,
        """                children: [\n                  _quick('Contradições', 'Procure contradições entre status, observações, riscos, recomendações e conclusão.'),\n                  _quick('Normas', 'Questione as referências normativas. Aponte onde a norma parece genérica, incerta ou precisa ser conferida.'),\n                  _quick('Prazos', 'Analise criticamente prioridades, responsáveis e prazos do plano de ação. Aponte o que parece incoerente ou sem justificativa.'),\n                  _quick('Conclusão', 'Revise a conclusão como um auditor exigente. Aponte exageros, termos frágeis e o que deveria ser reescrito.'),\n                ],""",
        """                children: widget.executiveMode\n                    ? [\n                        _quick(\n                          'Prioridades',\n                          'Quais são as prioridades gerenciais deste relatório? Ordene do mais urgente para o menos urgente e explique brevemente o motivo.',\n                        ),\n                        _quick(\n                          'Providenciar',\n                          'Resuma o que a empresa precisa providenciar, agrupando ações semelhantes. Use somente quantidades que estejam claramente registradas.',\n                        ),\n                        _quick(\n                          'Compras',\n                          'Quais itens ou serviços aparentam exigir compra ou contratação? Não invente quantidades e sinalize o que precisa ser confirmado.',\n                        ),\n                        _quick(\n                          'Manutenção',\n                          'Liste as pendências relacionadas a manutenção, reparo, instalação ou proteção coletiva e destaque as mais prioritárias.',\n                        ),\n                        _quick(\n                          'Atrasadas',\n                          'Quais ações estão vencidas ou atrasadas segundo os dados registrados? Informe responsável e prazo somente quando constarem no relatório.',\n                        ),\n                        _quick(\n                          'Mensagem à gestão',\n                          'Prepare uma mensagem curta e profissional para a gestão com as principais providências deste relatório, sem inventar dados.',\n                        ),\n                      ]\n                    : [\n                        _quick('Contradições', 'Procure contradições entre status, observações, riscos, recomendações e conclusão.'),\n                        _quick('Normas', 'Questione as referências normativas. Aponte onde a norma parece genérica, incerta ou precisa ser conferida.'),\n                        _quick('Prazos', 'Analise criticamente prioridades, responsáveis e prazos do plano de ação. Aponte o que parece incoerente ou sem justificativa.'),\n                        _quick('Conclusão', 'Revise a conclusão como um auditor exigente. Aponte exageros, termos frágeis e o que deveria ser reescrito.'),\n                      ],""",
        'atalhos de conversa executiva',
    )

    text = replace_once(
        text,
        """                            Text('Revisando criticamente...'),""",
        """                            Text(\n                              widget.executiveMode\n                                  ? 'Analisando para a gestão...'\n                                  : 'Revisando criticamente...',\n                            ),""",
        'texto de carregamento',
    )

    text = replace_once(
        text,
        """                      decoration: const InputDecoration(\n                        hintText: 'Pergunte sobre um erro, item, prazo, NR, conclusão...',\n                        border: OutlineInputBorder(),\n                        isDense: true,\n                      ),""",
        """                      decoration: InputDecoration(\n                        hintText: widget.executiveMode\n                            ? 'Pergunte o que priorizar, comprar, corrigir ou levar para a gestão...'\n                            : 'Pergunte sobre um erro, item, prazo, NR, conclusão...',\n                        border: const OutlineInputBorder(),\n                        isDense: true,\n                      ),""",
        'campo de pergunta executivo',
    )

    path.write_text(text, encoding='utf-8')


def patch_report_screen() -> None:
    path = APP / 'lib/screens/report_screen.dart'
    text = path.read_text(encoding='utf-8')

    marker = '  Future<void> _setExecutiveAiEnabled(bool value) async {\n'
    method = """  Future<void> _openExecutiveAiChat() async {\n    await Navigator.of(context).push(\n      MaterialPageRoute(\n        builder: (_) => AiReportChatScreen(\n          inspectionId: widget.inspectionId,\n          reportTitle: widget.title,\n          executiveMode: true,\n        ),\n      ),\n    );\n  }\n\n"""
    text = replace_once(
        text,
        marker,
        method + marker,
        'abertura do chat executivo',
    )

    text = replace_once(
        text,
        """                  if (executiveAiEnabled) ...[\n                    const SizedBox(height: 4),\n                    SizedBox(\n                      width: double.infinity,\n                      child: OutlinedButton.icon(""",
        """                  if (executiveAiEnabled) ...[\n                    const SizedBox(height: 4),\n                    SizedBox(\n                      width: double.infinity,\n                      child: FilledButton.icon(\n                        onPressed: _openExecutiveAiChat,\n                        icon: const Icon(Icons.forum_outlined),\n                        label: const Text('Conversar com a IA sobre o Executivo'),\n                        style: FilledButton.styleFrom(\n                          backgroundColor: AuditarBrand.navyDark,\n                          padding: const EdgeInsets.symmetric(vertical: 12),\n                        ),\n                      ),\n                    ),\n                    const SizedBox(height: 8),\n                    SizedBox(\n                      width: double.infinity,\n                      child: OutlinedButton.icon(""",
        'botão de conversa do executivo',
    )

    path.write_text(text, encoding='utf-8')


def validate() -> None:
    chat = (APP / 'lib/screens/ai_report_chat_screen.dart').read_text(encoding='utf-8')
    report = (APP / 'lib/screens/report_screen.dart').read_text(encoding='utf-8')
    checks = {
        'modo executivo no chat': 'final bool executiveMode;' in chat,
        'prompt executivo': 'MODO EXECUTIVO GERENCIAL' in chat,
        'atalho prioridades': "'Prioridades'" in chat,
        'atalho providenciar': "'Providenciar'" in chat,
        'atalho gestão': "'Mensagem à gestão'" in chat,
        'botão executivo': 'Conversar com a IA sobre o Executivo' in report,
        'abertura executiva': 'executiveMode: true' in report,
        'revisor crítico preservado': 'Revisor crítico: analisar e conversar' in report,
    }
    missing = [name for name, ok in checks.items() if not ok]
    if missing:
        raise RuntimeError(
            'Validações do chat executivo falharam: ' + ', '.join(missing)
        )


def main() -> int:
    patch_ai_chat()
    patch_report_screen()
    validate()
    print('v3.29.18: chat interativo da IA do Relatório Executivo aplicado.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
