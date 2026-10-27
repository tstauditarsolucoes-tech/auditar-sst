import '../database.dart';

/// Configuração da Central Online incluída durante a compilação.
///
/// A URL pública fica no aplicativo. A chave é recebida por `--dart-define`,
/// evitando que seja publicada no código-fonte do repositório.
class WebServiceConfig {
  WebServiceConfig._();

  static const String endpoint = String.fromEnvironment(
    'AUDITAR_APPS_SCRIPT_URL',
    defaultValue:
        'https://script.google.com/macros/s/AKfycbxNG-wU-jZMKMR2cb1nR9OUd31GSUpGM0FIEagZEUP7sAHxkahLDuJ6T3wZvEe9rm6WrQ/exec',
  );

  static const String syncKey = String.fromEnvironment(
    'AUDITAR_SYNC_KEY',
  );

  static bool get hasCredentials =>
      endpoint.trim().isNotEmpty && syncKey.trim().isNotEmpty;

  static bool get hasPartialConfiguration =>
      endpoint.trim().isNotEmpty || syncKey.trim().isNotEmpty;

  static bool get hasValidEndpoint {
    final uri = Uri.tryParse(endpoint.trim());
    return uri != null &&
        uri.scheme == 'https' &&
        uri.host == 'script.google.com' &&
        uri.path.startsWith('/macros/s/') &&
        uri.path.endsWith('/exec');
  }

  static bool get isEmbedded => hasCredentials && hasValidEndpoint;

  /// Grava os valores permanentes no banco local antes de abrir o app.
  /// Assim, todas as funções existentes continuam usando a mesma fonte de
  /// configuração, inclusive Painel, CIPA, Drive e Assistente IA.
  static Future<void> applyEmbeddedConfiguration() async {
    if (!isEmbedded) return;

    final db = AppDatabase.instance;
    await db.setSetting(
      'management_panel_endpoint',
      endpoint.trim(),
    );
    await db.setSetting(
      'management_panel_sync_key',
      syncKey.trim(),
    );
  }
}
