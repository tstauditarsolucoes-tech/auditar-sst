// Auditar SST Web: SONDAGEM Flutter para Android/Windows, opt-in desligado.
// Nao importar este arquivo no sincronizador antigo nem trocar WebServiceConfig.
// Biblioteca Dart pura, sem SQLite, token, login, fotos, mutacoes ou filas.
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

typedef ProbeGet = Future<Map<String, dynamic>> Function(Uri endpoint);

enum ProbeStatus {
  disabled,
  invalidConfiguration,
  unreachable,
  incompatible,
  serverFoundButSyncUnavailable,
}

class ProbeResult {
  final ProbeStatus status;
  final String detail;
  const ProbeResult(this.status, this.detail);
  bool get canSync => false; // Falha fechada por contrato.
}

class NativeBackendProbe {
  // Valores vazios/desligados POR PADRAO, mesmo apos instalar novo APK/EXE.
  static const bool buildEnabled = bool.fromEnvironment(
    'AUDITAR_SST_NATIVE_PROBE_ENABLED',
    defaultValue: false,
  );
  static const String buildUrl = String.fromEnvironment(
    'AUDITAR_SST_NATIVE_PROBE_URL',
    defaultValue: '',
  );

  final bool enabled;
  final String baseUrl;
  final ProbeGet getJson;

  NativeBackendProbe({
    required this.enabled,
    required this.baseUrl,
    ProbeGet? getJson,
  }) : getJson = getJson ?? _readOnlyGet;

  factory NativeBackendProbe.fromBuildConfiguration() => NativeBackendProbe(
    enabled: buildEnabled,
    baseUrl: buildUrl,
  );

  // Nao aceita URI com usuario/senha, consulta, fragmento ou caminho
  // para evitar vazamento de credenciais ou troca acidental de Apps Script.
  static Uri? validatePrivateBaseUrl(String value) {
    if (value.isEmpty || value.length > 240 || value != value.trim()) {
      return null;
    }
    final uri = Uri.tryParse(value);
    if (uri == null ||
        uri.scheme != 'https' ||
        uri.host.isEmpty ||
        uri.userInfo.isNotEmpty ||
        uri.hasQuery ||
        uri.hasFragment ||
        (uri.path.isNotEmpty && uri.path != '/') ||
        uri.host.toLowerCase() == 'script.google.com') {
      return null;
    }
    return uri;
  }

  Future<ProbeResult> check() async {
    // Nao faz NENHUMA chamada de rede quando o opt-in estiver desativado.
    if (!enabled) {
      return const ProbeResult(ProbeStatus.disabled, 'Sondagem desativada');
    }
    final base = validatePrivateBaseUrl(baseUrl);
    if (base == null) {
      return const ProbeResult(
        ProbeStatus.invalidConfiguration,
        'URL HTTPS exclusiva de homologação não configurada',
      );
    }
    // Usa exclusivamente GET; nunca chama push, pull, login ou coleta ID.
    final url = base.replace(path: '/api/v1/native/handshake');
    Map<String, dynamic> response;
    try {
      response = await getJson(url).timeout(const Duration(seconds: 7));
    } catch (_) {
      return const ProbeResult(
        ProbeStatus.unreachable,
        'Servidor privado indisponível ou resposta inválida',
      );
    }
    if (response['ok'] != true ||
        response['service'] != 'auditar-sst-web' ||
        response['contract'] != 'sst-native-probe-v1' ||
        response['apiVersion'] != 1 ||
        response['environment'] != 'homologacao-isolada' ||
        response['productionDataConnected'] != false) {
      return const ProbeResult(
        ProbeStatus.incompatible,
        'Versão ou isolamento do servidor incompatível',
      );
    }
    final native = response['native'];
    if (native is! Map ||
        native['android'] != false ||
        native['windows'] != false ||
        native['syncEnabled'] != false ||
        native['writesEnabled'] != false ||
        native['authentication'] != 'not-implemented') {
      // Se o contrato mudar para permitir escrita, ESTE cliente continua
      // bloqueado ate nova implementacao revisada e testada.
      return const ProbeResult(
        ProbeStatus.incompatible,
        'Contrato nativo mudou; nenhuma sincronização liberada',
      );
    }
    return const ProbeResult(
      ProbeStatus.serverFoundButSyncUnavailable,
      'Servidor da homologação encontrado; Android/Windows ainda sem sincronização',
    );
  }

  static Future<Map<String, dynamic>> _readOnlyGet(Uri url) async {
    final client = HttpClient()
      ..connectionTimeout = const Duration(seconds: 5)
      ..autoUncompress = false;
    try {
      final request = await client.getUrl(url);
      request.followRedirects = false;
      request.maxRedirects = 0;
      request.headers.set(HttpHeaders.acceptHeader, 'application/json');
      final response = await request.close();
      if (response.statusCode != HttpStatus.ok ||
          response.headers.contentType?.mimeType != 'application/json') {
        throw const FormatException('Resposta inesperada');
      }
      final sink = BytesBuilder(copy: false);
      await for (final part in response) {
        if (sink.length + part.length > 4096) {
          throw const FormatException('Resposta grande demais');
        }
        sink.add(part);
      }
      final value = jsonDecode(utf8.decode(sink.takeBytes()));
      if (value is! Map<String, dynamic>) {
        throw const FormatException('Contrato JSON inválido');
      }
      return value;
    } finally {
      client.close(force: true);
    }
  }
}
