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
# The built-in PDF font cannot render the bullet separator U+2022; replace
# decorative separators without removing any substantive report content.
pdf_text=pdf.read_text(encoding='utf-8')
bullet_count=pdf_text.count('•')
if bullet_count < 2: raise RuntimeError('Expected PDF-only bullet separators absent')
pdf.write_text(pdf_text.replace('•',' - '),encoding='utf-8',newline='\n')
print('PDF_FONT_SEPARATOR_NORMALIZED',bullet_count)

one(pdf, "                  ? template!.footerText\n",
        "                  ? template!.footerText.replaceAll('•', ' - ')\n",
        'custom footer glyph')
one(pdf, "    final words = input.trim().split(RegExp(r'\\s+'));",
        "    final words = input.replaceAll('•', ' - ').trim().split(RegExp(r'\\s+'));",
        'long AI narrative bullet glyph')


one(net,
    "  static const int _maxRootAttempts = 2;",
    """  static const int _maxRootAttempts = 2;
  // Only the isolated CI local-HTTP test can enable this at compile time.
  // Release builds never pass this define; the default is strictly false.
  static const bool _allowTestLoopback = bool.fromEnvironment(
    'AUDITAR_TEST_LOOPBACK', defaultValue: false);""",
    'strict CI-only loopback default')
one(net,
    "  ) async {\n    final encodedBody = jsonEncode(payload);",
    """  ) async {
    final loopbackForTest = _allowTestLoopback &&
        endpoint.scheme == 'http' &&
        const {'127.0.0.1', 'localhost', '::1'}.contains(endpoint.host);
    if ((endpoint.scheme.toLowerCase() != 'https' && !loopbackForTest) ||
        endpoint.host.trim().isEmpty || endpoint.userInfo.isNotEmpty) {
      throw StateError(
        'A Central exige conexão HTTPS válida.',
      );
    }
    final encodedBody = jsonEncode(payload);""",
    'initial HTTPS endpoint')
one(net,
    "          uri = uri.resolve(location);\n          redirectedToTemporaryHost =",
    """          final target = uri.resolve(location);
          if (!isAllowedCentralRedirect(endpoint, target)) {
            throw StateError(
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
  static bool _isAuthorizedScriptRedirectHost(String host) {
    final value = host.toLowerCase();
    return value == 'script.google.com' ||
        value == 'script.googleusercontent.com' ||
        value.endsWith('.googleusercontent.com');
  }

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
    return _isAuthorizedScriptRedirectHost(source) &&
        _isAuthorizedScriptRedirectHost(destination);
  }

  static bool _isTemporaryGoogleHost(Uri uri) {""",
    'redirect allowlist')
# Never persist insecure endpoint in release config; existing service selectors
# already enforce HTTPS. Do not touch server auth or token serialization.
version=('3.29.104+246','3.29.105+247') if platform=='android' else ('3.30.28+215','3.30.29+216')
one(pub,'version: '+version[0],'version: '+version[1],'version bump')
print('REPORT_50_AND_CENTRAL_REDIRECT_PATCH_OK',platform,version[1])
