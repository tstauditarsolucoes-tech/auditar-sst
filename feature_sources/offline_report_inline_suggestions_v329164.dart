import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:path_provider/path_provider.dart';

class OfflineInlineSuggestion {
  const OfflineInlineSuggestion({
    required this.id,
    required this.title,
    required this.description,
    required this.risk,
    required this.possibleConsequence,
    required this.recommendation,
    required this.priority,
    required this.source,
    this.useCount = 0,
  });

  final String id;
  final String title;
  final String description;
  final String risk;
  final String possibleConsequence;
  final String recommendation;
  final String priority;
  final String source;
  final int useCount;

  bool get learned =>
      source.contains('approved') ||
      source.contains('manual') ||
      source.contains('learn');

  String get sourceLabel {
    if (source.contains('ai_approved')) return 'IA revisada';
    if (source.contains('manual') || source.contains('learn')) {
      return 'Aprendido no uso';
    }
    return 'Base Auditar';
  }
}

class OfflineReportInlineSuggestionService {
  static const _fileName = 'offline_report_knowledge_v1.json';

  static Future<List<OfflineInlineSuggestion>> search({
    required String query,
    List<String> contextTerms = const [],
    int limit = 3,
  }) async {
    final normalized = _normalize(query);
    if (normalized.length < 3) return const [];

    final all = <OfflineInlineSuggestion>[..._fallback];
    try {
      final dir = await getApplicationSupportDirectory();
      final file = File('${dir.path}/$_fileName');
      if (await file.exists()) {
        final decoded = jsonDecode(await file.readAsString());
        for (final map in _extractTemplateMaps(decoded)) {
          final item = _fromMap(map);
          if (item != null) all.add(item);
        }
      }
    } catch (_) {
      // Sugestões locais nunca podem bloquear a vistoria.
    }

    final deduped = <String, OfflineInlineSuggestion>{};
    for (final item in all) {
      final key = '${_normalize(item.title)}|${_normalize(item.description)}';
      final current = deduped[key];
      if (current == null || item.useCount > current.useCount || item.learned) {
        deduped[key] = item;
      }
    }

    final context = _normalize(contextTerms.where((e) => e.trim().isNotEmpty).join(' '));
    final ranked = deduped.values
        .map((item) => (item: item, score: _score(item, normalized, context)))
        .where((entry) => entry.score > 0)
        .toList()
      ..sort((a, b) {
        final score = b.score.compareTo(a.score);
        if (score != 0) return score;
        final used = b.item.useCount.compareTo(a.item.useCount);
        if (used != 0) return used;
        return a.item.title.compareTo(b.item.title);
      });

    return ranked.take(limit).map((entry) => entry.item).toList();
  }

  static List<Map<String, dynamic>> _extractTemplateMaps(dynamic value) {
    final out = <Map<String, dynamic>>[];

    void walk(dynamic node) {
      if (node is List) {
        for (final item in node) {
          walk(item);
        }
        return;
      }
      if (node is! Map) return;
      final map = <String, dynamic>{};
      for (final entry in node.entries) {
        map['${entry.key}'] = entry.value;
      }
      final title = '${map['title'] ?? ''}'.trim();
      if (title.isNotEmpty &&
          (map.containsKey('description') ||
              map.containsKey('risk') ||
              map.containsKey('recommendation'))) {
        out.add(map);
      }
      for (final child in map.values) {
        if (child is List || child is Map) walk(child);
      }
    }

    walk(value);
    return out;
  }

  static OfflineInlineSuggestion? _fromMap(Map<String, dynamic> map) {
    final title = '${map['title'] ?? ''}'.trim();
    if (title.isEmpty) return null;

    String text(String key) => '${map[key] ?? ''}'.trim();
    int integer(String key) {
      final raw = map[key];
      if (raw is int) return raw;
      return int.tryParse('${raw ?? ''}') ?? 0;
    }

    final rawPriority = text('priority');
    final priority = const ['Baixa', 'Média', 'Alta', 'Crítica'].contains(rawPriority)
        ? rawPriority
        : 'Média';

    return OfflineInlineSuggestion(
      id: text('id').isEmpty ? 'local-${_normalize(title).hashCode}' : text('id'),
      title: title,
      description: text('description'),
      risk: text('risk'),
      possibleConsequence: text('possibleConsequence'),
      recommendation: text('recommendation'),
      priority: priority,
      source: text('source').isEmpty ? 'local_approved' : text('source'),
      useCount: [
        integer('useCount'),
        integer('usedCount'),
        integer('usageCount'),
      ].reduce((a, b) => a > b ? a : b),
    );
  }

