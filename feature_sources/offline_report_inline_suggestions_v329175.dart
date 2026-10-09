import '../services/offline_reasoning.dart';
import 'dart:async';
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
    this.assessment,
    this.reviewed = false,
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
  final OfflineAssessment? assessment;
  final bool reviewed;

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
  static const _learnedCacheTtl = Duration(seconds: 8);
  static List<OfflineInlineSuggestion>? _learnedCache;
  static DateTime? _learnedCacheAt;

  static Future<List<OfflineInlineSuggestion>> _learnedSuggestions() async {
    final now = DateTime.now();
    final cached = _learnedCache;
    final cachedAt = _learnedCacheAt;
    if (cached != null &&
        cachedAt != null &&
        now.difference(cachedAt) < _learnedCacheTtl) {
      return cached;
    }

    final learned = <OfflineInlineSuggestion>[];
    try {
      final dir = await getApplicationSupportDirectory();
      for (final path in ['${dir.path}/$_fileName', '${dir.path}/auditar_sst/offline_report_knowledge/$_fileName', '${dir.path}/offline_reasoning_learning_v1.json']) {
      try {
      final file = File(path);
      if (await file.exists()) {
        final decoded = jsonDecode(await file.readAsString());
        for (final map in _extractTemplateMaps(decoded)) {
          final item = _fromMap(map);
          if (item != null) learned.add(item);
        }
      }
      } catch (_) { /* Um arquivo inválido não bloqueia a outra biblioteca. */ }
      }
    } catch (_) {
      // A biblioteca local nunca pode bloquear a vistoria.
    }
    _learnedCache = List.unmodifiable(learned);
    _learnedCacheAt = now;
    return _learnedCache!;
  }

  static void invalidateLearnedCache() { _learnedCache = null; _learnedCacheAt = null; }

  static Future<void> _learningQueue = Future<void>.value();

  // A separate local file preserves the previous library and stores the latest
  // applied correction exactly, including shorter wording. No network involved.
  static Future<String?> learnApplied(OfflineInlineSuggestion item) async {
    String clean(String text) => text.trim().replaceAll(
      RegExp(r'\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b'), '');
    final title=clean(item.title);
    if(title.length < 4) return null;
    final key='${item.assessment?.rule.id ?? 'model'}|${_normalize(title)}';
    final id='auto-${base64Url.encode(utf8.encode(key)).replaceAll('=', '')}';
    final operation = _learningQueue.catchError((_) {}).then((_) async {
      final dir=await getApplicationSupportDirectory();
      final file=File('${dir.path}/offline_reasoning_learning_v1.json');
      final old=await file.exists() ? _extractTemplateMaps(jsonDecode(await file.readAsString())) : <Map<String,dynamic>>[];
      final previous=old.where((m)=>m['id']==id).firstOrNull;
      final count=int.tryParse('${previous?['useCount'] ?? 0}') ?? 0;
      final map=<String,dynamic>{'id':id,'title':title,
        'description':clean(item.assessment?.reusableDescription ?? item.title),
        'risk':clean(item.risk),'possibleConsequence':clean(item.possibleConsequence),
        'recommendation':clean(item.recommendation),'priority':item.priority,
        'source':'manual_auto_approved','useCount':count+1,
        'updatedAt':DateTime.now().toIso8601String()};
      await dir.create(recursive:true);
      final temporary=File('${file.path}.tmp');
      await temporary.writeAsString(jsonEncode({'schemaVersion':1,'templates':[map,...old.where((m)=>m['id']!=id)].take(500).toList()}),flush:true);
      await temporary.rename(file.path);
      invalidateLearnedCache();
    });
    _learningQueue=operation;
    await operation;
    return id;
  }

  static Future<List<OfflineInlineSuggestion>> search({
    required String query,
    List<String> contextTerms = const [],
    int limit = 3,
  }) async {
    final normalized = _normalize(OfflineReasoning.normalize(query));
    if (normalized.length < 3 || query.length > 3000 || limit <= 0) return const [];
    final assessments = OfflineReasoning.analyze(query, context: contextTerms);
    if (assessments.isNotEmpty) {
      final learned = await _learnedSuggestions();
      final results = <OfflineInlineSuggestion>[];
      for (final a in assessments) {
        results.add(OfflineInlineSuggestion(id: 'rule-${a.rule.id}', title: a.rule.title,
          description: a.description, risk: a.rule.risk, possibleConsequence: a.rule.consequence,
          recommendation: a.rule.action, priority: 'Alta', source: 'auditar_rule', assessment: a));
        for (final item in learned.where((i) => i.learned)) {
          if (OfflineReasoning.analyze('${item.title}. ${item.description}').any((v) => v.rule.id == a.rule.id)) {
            results.add(OfflineInlineSuggestion(id: item.id, title: item.title, description: a.description,
              risk: item.risk, possibleConsequence: item.possibleConsequence, recommendation: item.recommendation,
              priority: item.priority, source: item.source, useCount: item.useCount, assessment: a));
          }
        }
      }
      results.sort((a,b) {
        final learned = (b.learned ? 1 : 0).compareTo(a.learned ? 1 : 0);
        return learned != 0 ? learned : b.useCount.compareTo(a.useCount);
      });
      final unique = <String, OfflineInlineSuggestion>{};
      for (final item in results) { unique.putIfAbsent(item.id, () => item); }
      return unique.values.take(limit).toList();
    }
    if (OfflineReasoning.explicitSafeOrUncertain(query)) return const [];
    // Equipamentos com regras de falha explícitas não podem gerar uma
    // "não conformidade" baseada apenas na coincidência do nome.
    if (OfflineReasoning.has(
        'extintor|botao|botoeira|sensor|andaime',
        OfflineReasoning.normalize(query))) {
      return const [];
    }

    final all = <OfflineInlineSuggestion>[
      ..._fallback,
      ...await _learnedSuggestions(),
    ];

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
      'botao', 'botoeira', 'parada de emergencia', 'comando de emergencia',
    ])) found.add('machine_control');
    if (hasAny(const [
      'sensor', 'intertravamento', 'chave de seguranca', 'micro switch',
    ])) found.add('sensor');
    if (hasAny(const [
      'protecao de maquina', 'proteção de máquina', 'carter', 'grade de protecao',
      'parte movel', 'zona de perigo', 'polia', 'correia', 'engrenagem',
    ])) found.add('machine_guard');
    if (hasAny(const [
      'extintor', 'hidrante', 'combate a incendio', 'rota de fuga',
    ])) found.add('fire');
    if (hasAny(const [
      'painel eletrico', 'fiacao', 'condutor eletrico', 'cabo eletrico',
      'tomada', 'plugue', 'aterramento', 'choque',
    ])) found.add('electrical');
    if (hasAny(const [
      'epi', 'capacete', 'luva', 'oculos', 'protetor auricular',
      'respirador', 'mascara', 'botina', 'perneira', 'avental',
    ])) found.add('ppe');
    if (hasAny(const [
      'respirador', 'mascara', 'protecao respiratoria', 'proteção respiratória',
    ])) found.add('respiratory_ppe');
    if (hasAny(const [
      'protetor auricular', 'abafador', 'protecao auditiva', 'proteção auditiva',
    ])) found.add('hearing_ppe');
    if (hasAny(const [
      'guarda corpo', 'queda de nivel', 'trabalho em altura', 'linha de vida',
      'ancoragem', 'cinto paraquedista', 'telhado',
    ])) found.add('fall');
    if (hasAny(const ['andaime', 'plataforma de trabalho'])) {
      found.add('scaffold');
    }
    if (hasAny(const ['escada', 'escada portatil', 'escada de acesso'])) {
      found.add('ladder');
    }
    if (hasAny(const [
      'inflamavel', 'combustivel', 'gasolina', 'diesel', 'glp', 'solvente',
    ])) found.add('flammable');
    if (hasAny(const [
      'produto quimico', 'quimico', 'rotulo', 'fispq', 'ficha de seguranca',
      'recipiente sem identificacao',
    ])) found.add('chemical');
    if (hasAny(const ['ruido', 'barulho', 'protetor auricular'])) {
      found.add('noise');
    }
    if (hasAny(const ['calor', 'estresse termico', 'temperatura elevada'])) {
      found.add('heat');
    }
    if (hasAny(const ['poeira', 'particulado', 'fumaca', 'fumo metalico'])) {
      found.add('airborne');
    }
    if (hasAny(const [
      'ergonomia', 'postura', 'levantamento manual', 'peso', 'repetitiv',
      'sobrecarga', 'movimentacao manual',
    ])) found.add('ergonomics');
    if (hasAny(const [
      'empilhadeira', 'empilhamento', 'armazenamento', 'pallet', 'carga',
      'movimentacao de materiais',
    ])) found.add('material_handling');
    if (hasAny(const [
      'organizacao', 'obstrucao', 'corredor', 'passagem', 'piso molhado',
      'buraco', 'canaleta', 'tropeco', 'queda mesmo nivel',
    ])) found.add('housekeeping');
    if (hasAny(const [
      'banheiro', 'sanitario', 'refeitorio', 'vestiario', 'agua potavel',
    ])) found.add('sanitary');
    if (hasAny(const [
      'sinalizacao', 'placa', 'demarcacao', 'identificacao',
    ])) found.add('signage');
    if (hasAny(const ['espaco confinado', 'tanque', 'silo'])) {
      found.add('confined');
    }
    if (hasAny(const [
      'compressor', 'vaso de pressao', 'caldeira', 'tubulacao pressurizada',
    ])) found.add('pressure');
    if (hasAny(const [
      'saida de emergencia', 'rota de fuga', 'porta corta fogo',
      'iluminacao de emergencia',
    ])) found.add('emergency_route');
    if (hasAny(const ['empilhadeira', 'transpaleteira', 'paleteira'])) {
      found.add('forklift');
    }
    if (hasAny(const [
      'talha', 'gancho', 'cinta de elevacao', 'linga', 'cabo de aco',
      'carga suspensa', 'ponte rolante', 'munck',
    ])) found.add('lifting');
    if (hasAny(const ['solda', 'soldagem', 'trabalho a quente', 'fagulha'])) {
      found.add('hot_work');
    }
    if (hasAny(const ['escavacao', 'vala', 'talude', 'escoramento'])) {
      found.add('excavation');
    }
    if (hasAny(const [
      'esmerilhadeira', 'lixadeira', 'serra circular', 'furadeira',
      'ferramenta eletrica',
    ])) found.add('portable_tool');
    if (hasAny(const ['primeiros socorros', 'kit de primeiros socorros'])) {
      found.add('first_aid');
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
      final contextConcepts = _concepts(context);
      final commonContext = contextConcepts.intersection(itemConcepts);
      if (commonContext.isNotEmpty) score += 4 * commonContext.length;
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
    OfflineInlineSuggestion(
      id: 'auditar-aterramento-ausente',
      title: 'Equipamento sem aterramento identificado',
      description:
          'Foi identificada ausência ou inadequação aparente do aterramento elétrico do equipamento.',
      risk:
          'Possibilidade de choque elétrico em caso de falha de isolação ou energização indevida da carcaça.',
      possibleConsequence:
          'Choque elétrico, queimaduras ou acidente grave.',
      recommendation:
          'Solicitar avaliação por profissional autorizado e regularizar o sistema de proteção e aterramento antes da liberação do equipamento.',
      priority: 'Crítica',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-cabo-eletrico-danificado',
      title: 'Cabo elétrico danificado ou com emenda inadequada',
      description:
          'Foram identificados danos, emendas improvisadas ou partes do cabo elétrico sem proteção adequada.',
      risk:
          'Contato com partes energizadas, curto-circuito e princípio de incêndio.',
      possibleConsequence:
          'Choque elétrico, queimaduras, incêndio ou interrupção da atividade.',
      recommendation:
          'Retirar o cabo da condição de uso e providenciar substituição ou reparo tecnicamente adequado por profissional autorizado.',
      priority: 'Crítica',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-extintor-pressao-irregular',
      title: 'Extintor com indicação de pressão irregular',
      description:
          'O indicador de pressão do extintor foi observado fora da condição normal de operação.',
      risk:
          'Possibilidade de funcionamento inadequado do equipamento em uma emergência.',
      possibleConsequence:
          'Redução da capacidade de resposta inicial a princípio de incêndio.',
      recommendation:
          'Retirar o equipamento para avaliação/manutenção e manter o ponto protegido com equipamento regularizado.',
      priority: 'Alta',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-extintor-sem-lacre',
      title: 'Extintor sem lacre ou com lacre violado',
      description:
          'Foi identificado extintor sem lacre de segurança ou com evidência de violação.',
      risk:
          'Incerteza quanto à integridade e condição de uso do equipamento.',
      possibleConsequence:
          'Falha ou indisponibilidade do equipamento durante emergência.',
      recommendation:
          'Providenciar avaliação do extintor por empresa habilitada e regularizar o equipamento antes de mantê-lo disponível para uso.',
      priority: 'Alta',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-escada-sem-corrimao',
      title: 'Escada fixa sem corrimão ou proteção adequada',
      description:
          'Foi identificada escada de circulação sem corrimão ou com proteção lateral insuficiente.',
      risk:
          'Perda de equilíbrio e queda durante subida ou descida.',
      possibleConsequence:
          'Contusões, fraturas ou lesões graves.',
      recommendation:
          'Providenciar corrimão e proteção compatível com a condição de circulação, restringindo o acesso quando houver risco relevante.',
      priority: 'Alta',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-andaime-sem-ancoragem',
      title: 'Andaime sem amarração ou ancoragem adequada',
      description:
          'Foi identificado andaime sem amarração, ancoragem ou estabilidade compatível com a condição de uso.',
      risk:
          'Tombamento da estrutura ou queda de trabalhador e materiais.',
      possibleConsequence:
          'Traumas graves ou acidente fatal.',
      recommendation:
          'Interromper o uso, regularizar montagem, estabilidade e proteções, e liberar somente após verificação das condições seguras.',
      priority: 'Crítica',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-andaime-sem-guarda-corpo',
      title: 'Andaime sem guarda-corpo ou proteção contra queda',
      description:
          'Foi identificada plataforma de andaime sem proteção coletiva adequada contra queda.',
      risk:
          'Queda de trabalhador para nível inferior.',
      possibleConsequence:
          'Traumas graves ou acidente fatal.',
      recommendation:
          'Suspender o uso até a instalação das proteções coletivas e demais requisitos aplicáveis ao trabalho em altura.',
      priority: 'Crítica',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-escada-portatil-inadequada',
      title: 'Escada portátil em condição inadequada',
      description:
          'A escada portátil apresenta condição de uso, posicionamento, apoio ou conservação inadequada.',
      risk:
          'Escorregamento, tombamento ou queda durante o acesso.',
      possibleConsequence:
          'Contusões, fraturas ou lesões graves.',
      recommendation:
          'Retirar a escada inadequada de uso, corrigir a condição e garantir apoio, conservação e utilização segura.',
      priority: 'Alta',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-combustivel-recipiente-inadequado',
      title: 'Combustível armazenado em recipiente inadequado',
      description:
          'Foi identificado combustível ou líquido inflamável armazenado em recipiente não adequado ou sem identificação.',
      risk:
          'Vazamento, geração de vapores inflamáveis e ignição acidental.',
      possibleConsequence:
          'Incêndio, queimaduras e danos materiais.',
      recommendation:
          'Transferir o produto para recipiente compatível, identificado e destinado ao armazenamento seguro, mantendo-o em local controlado.',
      priority: 'Crítica',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-quimico-sem-identificacao',
      title: 'Produto químico sem identificação',
      description:
          'Foi encontrado produto químico em recipiente sem identificação adequada do conteúdo e dos perigos.',
      risk:
          'Uso incorreto, mistura incompatível ou exposição sem conhecimento do perigo.',
      possibleConsequence:
          'Intoxicação, queimaduras químicas, reação perigosa ou contaminação.',
      recommendation:
          'Identificar corretamente o recipiente, manter informações de segurança disponíveis e orientar os trabalhadores sobre o manuseio.',
      priority: 'Alta',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-protetor-auricular-nao-utilizado',
      title: 'Protetor auricular não utilizado em área de ruído',
      description:
          'Foi observada permanência ou circulação em área com exposição a ruído sem utilização do protetor auricular previsto.',
      risk:
          'Exposição ocupacional ao ruído sem a proteção individual prevista.',
      possibleConsequence:
          'Danos auditivos, dificuldade de comunicação, fadiga e aumento do risco de acidentes.',
      recommendation:
          'Regularizar o uso do protetor auricular, reforçar orientação e supervisão e manter o controle da exposição ao ruído.',
      priority: 'Alta',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-poeira-sem-protecao',
      title: 'Exposição à poeira sem proteção adequada',
      description:
          'Foi observada exposição a poeira ou particulado sem controle ou proteção compatível com a atividade.',
      risk:
          'Inalação de partículas e contato com olhos e vias respiratórias.',
      possibleConsequence:
          'Irritação, desconforto respiratório e possíveis agravos relacionados à exposição.',
      recommendation:
          'Reavaliar os controles coletivos, limpeza e ventilação e garantir EPI respiratório adequado quando previsto na avaliação de risco.',
      priority: 'Alta',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-calor-excessivo',
      title: 'Exposição a calor em condição relevante',
      description:
          'Foi observada atividade com carga térmica ou proximidade de fonte de calor que requer avaliação e controle.',
      risk:
          'Sobrecarga térmica e desconforto durante a execução da atividade.',
      possibleConsequence:
          'Desidratação, exaustão térmica, redução da atenção e outros agravos relacionados ao calor.',
      recommendation:
          'Avaliar a exposição, revisar controles, pausas, hidratação e organização do trabalho conforme o resultado da avaliação ocupacional.',
      priority: 'Alta',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-postura-inadequada',
      title: 'Postura inadequada ou sobrecarga na movimentação manual',
      description:
          'Foi observada movimentação manual com postura desfavorável, esforço elevado ou organização inadequada da tarefa.',
      risk:
          'Sobrecarga musculoesquelética durante levantamento, transporte ou posicionamento de materiais.',
      possibleConsequence:
          'Dor, fadiga, distensão e possíveis agravos musculoesqueléticos.',
      recommendation:
          'Reorganizar o método, reduzir esforço e alcance, orientar a técnica de movimentação e avaliar necessidade de auxílio mecânico ou trabalho em dupla.',
      priority: 'Média',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-empilhamento-instavel',
      title: 'Empilhamento de materiais instável',
      description:
          'Foi identificado empilhamento com condição de estabilidade, alinhamento ou organização inadequada.',
      risk:
          'Queda de materiais, tombamento da pilha e atingimento de trabalhadores.',
      possibleConsequence:
          'Cortes, contusões, esmagamentos ou lesões graves.',
      recommendation:
          'Reorganizar o empilhamento em base estável, respeitar o método definido e manter área de circulação e afastamentos seguros.',
      priority: 'Alta',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-rota-obstruida',
      title: 'Rota de circulação ou acesso obstruído',
      description:
          'Foram identificados materiais ou objetos obstruindo circulação, acesso a equipamentos ou rota prevista.',
      risk:
          'Tropeços, colisões e dificuldade de deslocamento ou resposta a emergência.',
      possibleConsequence:
          'Quedas, contusões ou atraso na evacuação e no acesso a recursos de emergência.',
      recommendation:
          'Remover a obstrução e manter permanentemente livre e organizada a rota de circulação ou acesso.',
      priority: 'Alta',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-piso-molhado',
      title: 'Piso molhado ou escorregadio sem controle',
      description:
          'Foi identificada área com piso molhado, escorregadio ou contaminado sem controle imediato adequado.',
      risk:
          'Escorregamento e queda no mesmo nível.',
      possibleConsequence:
          'Contusões, entorses, fraturas ou outros traumas.',
      recommendation:
          'Eliminar a fonte, secar ou limpar a área e sinalizar temporariamente enquanto a condição persistir.',
      priority: 'Média',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-abertura-piso-sem-protecao',
      title: 'Abertura ou canaleta sem proteção',
      description:
          'Foi identificada abertura, canaleta ou descontinuidade no piso sem proteção ou isolamento adequado.',
      risk:
          'Tropeço, queda no mesmo nível ou queda em abertura.',
      possibleConsequence:
          'Contusões, entorses, fraturas ou lesões mais graves conforme a profundidade.',
      recommendation:
          'Proteger, tampar ou isolar a abertura de forma resistente e sinalizar até a regularização definitiva.',
      priority: 'Alta',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-refeitorio-inadequado',
      title: 'Condição inadequada em área de refeição',
      description:
          'Foi identificada condição de organização, higiene, conservação ou estrutura inadequada na área destinada às refeições.',
      risk:
          'Exposição a condições inadequadas de higiene e conforto durante as refeições.',
      possibleConsequence:
          'Desconforto, contaminação ou comprometimento das condições sanitárias do ambiente.',
      recommendation:
          'Regularizar as condições de higiene, conservação, organização e estrutura da área de refeição.',
      priority: 'Média',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-sinalizacao-ausente',
      title: 'Sinalização de segurança ausente ou insuficiente',
      description:
          'Foi identificada ausência, baixa visibilidade ou inadequação da sinalização necessária para orientação e advertência.',
      risk:
          'Falha de comunicação do perigo, acesso indevido ou comportamento incompatível com a área.',
      possibleConsequence:
          'Aumento da probabilidade de incidentes por falta de orientação visual.',
      recommendation:
          'Instalar ou corrigir a sinalização no ponto adequado, com boa visibilidade e coerência com o risco existente.',
      priority: 'Média',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-espaco-confinado-controle',
      title: 'Espaço confinado sem controle claramente identificado',
      description:
          'Foi identificada condição relacionada a espaço confinado sem evidência clara dos controles de acesso e autorização aplicáveis.',
      risk:
          'Entrada não autorizada e exposição a atmosfera perigosa ou outros riscos do espaço.',
      possibleConsequence:
          'Intoxicação, asfixia, queda, aprisionamento ou acidente fatal.',
      recommendation:
          'Restringir o acesso e verificar formalmente a caracterização, sinalização, autorização, avaliação atmosférica e controles aplicáveis antes de qualquer entrada.',
      priority: 'Crítica',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-vaso-pressao-identificacao',
      title: 'Equipamento pressurizado sem identificação ou controle visível',
      description:
          'Foi observado equipamento pressurizado sem identificação ou informação de controle facilmente verificável no ponto inspecionado.',
      risk:
          'Dificuldade de controle da integridade e das condições seguras de operação.',
      possibleConsequence:
          'Falha operacional, ruptura ou acidente grave conforme o equipamento e a pressão envolvida.',
      recommendation:
          'Encaminhar para verificação do responsável técnico e regularizar identificação, inspeções e controles aplicáveis ao equipamento.',
      priority: 'Alta',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-saida-emergencia-obstruida',
      title: 'Saída de emergência obstruída',
      description: 'Foi identificada obstrução no acesso ou passagem da saída de emergência.',
      risk: 'Dificuldade de abandono rápido e seguro da área.',
      possibleConsequence: 'Atraso na evacuação e maior exposição ao perigo.',
      recommendation: 'Desobstruir imediatamente a saída e manter a rota permanentemente livre e identificada.',
      priority: 'Crítica',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-saida-emergencia-sem-sinalizacao',
      title: 'Saída de emergência sem sinalização adequada',
      description: 'A saída de emergência não apresenta identificação visível ou suficiente.',
      risk: 'Dificuldade de orientação durante uma evacuação.',
      possibleConsequence: 'Atraso na saída e fluxo desorganizado.',
      recommendation: 'Instalar ou regularizar a sinalização da saída e da rota de fuga.',
      priority: 'Alta',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-iluminacao-emergencia-inoperante',
      title: 'Iluminação de emergência inoperante',
      description: 'O ponto de iluminação de emergência não funcionou durante a verificação.',
      risk: 'Redução da visibilidade em falta de energia ou evacuação.',
      possibleConsequence: 'Quedas, desorientação e atraso no abandono da área.',
      recommendation: 'Providenciar manutenção e testar o sistema antes da regularização.',
      priority: 'Alta',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-porta-corta-fogo-irregular',
      title: 'Porta corta-fogo com condição inadequada',
      description: 'A porta corta-fogo está bloqueada, travada aberta ou com fechamento comprometido.',
      risk: 'Perda da compartimentação contra fumaça e fogo.',
      possibleConsequence: 'Propagação de fumaça ou calor para outras áreas.',
      recommendation: 'Desobstruir e regularizar o fechamento e funcionamento da porta.',
      priority: 'Crítica',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-hidrante-obstruido',
      title: 'Hidrante com acesso obstruído',
      description: 'O acesso ao hidrante ou abrigo de mangueira está obstruído.',
      risk: 'Atraso no uso do sistema de combate a incêndio.',
      possibleConsequence: 'Comprometimento da resposta inicial à emergência.',
      recommendation: 'Desobstruir e manter livre a área necessária para utilização do hidrante.',
      priority: 'Alta',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-painel-eletrico-sem-identificacao',
      title: 'Painel elétrico sem identificação',
      description: 'O painel ou quadro elétrico não apresenta identificação funcional suficiente.',
      risk: 'Intervenção incorreta e dificuldade de resposta segura.',
      possibleConsequence: 'Choque, acionamento indevido ou atraso na desenergização.',
      recommendation: 'Identificar o painel e seus circuitos de forma legível e atualizada.',
      priority: 'Alta',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-painel-eletrico-obstruido',
      title: 'Painel elétrico com acesso obstruído',
      description: 'Materiais ou objetos dificultam o acesso ao painel elétrico.',
      risk: 'Dificuldade de desligamento rápido e acesso inseguro.',
      possibleConsequence: 'Atraso em emergência e maior exposição a risco elétrico.',
      recommendation: 'Desobstruir a área e manter espaço seguro de acesso ao painel.',
      priority: 'Alta',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-tomada-danificada',
      title: 'Tomada ou plugue danificado',
      description: 'Foi identificada tomada ou plugue com dano, folga ou partes acessíveis.',
      risk: 'Contato com partes energizadas, aquecimento ou curto-circuito.',
      possibleConsequence: 'Choque, queimaduras ou princípio de incêndio.',
      recommendation: 'Retirar o ponto de uso até reparo ou substituição adequada.',
      priority: 'Alta',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-extensao-improvisada',
      title: 'Extensão elétrica improvisada ou inadequada',
      description: 'Foi identificada extensão, emenda ou ligação provisória sem condição segura.',
      risk: 'Falha de isolação, aquecimento, choque ou curto-circuito.',
      possibleConsequence: 'Choque, queimaduras ou incêndio.',
      recommendation: 'Substituir por instalação ou extensão adequada à carga e ao ambiente.',
      priority: 'Alta',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-eletrica-area-molhada',
      title: 'Instalação elétrica exposta em área molhada',
      description: 'Há condição elétrica exposta ou inadequadamente protegida em área sujeita a umidade.',
      risk: 'Contato elétrico favorecido pela presença de água.',
      possibleConsequence: 'Choque elétrico grave ou fatal.',
      recommendation: 'Isolar a condição e providenciar adequação por profissional autorizado.',
      priority: 'Crítica',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-maquina-manutencao-energizada',
      title: 'Intervenção em máquina sem bloqueio seguro',
      description: 'Foi identificada intervenção com possibilidade de energização ou movimento inesperado.',
      risk: 'Partida inesperada, aprisionamento ou esmagamento.',
      possibleConsequence: 'Lesões graves, amputações ou acidente fatal.',
      recommendation: 'Aplicar parada, bloqueio e impedimento de reenergização antes da intervenção.',
      priority: 'Crítica',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-eixo-rotativo-exposto',
      title: 'Eixo ou componente rotativo exposto',
      description: 'Eixo, acoplamento ou componente rotativo está acessível sem proteção.',
      risk: 'Enroscamento, arraste e aprisionamento.',
      possibleConsequence: 'Lesões graves, fraturas ou amputações.',
      recommendation: 'Instalar proteção que impeça o acesso durante a operação.',
      priority: 'Crítica',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-correia-polia-sem-protecao',
      title: 'Correia ou polia sem proteção adequada',
      description: 'Correia, polia ou transmissão mecânica encontra-se acessível.',
      risk: 'Aprisionamento, arraste e esmagamento.',
      possibleConsequence: 'Lesões graves ou amputações.',
      recommendation: 'Instalar ou recompor a proteção da transmissão antes da liberação.',
      priority: 'Crítica',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-serra-sem-protecao',
      title: 'Serra circular sem proteção adequada',
      description: 'A serra apresenta área de corte ou transmissão acessível sem proteção suficiente.',
      risk: 'Contato com elemento cortante ou parte móvel.',
      possibleConsequence: 'Cortes graves, amputações ou projeção de partículas.',
      recommendation: 'Interromper a condição e regularizar as proteções antes do uso.',
      priority: 'Crítica',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-esmerilhadeira-sem-protecao',
      title: 'Esmerilhadeira ou lixadeira sem proteção',
      description: 'A ferramenta está sem coifa, proteção ou componente de segurança previsto.',
      risk: 'Contato com disco, ruptura e projeção de partículas.',
      possibleConsequence: 'Cortes, lesões oculares ou trauma grave.',
      recommendation: 'Retirar de uso e regularizar proteção e acessórios compatíveis.',
      priority: 'Crítica',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-misturador-protecao-inadequada',
      title: 'Misturador ou masseira com proteção inadequada',
      description: 'O equipamento permite acesso à zona de mistura ou transmissão em condição perigosa.',
      risk: 'Aprisionamento, esmagamento ou arraste.',
      possibleConsequence: 'Lesões graves em mãos e membros superiores.',
      recommendation: 'Regularizar proteção, intertravamento e parada antes da utilização.',
      priority: 'Crítica',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-oculos-nao-utilizado',
      title: 'Óculos de proteção não utilizado',
      description: 'Atividade com risco de projeção é executada sem proteção ocular prevista.',
      risk: 'Contato dos olhos com partículas, fragmentos ou respingos.',
      possibleConsequence: 'Irritação, lesão ocular ou perda parcial da visão.',
      recommendation: 'Regularizar o uso do óculos adequado e reforçar orientação e supervisão.',
      priority: 'Alta',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-luva-inadequada',
      title: 'Luva inadequada para a atividade',
      description: 'A proteção das mãos utilizada não é compatível com o perigo observado.',
      risk: 'Exposição a corte, abrasão, calor ou produto químico.',
      possibleConsequence: 'Cortes, queimaduras, irritações ou outras lesões nas mãos.',
      recommendation: 'Reavaliar e fornecer luva compatível com o risco e o método de trabalho.',
      priority: 'Alta',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-respirador-nao-utilizado',
      title: 'Proteção respiratória não utilizada',
      description: 'Há exposição a poeira, fumos ou contaminante sem a proteção respiratória prevista.',
      risk: 'Inalação de contaminantes presentes no ambiente.',
      possibleConsequence: 'Irritação, sintomas respiratórios ou agravos relacionados à exposição.',
      recommendation: 'Regularizar o respirador e revisar os controles coletivos existentes.',
      priority: 'Alta',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-calcado-inadequado',
      title: 'Calçado de segurança não utilizado ou inadequado',
      description: 'Trabalhador está em área de risco sem calçado compatível.',
      risk: 'Impacto, perfuração, esmagamento ou escorregamento.',
      possibleConsequence: 'Lesões nos pés e quedas.',
      recommendation: 'Regularizar o uso do calçado adequado à atividade e ao ambiente.',
      priority: 'Alta',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-capacete-nao-utilizado',
      title: 'Capacete de segurança não utilizado',
      description: 'Trabalhador está em área com risco de impacto ou queda de objetos sem capacete.',
      risk: 'Impacto na cabeça por objetos ou estruturas.',
      possibleConsequence: 'Traumatismo craniano ou lesão grave.',
      recommendation: 'Regularizar o uso do capacete e reforçar a exigência na área.',
      priority: 'Alta',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-cinto-nao-conectado',
      title: 'Cinturão de segurança sem conexão ao sistema',
      description: 'Trabalhador em risco de queda está com cinturão sem conexão eficaz.',
      risk: 'Queda para nível inferior sem retenção.',
      possibleConsequence: 'Trauma grave ou acidente fatal.',
      recommendation: 'Interromper a exposição até conexão correta ao sistema de proteção.',
      priority: 'Crítica',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-linha-vida-ausente',
      title: 'Linha de vida ou sistema de ancoragem ausente',
      description: 'A atividade em altura não dispõe de sistema de ancoragem adequado.',
      risk: 'Impossibilidade de conexão segura do trabalhador.',
      possibleConsequence: 'Queda de altura com lesão grave ou fatal.',
      recommendation: 'Não executar a atividade até disponibilizar sistema adequado e verificado.',
      priority: 'Crítica',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-borda-sem-protecao',
      title: 'Borda ou periferia sem proteção contra queda',
      description: 'Há acesso a borda com desnível sem proteção coletiva suficiente.',
      risk: 'Queda de trabalhador para nível inferior.',
      possibleConsequence: 'Traumas graves ou acidente fatal.',
      recommendation: 'Restringir o acesso e instalar proteção coletiva adequada.',
      priority: 'Crítica',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-escada-sem-fixacao',
      title: 'Escada portátil sem fixação ou estabilidade',
      description: 'A escada está apoiada sem condição estável ou meio contra deslocamento.',
      risk: 'Deslizamento ou tombamento durante o acesso.',
      possibleConsequence: 'Queda e traumatismos.',
      recommendation: 'Reposicionar e estabilizar a escada antes do uso.',
      priority: 'Alta',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-andaime-base-inadequada',
      title: 'Andaime com base ou apoio inadequado',
      description: 'O andaime apresenta apoio instável, improvisado ou sem nivelamento adequado.',
      risk: 'Deslocamento, tombamento ou colapso da estrutura.',
      possibleConsequence: 'Queda de trabalhadores e materiais.',
      recommendation: 'Interromper o uso e regularizar base, nivelamento e apoio.',
      priority: 'Crítica',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-escavacao-sem-escoramento',
      title: 'Escavação ou vala sem proteção adequada',
      description: 'A escavação apresenta condição de estabilidade ou acesso sem proteção compatível.',
      risk: 'Desmoronamento, queda ou soterramento.',
      possibleConsequence: 'Lesões graves, asfixia ou acidente fatal.',
      recommendation: 'Restringir a área e definir proteção ou escoramento antes da entrada.',
      priority: 'Crítica',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-vergalhao-exposto',
      title: 'Pontas de vergalhão expostas',
      description: 'Vergalhões ou elementos pontiagudos estão expostos em área de trabalho.',
      risk: 'Perfuração, corte ou empalamento em caso de contato ou queda.',
      possibleConsequence: 'Ferimentos graves.',
      recommendation: 'Instalar proteção nas pontas e impedir contato acidental.',
      priority: 'Alta',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-empilhadeira-sem-cinto',
      title: 'Empilhadeira com operador sem cinto de segurança',
      description: 'O operador utiliza a empilhadeira sem o cinto previsto.',
      risk: 'Projeção ou esmagamento em tombamento ou colisão.',
      possibleConsequence: 'Lesão grave ou fatal.',
      recommendation: 'Interromper a condução sem cinto e reforçar o uso obrigatório.',
      priority: 'Crítica',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-empilhadeira-sem-alerta',
      title: 'Empilhadeira com alerta sonoro ou luminoso inoperante',
      description: 'Buzina, alarme de ré ou sinalização da empilhadeira não funciona adequadamente.',
      risk: 'Baixa percepção do equipamento por pedestres.',
      possibleConsequence: 'Atropelamento, colisão ou esmagamento.',
      recommendation: 'Providenciar manutenção antes de liberar o equipamento.',
      priority: 'Alta',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-pedestre-empilhadeira-sem-segregacao',
      title: 'Circulação de pedestres e empilhadeiras sem segregação',
      description: 'Pedestres e equipamentos móveis compartilham rota sem separação suficiente.',
      risk: 'Atropelamento ou colisão.',
      possibleConsequence: 'Lesões graves ou fatais.',
      recommendation: 'Organizar e sinalizar rotas, priorizando segregação física ou controle eficaz.',
      priority: 'Crítica',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-pallet-danificado',
      title: 'Pallet danificado em uso ou armazenamento',
      description: 'Foi identificado pallet com dano estrutural ou condição inadequada.',
      risk: 'Queda ou instabilidade da carga.',
      possibleConsequence: 'Esmagamento, impacto ou dano de materiais.',
      recommendation: 'Retirar o pallet danificado e substituir por unidade adequada.',
      priority: 'Alta',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-cinta-elevacao-danificada',
      title: 'Cinta ou acessório de içamento danificado',
      description: 'Acessório de içamento apresenta desgaste, corte ou deformação.',
      risk: 'Rompimento durante movimentação de carga.',
      possibleConsequence: 'Queda de carga, esmagamento ou acidente fatal.',
      recommendation: 'Retirar o acessório de uso e substituir após inspeção adequada.',
      priority: 'Crítica',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-gancho-sem-trava',
      title: 'Gancho de içamento sem trava de segurança',
      description: 'O gancho de movimentação não possui trava funcional.',
      risk: 'Desengate acidental da carga.',
      possibleConsequence: 'Queda de carga e esmagamento.',
      recommendation: 'Não utilizar até regularizar a trava de segurança.',
      priority: 'Crítica',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-carga-suspensa-pessoas',
      title: 'Pessoas expostas sob carga suspensa',
      description: 'Há permanência ou circulação de pessoas na zona de carga suspensa.',
      risk: 'Atingimento por queda ou deslocamento da carga.',
      possibleConsequence: 'Lesões graves ou fatais.',
      recommendation: 'Isolar a área e impedir permanência sob a trajetória da carga.',
      priority: 'Crítica',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-cilindro-gas-sem-fixacao',
      title: 'Cilindro de gás sem fixação adequada',
      description: 'Cilindro está armazenado ou utilizado sem suporte eficaz contra tombamento.',
      risk: 'Queda, dano à válvula e liberação descontrolada de gás.',
      possibleConsequence: 'Impacto, incêndio, explosão ou exposição ao gás.',
      recommendation: 'Manter o cilindro na posição adequada e fixado em suporte compatível.',
      priority: 'Crítica',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-solda-sem-biombo',
      title: 'Soldagem sem proteção coletiva contra radiação e projeções',
      description: 'A atividade de soldagem ocorre sem barreira para pessoas próximas.',
      risk: 'Exposição à radiação, fagulhas e partículas quentes.',
      possibleConsequence: 'Lesões oculares, queimaduras ou princípio de incêndio.',
      recommendation: 'Isolar a área e utilizar biombo ou proteção coletiva adequada.',
      priority: 'Alta',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-trabalho-quente-sem-controle',
      title: 'Trabalho a quente sem controle adequado da área',
      description: 'Atividade com chama, solda ou faíscas ocorre sem controle suficiente do entorno.',
      risk: 'Ignição de materiais combustíveis ou exposição de pessoas.',
      possibleConsequence: 'Incêndio, queimaduras ou danos materiais.',
      recommendation: 'Organizar a área, afastar combustíveis e definir meios de resposta.',
      priority: 'Crítica',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-quimicos-incompativeis-juntos',
      title: 'Produtos químicos incompatíveis sem segregação',
      description: 'Produtos distintos estão armazenados juntos sem avaliação de compatibilidade.',
      risk: 'Reação química, vazamento, geração de calor ou gases.',
      possibleConsequence: 'Queimaduras, intoxicação ou incêndio.',
      recommendation: 'Reorganizar o armazenamento conforme compatibilidade e identificação.',
      priority: 'Alta',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-quimico-sem-contencao',
      title: 'Produto químico sem contenção para vazamentos',
      description: 'O armazenamento não dispõe de contenção adequada quando necessária.',
      risk: 'Espalhamento de vazamento e contato com pessoas ou ambiente.',
      possibleConsequence: 'Irritação, queimadura, contaminação ou incêndio.',
      recommendation: 'Providenciar contenção compatível e procedimento para vazamentos.',
      priority: 'Alta',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-exaustao-inoperante',
      title: 'Sistema de exaustão inoperante ou insuficiente',
      description: 'A exaustão local não funciona ou não controla adequadamente a emissão.',
      risk: 'Aumento de poeiras, fumos, vapores ou calor no ambiente.',
      possibleConsequence: 'Maior exposição ocupacional e desconforto.',
      recommendation: 'Regularizar o sistema e verificar sua eficácia após manutenção.',
      priority: 'Alta',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-ventilacao-inadequada',
      title: 'Ventilação inadequada no ambiente de trabalho',
      description: 'O ambiente apresenta baixa renovação de ar ou ventilação insuficiente.',
      risk: 'Acúmulo de calor, odores, vapores ou contaminantes.',
      possibleConsequence: 'Desconforto, mal-estar ou maior exposição.',
      recommendation: 'Avaliar e melhorar a ventilação conforme a atividade e agentes presentes.',
      priority: 'Média',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-iluminacao-insuficiente',
      title: 'Iluminação insuficiente na área de trabalho',
      description: 'A área apresenta visibilidade reduzida para execução segura da atividade.',
      risk: 'Erro operacional, tropeço ou contato com obstáculos.',
      possibleConsequence: 'Acidentes, fadiga visual ou perda de qualidade.',
      recommendation: 'Avaliar e melhorar a iluminação dos pontos de tarefa e circulação.',
      priority: 'Média',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-carga-manual-excessiva',
      title: 'Movimentação manual de carga com esforço elevado',
      description: 'A carga é movimentada manualmente com esforço relevante ou pega desfavorável.',
      risk: 'Sobrecarga lombar e musculoesquelética, além de queda da carga.',
      possibleConsequence: 'Distensões, dores ou esmagamento de mãos e pés.',
      recommendation: 'Reavaliar peso, frequência, pega e possibilidade de auxílio mecânico.',
      priority: 'Alta',
      source: 'auditar_seed',
    ),
    OfflineInlineSuggestion(
      id: 'auditar-primeiros-socorros-incompleto',
      title: 'Material de primeiros socorros incompleto ou indisponível',
      description: 'O ponto destinado a primeiros socorros não possui material previsto ou acesso adequado.',
      risk: 'Atraso no atendimento inicial a uma ocorrência.',
      possibleConsequence: 'Agravamento de lesões até atendimento especializado.',
      recommendation: 'Repor e organizar o material e manter o acesso disponível.',
      priority: 'Alta',
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
      onTap: () => _review(context, item),
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

  Future<void> _review(BuildContext context, OfflineInlineSuggestion item) async {
    final selected = await showDialog<OfflineInlineSuggestion>(context: context, barrierDismissible: false,
      builder: (_) => _OfflineReviewDialog(item: item));
    if (selected != null && context.mounted) onSelected(selected);
  }

  // Aplicar é uma aceitação consciente pelo técnico; não há confirmação
  // extra nem aprendizado ao apenas digitar ou abrir a prévia.
  void _quickApply(BuildContext context, OfflineInlineSuggestion item) {
    final a = item.assessment;
    if (a == null) {
      _review(context, item);
      return;
    }
    unawaited(OfflineReportInlineSuggestionService.learnApplied(item)
        .then<void>((_) {})
        .catchError((_) {}));
    onSelected(OfflineInlineSuggestion(
      id: item.id,
      title: item.title,
      description: a.description,
      risk: item.risk,
      possibleConsequence: item.possibleConsequence,
      recommendation:
          '${item.recommendation}\nReferência temática para conferência: ${a.rule.reference}.',
      priority: item.priority,
      source: item.source,
      assessment: a,
      reviewed: true,
    ));
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
                  'Outras sugestões',
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
        if (items.isEmpty) {
          if (snapshot.connectionState != ConnectionState.done ||
              query.trim().length < 5) {
            return const SizedBox.shrink();
          }
          final theme = Theme.of(context);
          return Padding(
            padding: const EdgeInsets.only(top: 8),
            child: Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
              decoration: BoxDecoration(
                color: theme.colorScheme.surfaceContainerHighest.withValues(
                  alpha: 0.28,
                ),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: theme.colorScheme.outlineVariant),
              ),
              child: Row(
                children: [
                  const Icon(Icons.search_off_rounded, size: 18),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      OfflineReasoning.explicitSafeOrUncertain(query)
                          ? 'Condição normal, corrigida ou ainda não verificada: nenhuma falha ativa sugerida.'
                          : 'Precisa de mais detalhes: informe o equipamento, a falha observada e a condição atual.',
                    ),
                  ),
                ],
              ),
            ),
          );
        }

        final theme = Theme.of(context);
        final visible = items.take(1).toList(growable: false);
        final hidden = items.skip(1).toList(growable: false);

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
                    const Icon(Icons.auto_awesome_outlined, size: 18),
                    const SizedBox(width: 6),
                    Expanded(
                      child: Text(
                        items.first.assessment != null
                            ? 'Correspondência forte • confira os fatos'
                            : 'Precisa de mais detalhes • modelo semelhante',
                        style: theme.textTheme.labelLarge?.copyWith(
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 5),
                _row(context, visible.first, compact: true),
                Padding(
                  padding: const EdgeInsets.fromLTRB(10, 0, 10, 4),
                  child: Text(
                    visible.first.assessment == null
                        ? 'Modelo parecido. Confirme a falha e ajuste a descrição antes de aplicar.'
                        : visible.first.description,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: theme.textTheme.bodySmall,
                  ),
                ),
                Wrap(
                  alignment: WrapAlignment.start,
                  spacing: 8,
                  runSpacing: 4,
                  children: [
                    if (visible.first.assessment != null)
                      FilledButton.tonal(
                        onPressed: () => _quickApply(context, visible.first),
                        child: const Text('Aplicar'),
                      ),
                    OutlinedButton(
                      onPressed: () => _review(context, visible.first),
                      child: const Text('Ajustar'),
                    ),
                    if (hidden.isNotEmpty)
                      TextButton.icon(
                        onPressed: () => _showMore(context, hidden),
                        icon: const Icon(Icons.expand_more_rounded, size: 18),
                        label: const Text('Outras opções'),
                      ),
                  ],
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}


class _OfflineReviewDialog extends StatefulWidget {
  const _OfflineReviewDialog({required this.item});
  final OfflineInlineSuggestion item;
  @override
  State<_OfflineReviewDialog> createState() => _OfflineReviewDialogState();
}
class _OfflineReviewDialogState extends State<_OfflineReviewDialog> {
  late final title = TextEditingController(text: widget.item.title);
  late final description = TextEditingController(text: widget.item.description);
  late final risk = TextEditingController(text: widget.item.risk);
  late final consequence = TextEditingController(text: widget.item.possibleConsequence);
  late final action = TextEditingController(text: widget.item.recommendation);
  late String priority = widget.item.priority;
  String exposure = 'Não informado';
  bool busy = false;
  @override
  void dispose() { for(final c in [title,description,risk,consequence,action]) { c.dispose(); } super.dispose(); }
  Widget field(String label, TextEditingController controller) => Padding(padding: const EdgeInsets.only(bottom: 12), child: TextField(controller: controller, minLines: 1, maxLines: 5, decoration: InputDecoration(labelText: label, border: const OutlineInputBorder())));
  Future<void> apply() async {
    if (busy) return;
    if (title.text.trim().isEmpty || description.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Preencha título e descrição antes de aplicar.')));
      return;
    }
    setState(() => busy = true);
    // O registro é aplicado imediatamente. Gravação de aprendizado nunca
    // bloqueia a navegação, mas continua serializada no armazenamento local.
    unawaited(OfflineReportInlineSuggestionService.learnApplied(
      OfflineInlineSuggestion(
        id: widget.item.id,
        title: title.text.trim(),
        description: widget.item.description,
        risk: risk.text.trim(),
        possibleConsequence: consequence.text.trim(),
        recommendation: action.text.trim(),
        priority: priority,
        source: widget.item.source,
        assessment: widget.item.assessment,
      ),
    ).then<void>((_) {}).catchError((_) {}));
    if (!mounted) return;
    final a = widget.item.assessment;
    Navigator.pop(context, OfflineInlineSuggestion(
      id: widget.item.id,
      title: title.text.trim(),
      description: description.text.trim(),
      risk: risk.text.trim(),
      possibleConsequence: consequence.text.trim(),
      recommendation:
          '${action.text.trim()}${a == null ? '' : '\nReferência temática para conferência: ${a.rule.reference}.'}',
      priority: priority,
      source: widget.item.source,
      assessment: a,
      reviewed: true,
    ));
  }
  @override
  Widget build(BuildContext context) {
    final a=widget.item.assessment;
    return PopScope(canPop: !busy, child: AlertDialog(title: const Text('Revisar sugestão sem IA'),
      content: SizedBox(width: 560, child: SingleChildScrollView(child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        if(a != null) ...[
          Text('${a.segment} • ${a.equipment}', style: const TextStyle(fontWeight: FontWeight.bold)),
          Text(a.reason), const SizedBox(height: 12),
          Text(a.rule.question),
          Wrap(spacing: 8, children: ['Sim','Não','Não informado'].map((answer) => ChoiceChip(label: Text(answer), selected: exposure == answer, onSelected: (_) => setState(() { exposure=answer; priority=a.priority(answer); }))).toList()),
          Text(a.priorityReason(exposure)), const SizedBox(height: 12),
        ],
        const Text('Confira os fatos e ajuste o texto antes de aplicar. A referência normativa é temática; o enquadramento depende da atividade.'),
        const SizedBox(height: 12),
        field('Título',title), field('Descrição do registro',description), field('Risco',risk),
        field('Possíveis consequências',consequence),field('Recomendação',action),
        DropdownButtonFormField<String>(key: ValueKey(priority), initialValue: priority,
          decoration: const InputDecoration(labelText: 'Prioridade — revisão do técnico'),
          items: ['Baixa','Média','Alta','Crítica'].map((p)=>DropdownMenuItem(value:p,child:Text(p))).toList(),
          onChanged: (v) {if(v != null) setState(()=>priority=v);}),
        const Padding(padding: EdgeInsets.only(top:12), child: Text('Aprendizado automático ao aplicar: suas correções serão reutilizadas nas próximas sugestões.')),
      ]))),
      actions: [TextButton(onPressed: busy ? null : ()=>Navigator.pop(context), child: const Text('Cancelar')),
        FilledButton(onPressed: busy ? null : apply, child: Text(busy ? 'Salvando...' : 'Aplicar texto revisado'))]));
  }
}
