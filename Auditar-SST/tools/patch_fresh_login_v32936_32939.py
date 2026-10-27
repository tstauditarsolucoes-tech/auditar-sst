#!/usr/bin/env python3
"""Auditar SST: exige novo login a cada inicializacao, preservando o deviceId.

Android: 3.29.35+177 -> 3.29.36+178
Windows: 3.29.38+180 -> 3.29.39+181

Nao altera telas/layout. A restauracao de sessao antiga fica desativada no uso
normal; o parametro restoreSavedSessionForTesting existe apenas para manter os
testes de sincronizacao offline capazes de injetar uma sessao simulada.
"""
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else '.')
platform = (sys.argv[2] if len(sys.argv) > 2 else '').strip().lower()
if platform not in {'android', 'windows'}:
    raise SystemExit('Uso: patch_fresh_login_v32936_32939.py <app_root> <android|windows>')

pub_path = root / 'pubspec.yaml'
auth_path = root / 'lib/services/auth_service.dart'
test_path = root / 'test/device_sync_roundtrip_test.dart'
pub = pub_path.read_text(encoding='utf-8')
auth = auth_path.read_text(encoding='utf-8')

if platform == 'android':
    expected = 'version: 3.29.35+177'
    target = 'version: 3.29.36+178'
else:
    expected = 'version: 3.29.38+180'
    target = 'version: 3.29.39+181'

if target not in pub:
    if expected not in pub:
        raise RuntimeError(f'Versao esperada ausente: {expected}')
    pub = pub.replace(expected, target, 1)

signature = '  static Future<void> initialize() async {\n'
new_signature = (
    '  static Future<void> initialize({bool restoreSavedSessionForTesting = false}) async {\n'
)
if new_signature not in auth:
    if signature not in auth:
        raise RuntimeError('Nao foi possivel localizar AuthService.initialize()')
    auth = auth.replace(signature, new_signature, 1)

    guard = r'''    // Segurança: cada nova inicialização do aplicativo exige senha novamente.
    // Mantemos somente o deviceId persistente para preservar a identidade do
    // aparelho, licença e vínculo de sincronização.
    if (!restoreSavedSessionForTesting) {
      _sessionToken = '';
      _currentUser = null;

      final file = await _authFile();
      if (!await file.exists()) return;
      try {
        final decoded = jsonDecode(await file.readAsString());
        if (decoded is Map) {
          _deviceId = '${decoded['deviceId'] ?? ''}'.trim();
        }
        if (_deviceId.isEmpty) _deviceId = const Uuid().v4();
        await file.writeAsString(jsonEncode({'deviceId': _deviceId}));
      } catch (_) {
        _sessionToken = '';
        _currentUser = null;
        _deviceId = const Uuid().v4();
        try {
          await file.writeAsString(jsonEncode({'deviceId': _deviceId}));
        } catch (_) {}
      }
      return;
    }

'''
    auth = auth.replace(new_signature, new_signature + guard, 1)

# O teste de roundtrip precisa injetar uma sessão simulada. Em produção o
# parâmetro nunca é informado e a sessão não é restaurada automaticamente.
if test_path.exists():
    test = test_path.read_text(encoding='utf-8')
    old = '  await AuthService.initialize();\n  await AuthService.activateSavedSession();\n'
    new = (
        '  await AuthService.initialize(restoreSavedSessionForTesting: true);\n'
        '  await AuthService.activateSavedSession();\n'
    )
    if new not in test:
        if old not in test:
            raise RuntimeError('Teste de sincronizacao: marcador de sessao nao encontrado')
        test = test.replace(old, new, 1)
    test_path.write_text(test, encoding='utf-8')

pub_path.write_text(pub, encoding='utf-8')
auth_path.write_text(auth, encoding='utf-8')

assert target in pub
assert 'restoreSavedSessionForTesting = false' in auth
assert "jsonEncode({'deviceId': _deviceId})" in auth
print(f'Login fresco aplicado em {platform}: {target}')
