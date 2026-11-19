#!/usr/bin/env python3
"""Substitui HTTP do servidor falso por HTTPS local SOMENTE no teste de sincronizacao."""
from pathlib import Path
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile

if len(sys.argv)!=2:
    raise SystemExit("Uso: patch_ci_https_fixture_20261119.py <APP_DIR>")
root=Path(sys.argv[1]).resolve()
target=root/"test/device_sync_roundtrip_test.dart"
if not target.is_file():raise RuntimeError("Fixture de sincronizacao ausente")
protected=[root/x for x in ("lib/services/apps_script_http.dart","lib/services/device_sync_service.dart","lib/services/auth_service.dart","lib/database.dart")]
before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected if p.is_file()}
code=target.read_text(encoding="utf-8")
if "class _FixtureLoopbackHttpsOverrides extends HttpOverrides" in code:
    print("LOCAL_HTTPS_FIXTURE_ALREADY_APPLIED")
    sys.exit(0)
anchors=("class _FakeCentral {",
    "server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);",
    "'http://"+chr(36)+"{server.address.address}:"+chr(36)+"{server.port}/exec',",
    "HttpOverrides.global = null;",
    "central = _FakeCentral();",
    "await central.start();")
if any(code.count(x)!=1 for x in anchors):
    raise RuntimeError("Layout do teste mudou: nao aplicar fixture HTTPS")
openssl=shutil.which("openssl")
if not openssl and os.name=="nt":
    for p in (r"C:\Program Files\Git\usr\bin\openssl.exe",
              r"C:\Program Files\Git\mingw64\bin\openssl.exe",
              r"C:\Program Files\OpenSSL-Win64\bin\openssl.exe"):
        if Path(p).is_file():openssl=p;break
if not openssl:raise RuntimeError("OpenSSL ausente: proibido liberar HTTP inseguro")
with tempfile.TemporaryDirectory(prefix="auditar_ci_https_") as d:
    crt=Path(d)/"cert.pem";key=Path(d)/"key.pem"
    cmd=[openssl,"req","-x509","-newkey","rsa:2048","-nodes",
         "-days","2","-keyout",str(key),"-out",str(crt),"-subj","/CN=127.0.0.1",
         "-addext","subjectAltName=IP:127.0.0.1,DNS:localhost"]
    r=subprocess.run(cmd,capture_output=True,text=True)
    if r.returncode:raise RuntimeError("Certificado local de teste nao gerado: "+r.stderr[-400:])
    cert_pem=crt.read_text(encoding="utf-8").rstrip()
    key_pem=key.read_text(encoding="utf-8").rstrip()
fixture="""// Somente teste: TLS de loopback; NUNCA incluso no aplicativo distribuido.
const _fixtureLocalCertificate = r'''__CERT__''';
const _fixtureLocalPrivateKey = r'''__KEY__''';

class _FixtureLoopbackHttpsOverrides extends HttpOverrides {
  _FixtureLoopbackHttpsOverrides(this.port);
  final int port;
  @override
  HttpClient createHttpClient(SecurityContext? context) {
    final client = super.createHttpClient(context);
    client.badCertificateCallback = (certificate, host, remotePort) =>
        host == '127.0.0.1' && remotePort == port &&
        certificate.subject.contains('127.0.0.1');
    return client;
  }
}

""".replace("__CERT__",cert_pem).replace("__KEY__",key_pem)
code=code.replace("class _FakeCentral {",fixture+"class _FakeCentral {",1)
code=code.replace("server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);",
    """final context = SecurityContext(withTrustedRoots: false);
    context.useCertificateChainBytes(utf8.encode(_fixtureLocalCertificate));
    context.usePrivateKeyBytes(utf8.encode(_fixtureLocalPrivateKey));
    server = await HttpServer.bindSecure(InternetAddress.loopbackIPv4, 0, context);""",1)
code=code.replace(anchors[2], anchors[2].replace("http://","https://"),1)
code=code.replace("    await central.start();",
    "    await central.start();\n    HttpOverrides.global = _FixtureLoopbackHttpsOverrides(central.server.port);",1)
code=code.replace("    await central.close();",
    "    await central.close();\n    HttpOverrides.global = null;",1)
if "HttpServer.bindSecure" not in code or "https://"+chr(36)+"{server.address.address}" not in code:
    raise RuntimeError("Verificacao de HTTPS do teste falhou")
for p in protected:
    if p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()!=before[str(p)]:
        raise RuntimeError("Nucleo protegido foi alterado: "+str(p))
target.write_text(code,encoding="utf-8",newline="\n")
print("LOCAL_HTTPS_FIXTURE_CREATED_ONLY_FOR_FLUTTER_TEST")
print("PRODUCTION_HTTP_SYNC_AUTH_SQLITE_UNCHANGED")
