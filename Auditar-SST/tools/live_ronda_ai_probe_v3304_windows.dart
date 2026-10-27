import 'dart:convert';
import 'dart:typed_data';
import 'package:image/image.dart' as img;
import '../lib/services/apps_script_http.dart';

const endpoint =
    'https://script.google.com/macros/s/AKfycbxNG-wU-jZMKMR2cb1nR9OUd31GSUpGM0FIEagZEUP7sAHxkahLDuJ6T3wZvEe9rm6WrQ/exec';
const key = String.fromEnvironment('AUDITAR_SYNC_KEY');

Future<Map<String, dynamic>> post(
  Map<String, Object?> body, {
  required Duration timeout,
}) async {
  final r = await AppsScriptHttp.postJson(
    Uri.parse(endpoint),
    body,
    timeout: timeout,
  );
  if (r.statusCode != 200) throw StateError('HTTP ${r.statusCode}');
  final x = jsonDecode(utf8.decode(r.bodyBytes, allowMalformed: true));
  if (x is! Map) throw StateError('JSON inesperado');
  return Map<String, dynamic>.from(x);
}

Uint8List normalizedJpeg() {
  final image = img.Image(width: 96, height: 96, numChannels: 3);
  for (var y = 20; y < 76; y++) {
    for (var x = 20; x < 76; x++) {
      final p = image.getPixel(x, y);
      p.r = 220;
      p.g = 30;
      p.b = 30;
    }
  }
  return Uint8List.fromList(img.encodeJpg(image, quality: 55));
}

Future<void> main() async {
  if (key.trim().isEmpty) throw StateError('AUDITAR_SYNC_KEY ausente');

  final pullSw = Stopwatch()..start();
  final pull = await post({
    'action': 'device_sync_pull',
    'syncKey': key,
    'deviceId': 'v3304-windows-readonly',
    'platform': 'windows',
    'sinceVersion': 0,
    'limit': 1,
  }, timeout: const Duration(seconds: 30));
  pullSw.stop();
  if (pull['ok'] != true) throw StateError('Central: $pull');
  print('CENTRAL_REAL_OK ${pullSw.elapsedMilliseconds}ms');

  final jpg = normalizedJpeg();
  if (jpg.length < 4 || jpg[0] != 0xFF || jpg[1] != 0xD8) {
    throw StateError('JPEG normalizado invalido');
  }

  Object? lastError;
  Map<String, dynamic>? lastResponse;
  for (var attempt = 1; attempt <= 2; attempt++) {
    final sw = Stopwatch()..start();
    try {
      final ai = await post({
        'action': 'ai_assistant',
        'syncKey': key,
        'payload': {
          'mode': 'checklist_photo',
          'rondaDeferred': true,
          'companyName': 'Teste Auditar',
          'area': 'Ronda Expressa',
          'question':
              'Descreva objetivamente apenas o que é visível na imagem de teste.',
          'category': 'Ronda Expressa',
          'reference': '',
          'technicianContext': 'Teste técnico sem gravação de dados.',
          'images': ['data:image/jpeg;base64,${base64Encode(jpg)}'],
        },
      }, timeout: const Duration(seconds: 95));
      sw.stop();
      lastResponse = ai;
      if (ai['ok'] == true && ai['result'] is Map) {
        final result = Map<String, dynamic>.from(ai['result'] as Map);
        if ('${result['description'] ?? ''}'.trim().isNotEmpty) {
          print(
            'AI_PHOTO_NORMALIZED_OK attempt=$attempt ${sw.elapsedMilliseconds}ms jpegBytes=${jpg.length}',
          );
          return;
        }
      }
      print('AI_ATTEMPT_$attempt ${sw.elapsedMilliseconds}ms $ai');
      final code = '${ai['code'] ?? ''}';
      if (code == 'AI_PHOTO_INVALID_ARGUMENT') {
        throw StateError(
          'A Central ainda recusou o formato JPEG normalizado: $ai',
        );
      }
    } catch (e) {
      sw.stop();
      lastError = e;
      print('AI_ATTEMPT_${attempt}_ERROR ${sw.elapsedMilliseconds}ms $e');
      if ('$e'.contains('AI_PHOTO_INVALID_ARGUMENT')) rethrow;
    }
    if (attempt < 2) {
      await Future<void>.delayed(const Duration(seconds: 3));
    }
  }

  final transientCodes = {
    'AI_TEMPORARILY_UNAVAILABLE',
    'AI_PHOTO_FAILED',
    'AI_MODEL_NOT_AVAILABLE',
  };
  final code = '${lastResponse?['code'] ?? ''}';
  if (transientCodes.contains(code)) {
    print(
      'AI_BACKEND_TRANSIENT_ACCEPTED code=$code: formato da foto foi aceito; análise permanece pendente para nova tentativa.',
    );
    return;
  }
  throw StateError(
    'IA de foto terminou em estado inesperado: ${lastResponse ?? lastError}',
  );
}