  static const Set<String> _noiseTokens = {
    'a', 'ao', 'aos', 'as', 'com', 'da', 'das', 'de', 'do', 'dos', 'e', 'em',
    'esta', 'estava', 'foi', 'na', 'nas', 'no', 'nos', 'o', 'os', 'para', 'por',
    'que', 'um', 'uma', 'nao', 'sem', 'funciona', 'funcionou', 'funcionando',
    'funcionamento', 'inoperante', 'defeito', 'falha', 'falhou', 'emergencia',
  };

  static Set<String> _concepts(String value) {
    final text = _normalize(value);
    final found = <String>{};

    bool hasAny(Iterable<String> terms) =>
        terms.any((term) => text.contains(term));

    if (hasAny(const [
      'botao',
      'botoeira',
      'parada de emergencia',
      'comando de emergencia',
    ])) {
      found.add('machine_control');
    }
    if (hasAny(const ['extintor', 'combate a incendio'])) {
      found.add('extinguisher');
    }
    if (hasAny(const ['sensor', 'intertravamento', 'chave de seguranca'])) {
      found.add('sensor');
    }
    if (hasAny(const ['painel eletrico', 'fiacao', 'condutor eletrico'])) {
      found.add('electrical');
    }
    if (hasAny(const ['epi', 'capacete', 'luva', 'oculos', 'protetor auricular'])) {
      found.add('ppe');
    }
    if (hasAny(const ['guarda corpo', 'queda', 'trabalho em altura'])) {
      found.add('fall');
    }
    return found;
  }

  static Set<String> _usefulTokens(String normalized) => normalized
      .split(' ')
      .where((token) => token.length >= 3 && !_noiseTokens.contains(token))
      .toSet();

  static double _score(
    OfflineInlineSuggestion item,
    String query,
    String context,
  ) {
    final title = _normalize(item.title);
    final description = _normalize(item.description);
    final risk = _normalize(item.risk);
    final recommendation = _normalize(item.recommendation);
    final tokens = _usefulTokens(query);
    final queryConcepts = _concepts(query);
    final itemConcepts = _concepts(
      '${item.title} ${item.description} ${item.risk} ${item.recommendation}',
    );

    var score = 0.0;

    if (title == query) score += 40;
    if (query.length >= 8 && title.contains(query)) score += 28;
    if (query.length >= 8 && description.contains(query)) score += 14;

    for (final token in tokens) {
      if (title.split(' ').contains(token)) {
        score += 9;
      } else if (title.contains(token)) {
        score += 6;
      }
      if (description.contains(token)) score += 3;
      if (risk.contains(token)) score += 1.5;
      if (recommendation.contains(token)) score += 1.5;
    }

    if (queryConcepts.isNotEmpty) {
      final common = queryConcepts.intersection(itemConcepts);
      if (common.isNotEmpty) {
        score += 22 * common.length;
      } else if (itemConcepts.isNotEmpty) {
        score -= 24;
      }
    }

    if (context.isNotEmpty) {
      final contextTokens = _usefulTokens(context);
      for (final token in contextTokens) {
        if (title.contains(token) || description.contains(token)) {
          score += 0.5;
        }
      }
    }

    score += (item.useCount.clamp(0, 20)) * 0.15;
    if (item.learned) score += 0.75;

    // Evita exibir modelos ligados apenas por palavras genéricas.
    if (tokens.isEmpty && queryConcepts.isEmpty) return 0;
    return score >= 6 ? score : 0;
  }

