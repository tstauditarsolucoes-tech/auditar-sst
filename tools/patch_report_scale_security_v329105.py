#!/usr/bin/env python3
"""Keep large Ronda reports pageable and restrict credential-bearing HTTP redirects."""
from pathlib import Path
import sys
root=Path(sys.argv[1]); platform=sys.argv[2]
if platform not in ('android','windows'): raise SystemExit('Unknown platform')
pdf=root/'lib/services/express_round_pdf_service.dart'
net=root/'lib/services/apps_script_http.dart'
pub=root/'pubspec.yaml'
def one(file, old, new, label):
    s=file.read_text(encoding='utf-8')
    if s.count(old)!=1: raise RuntimeError(f'{label}: expected once, found {s.count(old)}')
    file.write_text(s.replace(old,new,1),encoding='utf-8',newline='\n')

one(pdf,
    "      pw.MultiPage(\n        pageFormat: PdfPageFormat.a4,",
    "      pw.MultiPage(\n        // Field dossiers with 30-50 photos can span well past 20 pages.\n        // Content remains independently pageable; no evidence is truncated.\n        maxPages: 300,\n        pageFormat: PdfPageFormat.a4,",
    'bounded long Ronda pagination')
one(net,
    "          uri = uri.resolve(location);\n          redirectedToTemporaryHost =",
    """          final target = uri.resolve(location);
          if (!isAllowedCentralRedirect(endpoint, target)) {
            throw const CentralTransportException(
              'Redirecionamento da Central bloqueado por segurança. '
              'Nenhum dado foi enviado ao endereço de destino.',
            );
          }
          uri = target;
          redirectedToTemporaryHost =""",
    'redirect safety')
one(net,
    "  static bool _isTemporaryGoogleHost(Uri uri) {",
    """  /// Redirects carrying account credentials must remain on the original
  /// HTTPS host or the official Apps Script content-delivery hosts.
  /// Relative redirects inherit the original host and are permitted.
  static bool isAllowedCentralRedirect(Uri origin, Uri target) {
    if (origin.scheme.toLowerCase() != 'https' ||
        target.scheme.toLowerCase() != 'https' ||
        target.host.isEmpty || target.userInfo.isNotEmpty ||
        (target.hasPort && target.port != 443)) {
      return false;
    }
    final source = origin.host.toLowerCase();
    final destination = target.host.toLowerCase();
    if (destination == source) return true;
    return _isGoogleScriptHost(source) && _isGoogleScriptHost(destination);
  }

  static bool _isTemporaryGoogleHost(Uri uri) {""",
    'redirect allowlist')
# Never persist insecure endpoint in release config; existing service selectors
# already enforce HTTPS. Do not touch server auth or token serialization.
version=('3.29.104+246','3.29.105+247') if platform=='android' else ('3.30.28+215','3.30.29+216')
one(pub,'version: '+version[0],'version: '+version[1],'version bump')
print('REPORT_50_AND_CENTRAL_REDIRECT_PATCH_OK',platform,version[1])
