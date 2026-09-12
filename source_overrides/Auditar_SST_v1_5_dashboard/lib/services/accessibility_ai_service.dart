import 'dart:convert';

import '../database.dart';
import 'apps_script_http.dart';

class AccessibilityAiException implements Exception {
  final String message;

  const AccessibilityAiException(this.message);

  @override
  String toString() => message;
}

class AccessibilityAiResult {
  final String summary;
  final String recommendation;
  final List<String> checksRequired;
  final List<String> references;
  final String confidence;
  final Map<String, dynamic> raw;

  const AccessibilityAiResult({
    required this.summary,
    required this.recommendation,
    required this.checksRequired,
    required this.references,
    required this.confidence,
    required this.raw,
  });
}

class AccessibilityAiService {
  AccessibilityAiService._();

  static bool _isPermanentAppsScriptUrl(Uri uri) {
    return uri.scheme == 'https' &&
        uri.host == 'script.google.com' &&
        uri.path.startsWith('/macros/s/') &&
        uri.path.endsWith('/exec');
  }

  static Future<Map<String, dynamic>> _request(
    Map<String, Object?> payload,
  ) async {
    final db = AppDatabase.instance;
    final endpoint = (await db.getSetting(
      'management_panel_endpoint',
      fallback: '',
    ))
        .trim();
    final syncKey = (await db.getSetting(
      'management_panel_sync_key',
      fallback: '',
    ))
        .trim();

    if (endpoint.isEmpty || syncKey.isEmpty) {
      throw const AccessibilityAiException(
        'Configure primeiro a Central Online e o Assistente IA nas configurações do Auditar SST.',
      );
    }

    final uri = Uri.tryParse(endpoint);
    if (uri == null || !_isPermanentAppsScriptUrl(uri)) {
      throw const AccessibilityAiException(
        'A URL da Central Online não é uma publicação permanente válida do Apps Script.',
      );
    }

    final response = await AppsScriptHttp.postJson(
      uri,
      <String, Object?>{
        'action': 'ai_assistant',
        'syncKey': syncKey,
        'payload': payload,
      },
      timeout: const Duration(seconds: 90),
    );

    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw AccessibilityAiException(
        'A Central Online respondeu com erro ${response.statusCode}.',
      );
    }

    Map<String, dynamic> body;
    try {
      body = jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
    } catch (_) {
      throw const AccessibilityAiException(
        'A Central Online retornou uma resposta inválida.',
      );
    }

    if (body['ok'] != true) {
      throw AccessibilityAiException(
        '${body['message'] ?? 'A IA não conseguiu concluir a análise.'}',
      );
    }

    final result = body['result'];
    if (result is! Map) {
      throw const AccessibilityAiException(
        'A resposta da IA não contém uma análise utilizável.',
      );
    }
    return Map<String, dynamic>.from(result);
  }

  static List<String> _stringList(dynamic value) {
    if (value is! List) return const [];
    return value
        .map((item) => '$item'.trim())
        .where((item) => item.isNotEmpty)
        .toList(growable: false);
  }

  /// Usa o modo de foto já existente no Assistente IA do Auditar SST quando
  /// houver evidência fotográfica. Assim a chave Gemini continua protegida no
  /// Apps Script e nenhuma credencial de IA é gravada no APK.
  static Future<AccessibilityAiResult> analyzePoint({
    required String companyName,
    required String category,
    required String location,
    required Map<String, String> measurements,
    required String technicianObservation,
    List<String> imageDataUris = const [],
  }) async {
    final cleanMeasurements = <String, String>{};
    measurements.forEach((key, value) {
      final text = value.trim();
      if (text.isNotEmpty) cleanMeasurements[key] = text;
    });

    if (imageDataUris.isNotEmpty) {
      final context = <String, Object?>{
        'local': location,
        'medidas_e_dados_coletados': cleanMeasurements,
        'observacao_do_tecnico': technicianObservation,
        'objetivo':
            'Apoiar levantamento para laudo de acessibilidade. Não declarar conformidade definitiva. Indicar pontos que precisam ser conferidos presencialmente e referências prováveis a confirmar na versão vigente.',
      };

      final raw = await _request(<String, Object?>{
        'mode': 'checklist_photo',
        'companyName': companyName,
        'area': location,
        'question': 'Acessibilidade — $category',
        'category': 'Laudo de Acessibilidade',
        'reference':
            'ABNT NBR 9050 e legislação de acessibilidade aplicável — confirmar versão vigente',
        'technicianContext': jsonEncode(context),
        'images': imageDataUris.take(4).toList(growable: false),
      });

      final summary = '${raw['description'] ?? ''}'.trim();
      final risk = '${raw['risk'] ?? ''}'.trim();
      final recommendation = '${raw['recommendation'] ?? ''}'.trim();
      final combined = [summary, if (risk.isNotEmpty) 'Impacto/barreira: $risk']
          .where((item) => item.trim().isNotEmpty)
          .join('\n\n');

      return AccessibilityAiResult(
        summary: combined,
        recommendation: recommendation,
        checksRequired: _stringList(raw['checksRequired']),
        references: _stringList(raw['likelyReferences']),
        confidence: '${raw['confidence'] ?? ''}'.trim(),
        raw: raw,
      );
    }

    // Sem foto, reaproveita o modo textual já disponível na Central Online.
    // O retorno é tratado como orientação de coleta, nunca como laudo pronto.
    final raw = await _request(<String, Object?>{
      'mode': 'company_priorities',
      'companyData': <String, Object?>{
        'tipo_de_analise': 'levantamento para laudo de acessibilidade',
        'empresa': companyName,
        'categoria': category,
        'local': location,
        'medidas_e_dados_coletados': cleanMeasurements,
        'observacao_do_tecnico': technicianObservation,
        'instrucao':
            'Analise somente os dados informados. Aponte o que merece atenção, o que ainda precisa ser medido/verificado e próximos passos. Não conclua conformidade legal definitiva e não invente dimensões.',
      },
    });

    final priorities = _stringList(raw['priorities']);
    final nextActions = _stringList(raw['nextActions']);
    final dataGaps = _stringList(raw['dataGaps']);

    return AccessibilityAiResult(
      summary: '${raw['situation'] ?? ''}'.trim(),
      recommendation: nextActions.join('\n'),
      checksRequired: dataGaps,
      references: const [],
      confidence: priorities.isEmpty ? '' : 'Orientativa',
      raw: raw,
    );
  }
}