  static String _normalize(String value) {
    var text = value.toLowerCase().trim();
    const accents = <String, String>{
      'á': 'a',
      'à': 'a',
      'â': 'a',
      'ã': 'a',
      'ä': 'a',
      'é': 'e',
      'è': 'e',
      'ê': 'e',
      'ë': 'e',
      'í': 'i',
      'ì': 'i',
      'î': 'i',
      'ï': 'i',
      'ó': 'o',
      'ò': 'o',
      'ô': 'o',
      'õ': 'o',
      'ö': 'o',
      'ú': 'u',
      'ù': 'u',
      'û': 'u',
      'ü': 'u',
      'ç': 'c',
    };
    accents.forEach((from, to) => text = text.replaceAll(from, to));
    return text
        .replaceAll(RegExp(r'[^a-z0-9]+'), ' ')
        .replaceAll(RegExp(r'\s+'), ' ')
        .trim();
  }

  static List<OfflineInlineSuggestion> get fallbackForTesting => _fallback;

  static List<OfflineInlineSuggestion> rankForTesting(String query) {
    final normalized = _normalize(query);
    final ranked = _fallback
        .map((item) => (item: item, score: _score(item, normalized, '')))
        .where((entry) => entry.score > 0)
        .toList()
      ..sort((a, b) => b.score.compareTo(a.score));
    return ranked.map((entry) => entry.item).toList();
  }

  static List<OfflineInlineSuggestion> decodeAndRankForTesting(
    String raw,
    String query,
  ) {
    final decoded = jsonDecode(raw);
    final items = _extractTemplateMaps(decoded)
        .map(_fromMap)
        .whereType<OfflineInlineSuggestion>()
        .toList();
    final normalized = _normalize(query);
    final ranked = items
        .map((item) => (item: item, score: _score(item, normalized, '')))
        .where((entry) => entry.score > 0)
        .toList()
      ..sort((a, b) => b.score.compareTo(a.score));
    return ranked.map((entry) => entry.item).toList();
  }

