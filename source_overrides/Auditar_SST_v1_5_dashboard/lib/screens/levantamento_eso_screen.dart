import 'package:flutter/material.dart';

class LevantamentoEsoScreen extends StatelessWidget {
  const LevantamentoEsoScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Levantamento ESO'),
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
                    'Coleta de campo para documentos SST',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Organize as informações da visita por empresa, ambiente, função, risco, EPI/EPC e medições. '
                    'O objetivo é deixar os dados prontos para lançamento na plataforma ESO e reduzir retrabalho.',
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 12),
          _ModuleCard(
            icon: Icons.business_search_outlined,
            title: 'Primeira visita',
            subtitle: 'Levantamento inicial completo da empresa para PGR, LTCAT, PCMSO e demais documentos.',
            onTap: () {
              Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => const PrimeiraVisitaEsoScreen(),
                ),
              );
            },
          ),
          _ModuleCard(
            icon: Icons.playlist_add_check_circle_outlined,
            title: 'Levantamento complementar',
            subtitle: 'Completar setores, funções, riscos ou informações que ficaram pendentes.',
            onTap: () => _emBreve(context),
          ),
          _ModuleCard(
            icon: Icons.speed_outlined,
            title: 'Medições',
            subtitle: 'Registrar avaliações quantitativas e vincular aos ambientes, funções e agentes.',
            onTap: () => _emBreve(context),
          ),
          _ModuleCard(
            icon: Icons.rule_folder_outlined,
            title: 'Pendências ESO',
            subtitle: 'Conferir o que ainda falta antes de finalizar o lançamento e os documentos.',
            onTap: () => _emBreve(context),
          ),
        ],
      ),
    );
  }

  static void _emBreve(BuildContext context) {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Módulo previsto para a próxima etapa do Levantamento ESO.'),
      ),
    );
  }
}

class _ModuleCard extends StatelessWidget {
  const _ModuleCard({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.onTap,
  });

  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              CircleAvatar(
                backgroundColor: colorScheme.primaryContainer,
                foregroundColor: colorScheme.onPrimaryContainer,
                child: Icon(icon),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    const SizedBox(height: 4),
                    Text(subtitle),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              const Icon(Icons.chevron_right_rounded),
            ],
          ),
        ),
      ),
    );
  }
}

class PrimeiraVisitaEsoScreen extends StatefulWidget {
  const PrimeiraVisitaEsoScreen({super.key});

  @override
  State<PrimeiraVisitaEsoScreen> createState() => _PrimeiraVisitaEsoScreenState();
}

class _PrimeiraVisitaEsoScreenState extends State<PrimeiraVisitaEsoScreen> {
  final _formKeys = List.generate(6, (_) => GlobalKey<FormState>());

  final _empresaController = TextEditingController();
  final _cnpjController = TextEditingController();
  final _responsavelController = TextEditingController();
  final _telefoneController = TextEditingController();
  final _turnosController = TextEditingController();
  final _observacoesEmpresaController = TextEditingController();

  final _setorController = TextEditingController();
  final _descricaoAmbienteController = TextEditingController();
  final _processoController = TextEditingController();

  final _cargoController = TextEditingController();
  final _cboController = TextEditingController();
  final _atividadeController = TextEditingController();
  final _jornadaController = TextEditingController();

  final _fonteRiscoController = TextEditingController();
  final _exposicaoController = TextEditingController();
  final _medidasControleController = TextEditingController();

  final _epiController = TextEditingController();
  final _caController = TextEditingController();
  final _epcController = TextEditingController();

  int _currentStep = 0;
  int _quantidadeTrabalhadores = 1;
  String? _grupoRisco;
  bool _necessitaMedicao = false;
  bool _epiEficaz = false;
  bool _possuiEpc = false;

  static const _gruposRisco = [
    'Físico',
    'Químico',
    'Biológico',
    'Ergonômico',
    'Acidente / Mecânico',
  ];

