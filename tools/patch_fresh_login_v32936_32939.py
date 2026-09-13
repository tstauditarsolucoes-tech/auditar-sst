#!/usr/bin/env python3
"""Auditar SST: exige novo login a cada inicializacao, preservando o deviceId.

Android: 3.29.35+177 -> 3.29.36+178
Windows: 3.29.38+180 -> 3.29.39+181

Nao altera telas/layout. Apenas impede restauracao automatica da sessao local salva.
"""
from pathlib import Path
import re
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else '.')
platform = (sys.argv[2] if len(sys.argv) > 2 else '').strip().lower()
if platform not in {'android', 'windows'}:
    raise SystemExit('Uso: patch_fresh_login_v32936_32939.py <app_root> <android|windows>')

pub_path = root / 'pubspec.yaml'
auth_path = root / 'lib/services/auth_service.dart'
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

pattern = re.compile(
    r"  static Future<void> initialize\(\) async \{.*?\n  \}\n\n  static Future<void> activateSavedSession\(\) async \{",
    re.S,
)
replacement = r'''  static Future<void> initialize() async {
    // Segurança: cada nova inicialização do aplicativo exige senha novamente.
    // Mantemos apenas o deviceId persistente para não quebrar identificação,
    // licença e sincronização do aparelho.
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

      // Remove sessão/usuário persistidos, preservando somente a identidade
      // do dispositivo. Assim, fechar e abrir o app volta para o login.
      await file.writeAsString(jsonEncode({'deviceId': _deviceId}));
    } catch (_) {
      _sessionToken = '';
      _currentUser = null;
      _deviceId = const Uuid().v4();
      try {
        await file.writeAsString(jsonEncode({'deviceId': _deviceId}));
      } catch (_) {}
    }
  }

  static Future<void> activateSavedSession() async {'''

if "cada nova inicialização do aplicativo exige senha novamente" not in auth:
    auth, count = pattern.subn(replacement, auth, count=1)
    if count != 1:
        raise RuntimeError('Nao foi possivel localizar AuthService.initialize()')

pub_path.write_text(pub, encoding='utf-8')
auth_path.write_text(auth, encoding='utf-8')

assert target in pub
assert "_sessionToken = '';" in auth
assert "jsonEncode({'deviceId': _deviceId})" in auth
print(f'Login fresco aplicado em {platform}: {target}')