  static const _fallback = <OfflineInlineSuggestion>[
    OfflineInlineSuggestion(
      id: 'auditar-extintor-sem-sinalizacao',
      title: 'Extintor sem placa de identificação',
      description:
          'Extintor sem placa de sinalização vertical identificando sua localização.',
      risk:
          'Dificuldade de localizar o equipamento rapidamente em uma situação de emergência.',
      possibleConsequence:
          'Atraso no acesso ao equipamento durante uma emergência.',
      recommendation:
          'Instalar placa de identificação do extintor em posição visível e manter o acesso livre.',
      priority: 'Alta',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-extintor-obstruido',
      title: 'Extintor com acesso obstruído',
      description:
          'Foi identificada obstrução no acesso ao extintor, dificultando sua pronta utilização.',
      risk:
          'Dificuldade ou atraso no acesso ao equipamento em uma situação de emergência.',
      possibleConsequence:
          'Comprometimento da resposta inicial em princípio de incêndio.',
      recommendation:
          'Desobstruir imediatamente a área e manter permanentemente livre o acesso ao extintor.',
      priority: 'Alta',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-extintor-vencido',
      title: 'Extintor com validade vencida',
      description:
          'Extintor identificado com prazo de validade ou manutenção vencido.',
      risk:
          'Possibilidade de indisponibilidade ou funcionamento inadequado do equipamento em emergência.',
      possibleConsequence:
          'Redução da eficiência da resposta a princípio de incêndio.',
      recommendation:
          'Providenciar inspeção, manutenção ou substituição do extintor e conferir sua liberação antes do retorno ao ponto.',
      priority: 'Alta',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-sensor-protecao-inoperante',
      title: 'Sensor de proteção sem funcionamento',
      description:
          'O sensor associado ao sistema de proteção não atuou durante o teste de funcionamento.',
      risk:
          'Possibilidade de acesso à zona de perigo sem atuação adequada do sistema de proteção.',
      possibleConsequence:
          'Aprisionamento, esmagamento ou contato com partes perigosas em movimento.',
      recommendation:
          'Suspender o uso quando o sensor integrar função de segurança, solicitar reparo e testar o sistema antes da liberação.',
      priority: 'Crítica',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-botao-emergencia-inoperante',
      title: 'Botão de emergência inoperante',
      description:
          'Durante o teste, o botão de parada de emergência não atuou conforme esperado.',
      risk:
          'Impossibilidade ou atraso na parada imediata da máquina em uma situação de perigo.',
      possibleConsequence:
          'Agravamento de acidente por impossibilidade de interromper rapidamente o movimento perigoso.',
      recommendation:
          'Interromper a operação quando a função de parada de emergência estiver inoperante, solicitar reparo e testar o dispositivo antes da liberação da máquina.',
      priority: 'Crítica',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-botoeira-inoperante',
      title: 'Botoeira de comando sem funcionamento',
      description:
          'A botoeira de comando não respondeu ao acionamento durante a verificação.',
      risk:
          'Falha no comando do equipamento, podendo comprometer o controle seguro da operação.',
      possibleConsequence:
          'Dificuldade de interrupção ou controle do equipamento durante a operação.',
      recommendation:
          'Solicitar avaliação e reparo pela manutenção e testar o comando antes da liberação do equipamento.',
      priority: 'Alta',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-painel-eletrico-aberto',
      title: 'Painel elétrico aberto',
      description:
          'Painel encontrado aberto, com componentes internos acessíveis.',
      risk:
          'Possibilidade de contato acidental com componentes energizados e choque elétrico.',
      possibleConsequence:
          'Choque elétrico, queimaduras ou ocorrência de acidente grave.',
      recommendation:
          'Restringir o acesso e solicitar avaliação por profissional autorizado, regularizando o fechamento e a proteção do painel.',
      priority: 'Crítica',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-protecao-maquina-ausente',
      title: 'Proteção de máquina ausente ou removida',
      description:
          'Foi identificada ausência ou remoção de proteção em área com acesso a partes perigosas da máquina.',
      risk:
          'Contato com partes móveis, pontos de esmagamento, corte ou aprisionamento.',
      possibleConsequence:
          'Lesões graves por contato com componentes em movimento.',
      recommendation:
          'Interromper a condição insegura, reinstalar ou adequar a proteção e testar o equipamento antes da liberação.',
      priority: 'Crítica',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-epi-nao-utilizado',
      title: 'Trabalhador sem utilização do EPI previsto',
      description:
          'Foi observada execução ou circulação em área de risco sem utilização do EPI previsto para a atividade.',
      risk:
          'Exposição do trabalhador ao agente ou perigo existente sem a proteção prevista.',
      possibleConsequence:
          'Aumento da possibilidade de lesão ou agravo relacionado à exposição.',
      recommendation:
          'Orientar o trabalhador, regularizar o uso do EPI adequado e reforçar a supervisão do cumprimento das medidas de proteção.',
      priority: 'Alta',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-guarda-corpo-ausente',
      title: 'Proteção contra queda ausente',
      description:
          'Foi identificada área com risco de queda sem proteção coletiva adequada.',
      risk:
          'Queda de trabalhador para nível inferior.',
      possibleConsequence:
          'Traumas graves ou acidente fatal.',
      recommendation:
          'Restringir o acesso até a instalação ou regularização da proteção coletiva adequada.',
      priority: 'Crítica',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-fiacao-exposta',
      title: 'Fiação ou componentes elétricos expostos',
      description:
          'Foram identificados condutores ou componentes elétricos acessíveis sem proteção adequada.',
      risk:
          'Contato acidental com partes energizadas.',
      possibleConsequence:
          'Choque elétrico, queimaduras ou acidente grave.',
      recommendation:
          'Isolar a condição e solicitar regularização por profissional autorizado antes da liberação.',
      priority: 'Crítica',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-organizacao-inadequada',
      title: 'Organização inadequada da área',
      description:
          'Foram identificados materiais ou objetos dispostos de forma inadequada na área de trabalho.',
      risk:
          'Tropeços, quedas, dificuldade de circulação ou interferência na execução segura das atividades.',
      possibleConsequence:
          'Quedas, colisões ou outros acidentes durante a circulação e o trabalho.',
      recommendation:
          'Organizar a área, definir locais adequados para armazenamento e manter as rotas de circulação livres.',
      priority: 'Média',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-maquina-sem-identificacao',
      title: 'Máquina sem identificação',
      description:
          'Máquina ou equipamento encontrado sem identificação visível para reconhecimento e controle.',
      risk:
          'Dificuldade de identificação, rastreabilidade e controle das condições do equipamento.',
      possibleConsequence:
          'Falhas de controle e manutenção do equipamento.',
      recommendation:
          'Providenciar identificação visível e compatível com o controle interno adotado para máquinas e equipamentos.',
      priority: 'Média',
      source: 'auditar_seed',
    ),
  ];
}