  @override
  void dispose() {
    for (final controller in [
      _empresaController,
      _cnpjController,
      _responsavelController,
      _telefoneController,
      _turnosController,
      _observacoesEmpresaController,
      _setorController,
      _descricaoAmbienteController,
      _processoController,
      _cargoController,
      _cboController,
      _atividadeController,
      _jornadaController,
      _fonteRiscoController,
      _exposicaoController,
      _medidasControleController,
      _epiController,
      _caController,
      _epcController,
    ]) {
      controller.dispose();
    }
    super.dispose();
  }

  void _continuar() {
    final key = _formKeys[_currentStep];
    final valid = key.currentState?.validate() ?? true;
    if (!valid) return;

    if (_currentStep < 5) {
      setState(() => _currentStep += 1);
    } else {
      _mostrarResumo();
    }
  }

  void _voltar() {
    if (_currentStep == 0) {
      Navigator.of(context).maybePop();
      return;
    }
    setState(() => _currentStep -= 1);
  }

  void _mostrarResumo() {
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      builder: (context) {
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(20, 20, 20, 24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Resumo do levantamento',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
                const SizedBox(height: 16),
                _ResumoLinha(label: 'Empresa', value: _empresaController.text),
                _ResumoLinha(label: 'Setor', value: _setorController.text),
                _ResumoLinha(label: 'Cargo/Função', value: _cargoController.text),
                _ResumoLinha(label: 'Grupo de risco', value: _grupoRisco ?? '-'),
                _ResumoLinha(label: 'Fonte geradora', value: _fonteRiscoController.text),
                _ResumoLinha(
                  label: 'Necessita medição',
                  value: _necessitaMedicao ? 'Sim' : 'Não',
                ),
                _ResumoLinha(label: 'EPI', value: _epiController.text),
                _ResumoLinha(label: 'EPC', value: _epcController.text),
                const SizedBox(height: 14),
                const Text(
                  'Nesta primeira etapa os dados ainda são mantidos somente durante a tela aberta. '
                  'A próxima etapa liga o formulário ao banco offline e permite vários setores, funções e riscos por visita.',
                ),
                const SizedBox(height: 18),
                SizedBox(
                  width: double.infinity,
                  child: FilledButton.icon(
                    onPressed: () => Navigator.of(context).pop(),
                    icon: const Icon(Icons.check_circle_outline),
                    label: const Text('Conferido'),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('ESO · Primeira visita'),
      ),
      body: Stepper(
        currentStep: _currentStep,
        onStepTapped: (index) => setState(() => _currentStep = index),
        onStepContinue: _continuar,
        onStepCancel: _voltar,
        controlsBuilder: (context, details) {
          return Padding(
            padding: const EdgeInsets.only(top: 18),
            child: Row(
              children: [
                FilledButton.icon(
                  onPressed: details.onStepContinue,
                  icon: Icon(_currentStep == 5 ? Icons.fact_check_outlined : Icons.arrow_forward_rounded),
                  label: Text(_currentStep == 5 ? 'Conferir' : 'Continuar'),
                ),
                const SizedBox(width: 10),
                TextButton(
                  onPressed: details.onStepCancel,
                  child: Text(_currentStep == 0 ? 'Sair' : 'Voltar'),
                ),
              ],
            ),
          );
        },
        steps: [
          Step(
            title: const Text('Empresa'),
            subtitle: const Text('Identificação da primeira visita'),
            isActive: _currentStep >= 0,
            content: Form(
              key: _formKeys[0],
              child: Column(
                children: [
                  _campoObrigatorio(_empresaController, 'Razão social / nome da empresa'),
                  _campo(_cnpjController, 'CNPJ'),
                  _campo(_responsavelController, 'Responsável que acompanha a visita'),
                  _campo(_telefoneController, 'Telefone / contato'),
                  _campo(_turnosController, 'Horários e turnos'),
                  _campo(
                    _observacoesEmpresaController,
                    'Observações gerais da empresa',
                    maxLines: 3,
                  ),
                ],
              ),
            ),
          ),
          Step(
            title: const Text('Ambiente / setor'),
            subtitle: const Text('Descrição do local e processo'),
            isActive: _currentStep >= 1,
            content: Form(
              key: _formKeys[1],
              child: Column(
                children: [
                  _campoObrigatorio(_setorController, 'Nome do setor / ambiente'),
                  _campoObrigatorio(
                    _descricaoAmbienteController,
                    'Descrição física do ambiente',
                    maxLines: 4,
                  ),
                  _campo(
                    _processoController,
                    'Processo / atividades realizadas no setor',
                    maxLines: 4,
                  ),
                ],
              ),
            ),
          ),
          Step(
            title: const Text('Cargo / função'),
            subtitle: const Text('O que o trabalhador realmente executa'),
            isActive: _currentStep >= 2,
            content: Form(
              key: _formKeys[2],
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _campoObrigatorio(_cargoController, 'Cargo / função'),
                  _campo(_cboController, 'CBO'),
                  _campoObrigatorio(
                    _atividadeController,
                    'Descrição das atividades reais',
                    maxLines: 5,
                  ),
                  _campo(_jornadaController, 'Jornada / horário'),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      const Expanded(child: Text('Quantidade de trabalhadores nesta função')),
                      IconButton(
                        tooltip: 'Diminuir',
                        onPressed: _quantidadeTrabalhadores > 1
                            ? () => setState(() => _quantidadeTrabalhadores -= 1)
                            : null,
                        icon: const Icon(Icons.remove_circle_outline),
                      ),
                      Text('$_quantidadeTrabalhadores'),
                      IconButton(
                        tooltip: 'Aumentar',
                        onPressed: () => setState(() => _quantidadeTrabalhadores += 1),
                        icon: const Icon(Icons.add_circle_outline),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
          Step(
            title: const Text('Risco / exposição'),
            subtitle: const Text('Agente, fonte e condição de exposição'),
            isActive: _currentStep >= 3,
            content: Form(
              key: _formKeys[3],
              child: Column(
                children: [
                  DropdownButtonFormField<String>(
                    value: _grupoRisco,
                    decoration: const InputDecoration(
                      labelText: 'Grupo de risco',
                      border: OutlineInputBorder(),
                    ),
                    items: _gruposRisco
                        .map(
                          (item) => DropdownMenuItem(
                            value: item,
                            child: Text(item),
                          ),
                        )
                        .toList(),
                    onChanged: (value) => setState(() => _grupoRisco = value),
                    validator: (value) => value == null ? 'Selecione o grupo de risco.' : null,
                  ),
                  const SizedBox(height: 12),
                  _campoObrigatorio(_fonteRiscoController, 'Agente / fonte geradora'),
                  _campoObrigatorio(
                    _exposicaoController,
                    'Como ocorre a exposição, frequência e duração',
                    maxLines: 4,
                  ),
                  _campo(
                    _medidasControleController,
                    'Medidas de controle existentes',
                    maxLines: 3,
                  ),
                  SwitchListTile.adaptive(
                    contentPadding: EdgeInsets.zero,
                    title: const Text('Necessita avaliação quantitativa / medição?'),
                    value: _necessitaMedicao,
                    onChanged: (value) => setState(() => _necessitaMedicao = value),
                  ),
                ],
              ),
            ),
          ),
          Step(
            title: const Text('EPI / EPC'),
            subtitle: const Text('Controles vinculados ao risco'),
            isActive: _currentStep >= 4,
            content: Form(
              key: _formKeys[4],
              child: Column(
                children: [
                  _campo(_epiController, 'EPI utilizado'),
                  _campo(_caController, 'CA do EPI'),
                  SwitchListTile.adaptive(
                    contentPadding: EdgeInsets.zero,
                    title: const Text('EPI observado como adequado/eficaz?'),
                    value: _epiEficaz,
                    onChanged: (value) => setState(() => _epiEficaz = value),
                  ),
                  SwitchListTile.adaptive(
                    contentPadding: EdgeInsets.zero,
                    title: const Text('Existe EPC para este risco?'),
                    value: _possuiEpc,
                    onChanged: (value) => setState(() => _possuiEpc = value),
                  ),
                  if (_possuiEpc)
                    _campo(
                      _epcController,
                      'Qual EPC / proteção coletiva?',
                      maxLines: 2,
                    ),
                ],
              ),
            ),
          ),
          Step(
            title: const Text('Conferência'),
            subtitle: const Text('Verificação antes de sair da empresa'),
            isActive: _currentStep >= 5,
            content: Form(
              key: _formKeys[5],
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _ConferenciaItem(
                    titulo: 'Empresa identificada',
                    ok: _empresaController.text.trim().isNotEmpty,
                  ),
                  _ConferenciaItem(
                    titulo: 'Setor/ambiente descrito',
                    ok: _setorController.text.trim().isNotEmpty &&
                        _descricaoAmbienteController.text.trim().isNotEmpty,
                  ),
                  _ConferenciaItem(
                    titulo: 'Cargo e atividade registrados',
                    ok: _cargoController.text.trim().isNotEmpty &&
                        _atividadeController.text.trim().isNotEmpty,
                  ),
                  _ConferenciaItem(
                    titulo: 'Risco/fonte/exposição registrados',
                    ok: _grupoRisco != null &&
                        _fonteRiscoController.text.trim().isNotEmpty &&
                        _exposicaoController.text.trim().isNotEmpty,
                  ),
                  _ConferenciaItem(
                    titulo: 'Necessidade de medição definida',
                    ok: true,
                    detalhe: _necessitaMedicao
                        ? 'Há medição complementar marcada como necessária.'
                        : 'Nenhuma medição complementar marcada neste registro.',
                  ),
                  const SizedBox(height: 12),
                  const Text(
                    'Próximas entregas do módulo: vários setores/funções/riscos por visita, fotos, voz para texto, '
                    'salvamento offline, pendências automáticas e espelho dos dados para lançamento no ESO.',
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _campo(
    TextEditingController controller,
    String label, {
    int maxLines = 1,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: TextFormField(
        controller: controller,
        maxLines: maxLines,
        textCapitalization: TextCapitalization.sentences,
        decoration: InputDecoration(
          labelText: label,
          border: const OutlineInputBorder(),
          alignLabelWithHint: maxLines > 1,
        ),
      ),
    );
  }

  Widget _campoObrigatorio(
    TextEditingController controller,
    String label, {
    int maxLines = 1,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: TextFormField(
        controller: controller,
        maxLines: maxLines,
        textCapitalization: TextCapitalization.sentences,
        decoration: InputDecoration(
          labelText: '$label *',
          border: const OutlineInputBorder(),
          alignLabelWithHint: maxLines > 1,
        ),
        validator: (value) {
          if (value == null || value.trim().isEmpty) {
            return 'Preencha este campo.';
          }
          return null;
        },
      ),
    );
  }
}

class _ConferenciaItem extends StatelessWidget {
  const _ConferenciaItem({
    required this.titulo,
    required this.ok,
    this.detalhe,
  });

  final String titulo;
  final bool ok;
  final String? detalhe;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      contentPadding: EdgeInsets.zero,
      leading: Icon(
        ok ? Icons.check_circle_rounded : Icons.error_outline_rounded,
        color: ok
            ? Theme.of(context).colorScheme.primary
            : Theme.of(context).colorScheme.error,
      ),
      title: Text(titulo),
      subtitle: detalhe == null ? null : Text(detalhe!),
    );
  }
}

class _ResumoLinha extends StatelessWidget {
  const _ResumoLinha({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(
              label,
              style: const TextStyle(fontWeight: FontWeight.w600),
            ),
          ),
          Expanded(child: Text(value.trim().isEmpty ? '-' : value)),
        ],
      ),
    );
  }
}
