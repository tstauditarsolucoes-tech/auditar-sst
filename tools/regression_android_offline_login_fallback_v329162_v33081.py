#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1])
auth = (root / "lib/services/auth_service.dart").read_text(encoding="utf-8")
pub = (root / "pubspec.yaml").read_text(encoding="utf-8")

is_android = "version: 3.29." in pub

if is_android:
    login_start = auth.index("  static Future<AuditarUser> login({")
    login_end = auth.index("  static Future<AuditarUser> _acceptLogin(", login_start)
    login = auth[login_start:login_end]

    assert "Platform.isAndroid && _isOfflineTransportError(error)" in login
    assert "return _loginOffline(identifier: identifier, password: password);" in login
    assert "rethrow;" in login

    assert "if (!Platform.isAndroid) return;" in auth
    assert "static Future<AuditarUser> _loginOffline" in auth
    assert "savedLogin != _normalizeOfflineLogin(identifier)" in auth
    assert "final calculated = _offlineVerifier(" in auth
    assert "if (calculated != savedVerifier)" in auth
    assert "O acesso offline precisa ser renovado" in auth
    assert "sha256.convert(bytes).bytes" in auth
    assert "value: password" not in auth
    assert "_isOfflineTransportError(error)" in login
    assert "Usuário ou senha incorretos." in auth

assert (
    "version: 3.29.162+304" in pub
    or "version: 3.29.163+305" in pub
    or "version: 3.29.164+306" in pub
    or "version: 3.29.165+307" in pub
    or "version: 3.29.166+308" in pub
    or "version: 3.30.81+268" in pub
    or "version: 3.30.82+269" in pub
    or "version: 3.30.83+270" in pub
    or "version: 3.30.84+271" in pub
    or "version: 3.30.85+272" in pub
), "versao da linha offline/controle operacional incorreta"

if is_android:
    print("OFFLINE_LOGIN_TRANSPORT_FALLBACK_OK")
    print("OFFLINE_PASSWORD_VERIFIER_PRESERVED_OK")
    print("ONLINE_AUTH_ERRORS_PRESERVED_OK")
else:
    print("WINDOWS_AUTH_COMPATIBILITY_OK")
