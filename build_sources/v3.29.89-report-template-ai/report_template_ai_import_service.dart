import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import '../database.dart';
import 'apps_script_http.dart';
import 'auth_service.dart';
import 'report_template_service.dart';
import 'web_service_config.dart';

class ReportTemplateAiDraft {
  final ReportTemplateDefinition template;
  final String templateClass;
  final String confidence;
  final String layoutSummary;
  final List<String> detectedSections;
  final List<String> adaptations;
  final List<String> warnings;
  final String sourceFileName;

  const ReportTemplateAiDraft({
    required this.template,
    required this.templateClass,
    required this.confidence,
    required this.layoutSummary,
    required this.detectedSections,
    required this.adaptations,
    required this.warnings,
    required this.sourceFileName,
  });
}

class ReportTemplateAiImportException implements Exception {
  final String message;
  const ReportTemplateAiImportException(this.message);

  @override
  String toString() => message;
}

class ReportTemplateAiImportService {
  static const int maxPdfBytes = 11 * 1024 * 1024;

  static Future<ReportTemplateAiDraft> analyzePdf({
    required Uint8List pdfBytes,
    required String fileName,
  }) async {
    if (pdfBytes.isEmpty) {
      throw const ReportTemplateAiImportException(
        'O PDF selecionado está vazio.',
      );
    }
    if (pdfBytes.length > maxPdfBytes) {
      throw const ReportTemplateAiImportException(
        'O PDF é muito grande para análise direta. Use um arquivo de até 11 MB.',
      );
    }
    if (pdfBytes.length < 5 ||
        String.fromCharCodes(pdfBytes.take(5)) != '%PDF-') {
      throw const ReportTemplateAiImportException(
        'Selecione um arquivo PDF válido.',
      );
    }

    final savedEndpoint = (await AppDatabase.instance.getSetting(
      'management_panel_endpoint',
      fallback: '',
    ))
        .trim();
    final savedSyncKey = (await AppDatabase.instance.getSetting(
      'management_panel_sync_key',
      fallback: '',
    ))
        .trim();
    final endpoint =
        savedEndpoint.isNotEmpty ? savedEndpoint : WebServiceConfig.endpoint.trim();
    final syncKey =
        savedSyncKey.isNotEmpty ? savedSyncKey : WebServiceConfig.syncKey.trim();

    if (endpoint.isEmpty || syncKey.isEmpty) {
      throw const ReportTemplateAiImportException(
        'A Central Online precisa estar configurada para usar o Criador de modelos com IA.',
      );
    }

    final uri = Uri.tryParse(endpoint);
    if (uri == null ||
        uri.scheme != 'https' ||
        uri.host != 'script.google.com' ||
        !uri.path.startsWith('/macros/s/') ||
        !uri.path.endsWith('/exec')) {
      throw const ReportTemplateAiImportException(
        'A URL da Central Online não é uma publicação permanente válida.',
      );
    }

    final document =
        'data:application/pdf;base64,${base64Encode(pdfBytes)}';
    Map<String, dynamic>? decoded;
    Object? lastError;

    for (var attempt = 0; attempt < 2; attempt++) {
      try {
        final response = await AppsScriptHttp.postJson(
          uri,
          {
            'action': 'ai_assistant',
            'syncKey': syncKey,
            'authToken': AuthService.sessionToken,
            'payload': {
              'mode': 'report_template_import',
              'sourceFileName': fileName,
              'document': document,
            },
          },
          timeout: const Duration(seconds: 105),
          allowLongAndroidRequest: true,
        );

        final body = utf8.decode(response.bodyBytes, allowMalformed: true);
        if (body.trimLeft().startsWith('<')) {
          throw const ReportTemplateAiImportException(
            'A Central Online retornou uma página temporária do Google.',
          );
        }

        final raw = jsonDecode(body);
        if (raw is! Map) {
          throw const ReportTemplateAiImportException(
            'A Central retornou uma resposta inválida para o modelo.',
          );
        }
        decoded = Map<String, dynamic>.from(raw);

        final transient = <int>{408, 429, 500, 502, 503, 504};
        if (transient.contains(response.statusCode) && attempt == 0) {
          await Future<void>.delayed(const Duration(seconds: 2));
          continue;
        }
        break;
      } on ReportTemplateAiImportException catch (error) {
        lastError = error;
        if (attempt == 0 &&
            (error.message.toLowerCase().contains('temporária') ||
                error.message.toLowerCase().contains('google'))) {
          await Future<void>.delayed(const Duration(seconds: 2));
          continue;
        }
        rethrow;
      } on SocketException catch (error) {
        lastError = error;
        if (attempt == 0) {
          await Future<void>.delayed(const Duration(seconds: 2));
          continue;
        }
      } on FormatException catch (error) {
        lastError = error;
      } catch (error) {
        lastError = error;
        if (attempt == 0) {
          await Future<void>.delayed(const Duration(seconds: 2));
          continue;
        }
      }
    }

    if (decoded == null) {
      throw ReportTemplateAiImportException(
        'Não foi possível consultar a IA para analisar o modelo. $lastError',
      );
    }

    if (decoded['ok'] != true) {
      final message =
          '${decoded['message'] ?? 'A IA não concluiu a análise do modelo.'}'
              .trim();
      if (message.toLowerCase().contains('tipo de análise de ia inválido')) {
        throw const ReportTemplateAiImportException(
          'A Central Online ainda não possui o módulo de importação de modelos. Atualize o Code.gs da Central para esta versão do app.',
        );
      }
      throw ReportTemplateAiImportException(message);
    }

    final rawResult = decoded['result'];
    if (rawResult is! Map) {
      throw const ReportTemplateAiImportException(
        'A IA respondeu sem um modelo utilizável.',
      );
    }
    final result = Map<String, dynamic>.from(rawResult);

    String value(String key, String fallback) {
      final text = '${result[key] ?? ''}'.trim();
      return text.isEmpty ? fallback : text;
    }

    bool flag(String key, bool fallback) {
      final raw = result[key];
      if (raw is bool) return raw;
      return fallback;
    }

    int columns() {
      final raw = result['photoColumns'];
      if (raw is num) return raw.round().clamp(1, 3);
      return 2;
    }

    String oneOf(String key, List<String> allowed, String fallback) {
      final text = '${result[key] ?? ''}'.trim().toLowerCase();
      return allowed.contains(text) ? text : fallback;
    }

    List<String> strings(String key) {
      final raw = result[key];
      if (raw is! List) return const [];
      return raw
          .map((item) => '$item'.trim())
          .where((item) => item.isNotEmpty)
          .take(20)
          .toList();
    }

    String color(String key, String fallback) {
      final text = value(key, fallback).toUpperCase();
      return RegExp(r'^#[0-9A-F]{6}$').hasMatch(text) ? text : fallback;
    }

    var name = value('name', 'Modelo importado com IA');
    if (name.length > 70) name = name.substring(0, 70).trim();

    final templateClass = value('templateClass', 'Personalizado');
    final analysisDescription = value(
      'description',
      'Modelo criado pela IA a partir de um PDF de referência.',
    );
    final description =
        '$analysisDescription • Importado com IA de "$fileName".';

    final template = ReportTemplateDefinition(
      id: ReportTemplateService.newCustomId(),
      name: name,
      description: description,
      primaryColor: color('primaryColor', '#0B2E4F'),
      secondaryColor: color('secondaryColor', '#178A3D'),
      headerTitle: value('headerTitle', 'RELATÓRIO GERENCIAL DE SST'),
      headerStyle: oneOf(
        'headerStyle',
        const ['classico', 'compacto', 'impacto'],
        'classico',
      ),
      logoMode: oneOf(
        'logoMode',
        const ['ambas', 'auditar', 'cliente', 'nenhuma'],
        'ambas',
      ),
      footerText: value(
        'footerText',
        'Auditar SST • Relatório gerencial de segurança do trabalho',
      ),
      photoColumns: columns(),
      signatureStyle: oneOf(
        'signatureStyle',
        const ['app', 'linhas', 'ocultar'],
        'app',
      ),
      showCover: flag('showCover', true),
      showSummary: flag('showSummary', true),
      showChecklistDetails: flag('showChecklistDetails', false),
      isBuiltIn: false,
      useLegacyRenderer: false,
    );

    return ReportTemplateAiDraft(
      template: template,
      templateClass: templateClass,
      confidence: value('confidence', 'Média'),
      layoutSummary: value(
        'layoutSummary',
        'A IA identificou a estrutura principal e adaptou o PDF aos componentes disponíveis no Auditar.',
      ),
      detectedSections: strings('detectedSections'),
      adaptations: strings('adaptations'),
      warnings: strings('warnings'),
      sourceFileName: fileName,
    );
  }
}
