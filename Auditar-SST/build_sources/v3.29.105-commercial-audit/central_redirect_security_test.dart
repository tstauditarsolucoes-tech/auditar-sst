import 'package:auditar_sst/services/apps_script_http.dart';
import 'package:flutter_test/flutter_test.dart';
void main() {
  test('Central redirects stay HTTPS and on authorized hosts', () {
    final origin = Uri.parse('https://script.google.com/macros/s/ex/exec');
    bool accepts(String target) => AppsScriptHttp.isAllowedCentralRedirect(
      origin, origin.resolve(target));
    expect(accepts('/macros/s/ex/exec'), isTrue);
    expect(accepts('https://script.googleusercontent.com/macros/echo'), isTrue);
    expect(accepts('https://abc.script.googleusercontent.com/macros/echo'), isTrue);
    expect(accepts('http://script.googleusercontent.com/macros/echo'), isFalse);
    expect(accepts('https://script.google.com.evil.example/'), isFalse);
    expect(accepts('https://example.com/collect'), isFalse);
    expect(accepts('https://user:pw@script.google.com/'), isFalse);
    expect(accepts('https://script.google.com:444/'), isFalse);
  });
  test('custom HTTPS Central can only redirect within its own host', () {
    final origin = Uri.parse('https://central.example.com/exec');
    expect(AppsScriptHttp.isAllowedCentralRedirect(
      origin, Uri.parse('https://central.example.com/next')), isTrue);
    expect(AppsScriptHttp.isAllowedCentralRedirect(
      origin, Uri.parse('https://script.googleusercontent.com/macros/echo')), isFalse);
    expect(AppsScriptHttp.isAllowedCentralRedirect(
      origin, Uri.parse('http://central.example.com/next')), isFalse);
  });
}
