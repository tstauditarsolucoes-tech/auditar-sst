// Dart puro: execute 'dart run native_backend_probe_test.dart' (sem Flutter).
import 'native_backend_probe.dart';

void check(bool value, String message) {
  if (!value) throw StateError(message);
}
Map<String, dynamic> fixture() => {
  'ok': true,
  'service': 'auditar-sst-web',
  'contract': 'sst-native-probe-v1',
  'apiVersion': 1,
  'environment': 'homologacao-isolada',
  'productionDataConnected': false,
  'native': {
    'android': false,
    'windows': false,
    'syncEnabled': false,
    'writesEnabled': false,
    'authentication': 'not-implemented',
  },
};

Future<void> main() async {
  var requests = 0;
  final disabled = await NativeBackendProbe(
    enabled: false,
    baseUrl: 'https://homologacao.invalid',
    getJson: (_) async {
      requests++;
      throw StateError('Deve permanecer offline');
    },
  ).check();
  check(disabled.status == ProbeStatus.disabled, 'Desativado por padrão');
  check(!disabled.canSync, 'Não pode sincronizar');

  for (final url in [
    '', 'http://homologacao.invalid', 'https://usuario:senha@homologacao.invalid',
    'https://homologacao.invalid/exec', 'https://homologacao.invalid/?token=x',
    'https://homologacao.invalid/#hash', 'https://script.google.com',
    ' https://homologacao.invalid',
  ]) {
    final value = await NativeBackendProbe(
      enabled: true,
      baseUrl: url,
      getJson: (_) async {
        requests++;
        return fixture();
      },
    ).check();
    check(
      value.status == ProbeStatus.invalidConfiguration,
      'URL insegura foi aceita: $url',
    );
  }
  check(requests == 0, 'Validação de URL não pode enviar dados');

  final success = await NativeBackendProbe(
    enabled: true,
    baseUrl: 'https://homologacao.invalid/',
    getJson: (uri) async {
      requests++;
      check(uri.toString() ==
        'https://homologacao.invalid/api/v1/native/handshake',
        'Somente GET handshake pode ser usado');
      return fixture();
    },
  ).check();
  check(
    success.status == ProbeStatus.serverFoundButSyncUnavailable,
    'Deve reconhecer servidor sem habilitar sync',
  );
  check(!success.canSync, 'O cliente não pode confirmar fila ou gravar dados');
  check(requests == 1, 'Somente um pedido permitido');

  final changed = fixture();
  (changed['native'] as Map<String, dynamic>)['syncEnabled'] = true;
  final rejected = await NativeBackendProbe(
    enabled: true, baseUrl: 'https://homologacao.invalid',
    getJson: (_) async => changed,
  ).check();
  check(rejected.status == ProbeStatus.incompatible,
    'Abertura futura de escrita exige um novo cliente revisado');

  final changedEnvironment = fixture();
  changedEnvironment['environment'] = 'production';
  final denied = await NativeBackendProbe(
    enabled: true, baseUrl: 'https://homologacao.invalid',
    getJson: (_) async => changedEnvironment,
  ).check();
  check(denied.status == ProbeStatus.incompatible,
    'Proibido aceitar ambiente de produção');

  final offline = await NativeBackendProbe(
    enabled: true, baseUrl: 'https://homologacao.invalid',
    getJson: (_) async => throw const FormatException('Conexão indisponível'),
  ).check();
  check(offline.status == ProbeStatus.unreachable, 'Conexão offline precisa falhar fechada');

  print('NATIVE_PROBE_READ_ONLY_DART_TESTS_OK');
}
