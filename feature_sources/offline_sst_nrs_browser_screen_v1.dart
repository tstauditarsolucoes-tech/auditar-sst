import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../services/offline_sst_all_nrs_v1.dart';
import '../services/offline_sst_deep_catalog_v2.dart';

/// Consulta local dos modelos da Biblioteca SST. Não registra uma NC, nem
/// depende da Central, da autenticação, da IA ou de uma conexão de dados.
class OfflineSstNrsBrowserScreen extends StatefulWidget {
  const OfflineSstNrsBrowserScreen({super.key});

  @override
  State<OfflineSstNrsBrowserScreen> createState() =>
      _OfflineSstNrsBrowserScreenState();
}

class _OfflineSstNrsBrowserScreenState
    extends State<OfflineSstNrsBrowserScreen> {
  final TextEditingController _query = TextEditingController();
  String _standard = 'Todas';

  @override
  void dispose() {
    _query.dispose();
    super.dispose();
  }

  List<Map<String, String>> get _items => OfflineSstDeepCatalog.browse(
        standard: _standard,
        search: _query.text,
        limit: 500,
      );

  Future<void> _showModel(Map<String, String> item) async {
    final title = item['title'] ?? '';
    final nr = item['nr'] ?? '';
    final description = item['description'] ?? '';
    final risk = item['risk'] ?? '';
    final consequence = item['possibleConsequence'] ?? '';
    final recommendation = item['recommendation'] ?? '';
    final priority = item['priority'] ?? '';
    final onlyBrowse = item['browseOnly'] == 'true';
    final clipboardText = [
      '$nr — $title',
      if (description.isNotEmpty) 'Situação: $description',
      if (risk.isNotEmpty) 'Risco: $risk',
      if (consequence.isNotEmpty) 'Possível consequência: $consequence',
      if (recommendation.isNotEmpty) 'Recomendação: $recommendation',
    ].join('\n\n');

    await showDialog<void>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: Text(title),
        content: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text('$nr • Prioridade orientativa: $priority',
                  style: const TextStyle(fontWeight: FontWeight.w700)),
              if (description.isNotEmpty) ...[
                const SizedBox(height: 12),
                const Text('Situação para conferência',
                    style: TextStyle(fontWeight: FontWeight.bold)),
                Text(description),
              ],
              if (risk.isNotEmpty) ...[
                const SizedBox(height: 10),
                const Text('Risco',
                    style: TextStyle(fontWeight: FontWeight.bold)),
                Text(risk),
              ],
              if (consequence.isNotEmpty) ...[
                const SizedBox(height: 10),
                const Text('Possível consequência',
                    style: TextStyle(fontWeight: FontWeight.bold)),
                Text(consequence),
              ],
              if (recommendation.isNotEmpty) ...[
                const SizedBox(height: 10),
                const Text('Recomendação sugerida',
                    style: TextStyle(fontWeight: FontWeight.bold)),
                Text(recommendation),
              ],
              const SizedBox(height: 12),
              Text(
                onlyBrowse
                    ? 'Consulta técnica: não estabelece insalubridade, '
                      'periculosidade, interdição, embargo ou penalidade.'
                    : 'Modelo orientativo. Confirme a situação no local e '
                      'adapte o texto antes de registrar qualquer ocorrência.',
                style: const TextStyle(fontSize: 12),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(),
            child: const Text('Fechar'),
          ),
          TextButton.icon(
            onPressed: () async {
              await Clipboard.setData(ClipboardData(text: clipboardText));
              if (dialogContext.mounted) {
                Navigator.of(dialogContext).pop();
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Texto copiado para revisão.')),
                );
              }
            },
            icon: const Icon(Icons.copy_outlined),
            label: const Text('Copiar texto'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final results = _items;
    final choices = <String>[
      'Todas',
      'Panificação',
      ...OfflineSstAllNrsCatalog.activeStandards,
    ];
    return Scaffold(
      appBar: AppBar(title: const Text('Biblioteca técnica por NR')),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(12, 12, 12, 0),
          child: Column(
            children: [
              Text(
                'Modelos técnicos disponíveis offline',
                style: Theme.of(context).textTheme.titleMedium
                    ?.copyWith(fontWeight: FontWeight.w800),
              ),
              const SizedBox(height: 4),
              const Text(
                'Estes modelos vêm instalados no aplicativo e funcionam '
                'sem internet. Para receber novos modelos embarcados, '
                'é preciso instalar uma versão atualizada do Auditar SST.',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 12),
              ),
              const SizedBox(height: 4),
              const Text(
                'Modelos compartilhados pela Central usam o cache e a '
                'sincronização próprios. Uma atualização da Central não '
                'substitui os arquivos offline desta instalação.',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 12),
              ),
              const SizedBox(height: 10),
              DropdownButtonFormField<String>(
                value: _standard,
                isExpanded: true,
                decoration: const InputDecoration(
                  border: OutlineInputBorder(),
                  labelText: 'Norma ou segmento',
                ),
                items: [
                  for (final nr in choices)
                    DropdownMenuItem(value: nr, child: Text(nr)),
                ],
                onChanged: (nr) {
                  if (nr != null) setState(() => _standard = nr);
                },
              ),
              const SizedBox(height: 10),
              TextField(
                controller: _query,
                onChanged: (_) => setState(() {}),
                decoration: InputDecoration(
                  border: const OutlineInputBorder(),
                  prefixIcon: const Icon(Icons.search),
                  labelText: 'Pesquisar máquina, risco ou situação',
                  suffixIcon: _query.text.isEmpty
                      ? null
                      : IconButton(
                          tooltip: 'Limpar pesquisa',
                          onPressed: () {
                            _query.clear();
                            setState(() {});
                          },
                          icon: const Icon(Icons.close),
                        ),
                ),
              ),
              const SizedBox(height: 8),
              Align(
                alignment: Alignment.centerLeft,
                child: Text(
                  'Opções encontradas: ${results.length}',
                  style: const TextStyle(fontSize: 12.5,
                      fontWeight: FontWeight.w700),
                ),
              ),
              const SizedBox(height: 6),
              Expanded(
                child: results.isEmpty
                    ? const Center(
                        child: Text('Nenhum modelo encontrado. '
                            'Tente outra palavra ou norma.'),
                      )
                    : ListView.builder(
                        itemCount: results.length,
                        itemBuilder: (context, index) {
                          final model = results[index];
                          return Card(
                            margin: const EdgeInsets.only(bottom: 7),
                            child: ListTile(
                              key: ValueKey('nr-model-${model['id']}'),
                              title: Text(model['title'] ?? ''),
                              subtitle: Text(
                                (model['nr'] ?? '') +
                                    (model['browseOnly'] == 'true'
                                        ? ' • Apenas consulta técnica'
                                        : ' • ${model['priority'] ?? ''}'),
                              ),
                              trailing: const Icon(Icons.chevron_right),
                              onTap: () => _showModel(model),
                            ),
                          );
                        },
                      ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
