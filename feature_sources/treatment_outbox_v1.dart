import 'dart:async';
import 'dart:convert';
import 'dart:math';

class TreatmentRejected implements Exception {
  TreatmentRejected(this.message);
  final String message;
  @override String toString() => message;
}
class TreatmentScopeChanged implements Exception {}

/// Independent durable outbox. No SST database, credentials, photos or sync APIs.
/// All operations are serialized, including acknowledgements, to prevent lost writes.
class TreatmentOutbox {
  TreatmentOutbox({required this.read, required this.write});
  final Future<String?> Function(String key) read;
  final Future<void> Function(String key, String value) write;
  Future<void> _tail = Future<void>.value();
  static String scope(String endpoint, String userId) =>
      'auditar_treatment_outbox_v1_' + base64Url.encode(utf8.encode(jsonEncode([endpoint,userId])));
  Future<T> _serial<T>(Future<T> Function() work) {
    final result = _tail.then((_) => work());
    _tail = result.then<void>((_) {}, onError: (Object _, StackTrace __) {});
    return result;
  }
  Future<List<Map<String,dynamic>>> _read(String scope) async {
    final raw = await read(scope);
    if (raw == null) return [];
    final value = jsonDecode(raw);
    if (value is! List || value.any((x) => x is! Map || x['record'] is! Map ||
        x['id'] is! String || x['companyId'] is! String || x['topicId'] is! String)) {
      throw StateError('Não foi possível ler a fila. Os dados foram preservados.');
    }
    return value.map((x) => Map<String,dynamic>.from(x as Map)).toList();
  }
  Future<void> _save(String scope, List<Map<String,dynamic>> items) => write(scope,jsonEncode(items));
  Future<List<Map<String,dynamic>>> list(String scope) => _serial(() => _read(scope));
  Future<String> enqueue(String scope, String companyId, String topicId,
      String title, Map<String,dynamic> record) => _serial(() async {
    final items = await _read(scope);
    if (items.length >= 100) throw StateError('A fila tem 100 mensagens. Resolva os envios pendentes antes de adicionar outras.');
    if (companyId.isEmpty || topicId.isEmpty || (record['message']??'').toString().trim().isEmpty) {
      throw StateError('Empresa, assunto e mensagem são obrigatórios.');
    }
    final id = 'app_'+DateTime.now().microsecondsSinceEpoch.toString()+'_'+
        List.generate(12, (_) => Random.secure().nextInt(256).toRadixString(16).padLeft(2,'0')).join();
    final safe = Map<String,dynamic>.from(jsonDecode(jsonEncode(record)) as Map);
    safe['requestId'] = id;
    items.add({'id':id,'companyId':companyId,'topicId':topicId,'title':title,
      'record':safe,'createdAt':DateTime.now().toUtc().toIso8601String(),
      'blocked':false,'error':''});
    await _save(scope,items); // The editor may clear only after this succeeds.
    return id;
  });
  Future<void> discard(String scope,String id) => _serial(() async {
    final items = await _read(scope);items.removeWhere((x)=>x['id']==id);await _save(scope,items);
  });
  Future<void> retry(String scope) => _serial(() async {
    final items = await _read(scope);
    for(final x in items){x['blocked']=false;x['error']='';}
    await _save(scope,items);
  });
  Future<int> flush(String scope, Future<void> Function(Map<String,dynamic>) send) => _serial(() async {
    final items = await _read(scope);int sent=0;
    while(items.isNotEmpty){
      final item=items.first;
      if(item['blocked']==true) break; // Preserve order; rejected text requires an explicit decision.
      try {
        await send(Map<String,dynamic>.from(jsonDecode(jsonEncode(item)) as Map));
      } on TreatmentScopeChanged {
        break; // Do not send another user's/endpoint's queue.
      } on TreatmentRejected catch(e) {
        item['blocked']=true;item['error']=e.message;await _save(scope,items);break;
      } catch(_) {
        item['error']='Envio ainda não confirmado. Nova tentativa com a mesma identificação.';
        await _save(scope,items);break;
      }
      items.removeAt(0);
      await _save(scope,items); // Failed save leaves the stored ID available for idempotent retry.
      sent++;
    }
    return sent;
  });
}