class OfflineReportInlineSuggestions extends StatelessWidget {
  const OfflineReportInlineSuggestions({
    super.key,
    required this.query,
    required this.onSelected,
    this.contextTerms = const [],
  });

  final String query;
  final List<String> contextTerms;
  final ValueChanged<OfflineInlineSuggestion> onSelected;

  Widget _row(
    BuildContext context,
    OfflineInlineSuggestion item, {
    bool compact = false,
  }) {
    final theme = Theme.of(context);
    return InkWell(
      borderRadius: BorderRadius.circular(10),
      onTap: () => onSelected(item),
      child: Padding(
        padding: EdgeInsets.symmetric(
          horizontal: 10,
          vertical: compact ? 8 : 10,
        ),
        child: Row(
          children: [
            Icon(
              item.learned ? Icons.history_rounded : Icons.auto_fix_high_outlined,
              size: 18,
              color: theme.colorScheme.primary,
            ),
            const SizedBox(width: 9),
            Expanded(
              child: Text(
                item.title,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: theme.textTheme.bodyMedium?.copyWith(
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
            const SizedBox(width: 6),
            const Icon(Icons.chevron_right_rounded, size: 18),
          ],
        ),
      ),
    );
  }

  Future<void> _showMore(
    BuildContext context,
    List<OfflineInlineSuggestion> items,
  ) async {
    await showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      isScrollControlled: true,
      builder: (sheetContext) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(12, 0, 12, 18),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Padding(
                padding: EdgeInsets.fromLTRB(8, 2, 8, 8),
                child: Text(
                  'Outras sugestões locais',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.w800),
                ),
              ),
              ...items.map(
                (item) => Card(
                  elevation: 0,
                  margin: const EdgeInsets.only(bottom: 6),
                  child: _row(sheetContext, item),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (query.trim().length < 3) return const SizedBox.shrink();

    return FutureBuilder<List<OfflineInlineSuggestion>>(
      future: OfflineReportInlineSuggestionService.search(
        query: query,
        contextTerms: contextTerms,
      ),
      builder: (context, snapshot) {
        final items = snapshot.data ?? const <OfflineInlineSuggestion>[];
        if (items.isEmpty) return const SizedBox.shrink();

        final theme = Theme.of(context);
        final visible = items.take(2).toList(growable: false);
        final hidden = items.skip(2).toList(growable: false);

        return Padding(
          padding: const EdgeInsets.only(top: 8),
          child: Container(
            width: double.infinity,
            padding: const EdgeInsets.fromLTRB(10, 9, 10, 8),
            decoration: BoxDecoration(
              color: theme.colorScheme.surfaceContainerHighest.withValues(
                alpha: 0.35,
              ),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: theme.colorScheme.outlineVariant),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Icon(Icons.offline_bolt_outlined, size: 18),
                    const SizedBox(width: 6),
                    Expanded(
                      child: Text(
                        'Sugestões mais próximas',
                        style: theme.textTheme.labelLarge?.copyWith(
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                    ),
                    Text(
                      'sem internet',
                      style: theme.textTheme.labelSmall?.copyWith(
                        color: theme.colorScheme.primary,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 5),
                for (var index = 0; index < visible.length; index++) ...[
                  if (index > 0) const Divider(height: 1),
                  _row(context, visible[index], compact: true),
                ],
                if (hidden.isNotEmpty)
                  Align(
                    alignment: Alignment.centerLeft,
                    child: TextButton.icon(
                      onPressed: () => _showMore(context, hidden),
                      icon: const Icon(Icons.expand_more_rounded, size: 18),
                      label: Text('Ver mais ${hidden.length}'),
                    ),
                  ),
              ],
            ),
          ),
        );
      },
    );
  }
}

