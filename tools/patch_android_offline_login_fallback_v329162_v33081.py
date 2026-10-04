#!/usr/bin/env python3
"""Corrige somente o fallback do login offline Android quando a Central fica inacessível."""
from pathlib import Path
import hashlib
import sys

if len(sys.argv) < 3:
    raise SystemExit("uso: patch_android_offline_login_fallback_v329162_v33081.py <APP_DIR> <android|windows>")

root = Path(sys.argv[1])
platform = sys.argv[2].strip().lower()
if platform not in ("android", "windows"):
    raise SystemExit("plataforma invalida")

protected = [
    "lib/database.dart",
    "lib/services/device_sync_service.dart",
    "lib/services/apps_script_http.dart",
    "lib/services/sync_coordinator.dart",
    "lib/services/drive_service.dart",
    "lib/services/media_sync_service.dart",
    "lib/services/ai_assistant_service.dart",
    "painel_web_google_apps_script/Code.gs",
    "painel_web_google_apps_script/MultiUser.gs",
    "painel_web_google_apps_script/ClientPortal.gs",
    "painel_web_google_apps_script/ClientPortal.html",
    "painel_web_google_apps_script/ReportEmail.gs",
]
before = {
    name: hashlib.sha256((root / name).read_bytes()).hexdigest()
    for name in protected
}

auth_path = root / "lib/services/auth_service.dart"
auth = auth_path.read_text(encoding="utf-8")

old = """    } catch (error) {
      // Com rede disponível, o usuário precisa de uma sessão nova confirmada pela
      // Central. Não reutilizamos silenciosamente token antigo em caso de timeout/DNS.
      rethrow;
    }
"""
new = """    } catch (error) {
      // O Android pode continuar reportando Wi-Fi/rede mesmo quando a Central
      // está realmente inacessível. Nesses casos de transporte, tenta o login
      // offline já provisionado neste aparelho, mantendo usuário + senha.
      // Erros reais de credencial/autorização continuam sendo devolvidos.
      if (Platform.isAndroid && _isOfflineTransportError(error)) {
        return _loginOffline(identifier: identifier, password: password);
      }
      rethrow;
    }
"""

if platform == "android":
    if new not in auth:
        count = auth.count(old)
        if count != 1:
            raise RuntimeError(
                f"bloco de fallback do login esperado 1 vez; encontrado {count}"
            )
        auth = auth.replace(old, new, 1)
    auth_path.write_text(auth, encoding="utf-8", newline="\n")
else:
    # O fallback de autenticação offline é exclusivo do Android.
    # No Windows, esta etapa apenas mantém a linha de versão compatível
    # sem alterar o AuthService.
    print("WINDOWS_AUTH_UNCHANGED_OK")

pub_path = root / "pubspec.yaml"
pub = pub_path.read_text(encoding="utf-8")
if platform == "android":
    old_version = "version: 3.29.161+303"
    new_version = "version: 3.29.162+304"
else:
    old_version = "version: 3.30.80+267"
    new_version = "version: 3.30.81+268"

if new_version not in pub:
    if old_version not in pub:
        raise RuntimeError(f"versao base nao encontrada: {old_version}")
    pub = pub.replace(old_version, new_version, 1)
pub_path.write_text(pub, encoding="utf-8", newline="\n")

after = {
    name: hashlib.sha256((root / name).read_bytes()).hexdigest()
    for name in protected
}
changed = [name for name in protected if before[name] != after[name]]
if changed:
    raise RuntimeError("nucleo protegido alterado indevidamente: " + ", ".join(changed))

print("ANDROID_OFFLINE_LOGIN_FALLBACK_OK")
print("SYNC_DB_HTTP_MEDIA_DRIVE_AI_GS_UNCHANGED_OK")
print(new_version)
