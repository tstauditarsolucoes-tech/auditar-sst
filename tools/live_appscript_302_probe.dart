import 'dart:convert';
import '../lib/services/apps_script_http.dart';

const endpoint='https://script.google.com/macros/s/AKfycbxNG-wU-jZMKMR2cb1nR9OUd31GSUpGM0FIEagZEUP7sAHxkahLDuJ6T3wZvEe9rm6WrQ/exec';
Future<void> main() async {
  for (final forced in [false,true]) {
    AppsScriptHttp.forceAndroidDirectForTesting=forced;
    final stopwatch=Stopwatch()..start();
    try {
      final response=await AppsScriptHttp.postJson(
        Uri.parse(endpoint),
        {'action':'health_check'},
        timeout: const Duration(seconds:25),
      );
      stopwatch.stop();
      final body=utf8.decode(response.bodyBytes,allowMalformed:true);
      print('REDIRECT_PROBE forcedAndroid=$forced status=${response.statusCode} json=${body.trimLeft().startsWith('{')} elapsedMs=${stopwatch.elapsedMilliseconds} locationHost=${Uri.tryParse(response.headers['location']??'')?.host??''}');
      if (response.statusCode!=200 || !body.trimLeft().startsWith('{')) {
        throw StateError('Fluxo redirect nao concluiu em JSON: status=${response.statusCode}');
      }
    } catch(e) {
      stopwatch.stop();
      print('REDIRECT_PROBE_ERROR forcedAndroid=$forced elapsedMs=${stopwatch.elapsedMilliseconds} type=${e.runtimeType}');
      rethrow;
    }
  }
}
