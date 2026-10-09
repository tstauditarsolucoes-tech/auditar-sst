import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:path_provider/path_provider.dart';
import '../database.dart';
import 'apps_script_http.dart';
import 'auth_service.dart';
import 'offline_reasoning.dart';

/// Fila e cache separados: não usa device_sync, não guarda fotos ou ocorrências.
/// A gravação local existente é preservada mesmo que a Central esteja offline.
class OfflineKnowledgeCloudService {
  OfflineKnowledgeCloudService._();
  static Future<void> _files = Future<void>.value();
  static Future<void>? _active;
  static DateTime? _lastAttempt;
  static String? get _user {
    final id=(AuthService.currentUser?.id ?? '')
      .replaceAll(RegExp(r'[^a-zA-Z0-9_-]'),'_');
    return id.isEmpty ? null : id.substring(0,id.length>64?64:id.length);
  }
  static Future<File?> _file(String name) async {
    final id=_user;
    if(id==null) return null;
    final dir=await getApplicationSupportDirectory();
    return File(dir.path+'/auditar_sst/'+name+'_v1_'+id+'.json');
  }
  static Future<Map<String,dynamic>> _read(File? f) async {
    if(f==null) return {};
    for(final path in [f.path,f.path+'.bak']) {
      try {
        final source=File(path);
        if(!await source.exists()) continue;
        final data=jsonDecode(await source.readAsString());
        if(data is Map) return Map<String,dynamic>.from(data);
      } catch (_) {}
    }
    return {};
  }
  static Future<void> _write(File f,Map<String,dynamic> data) async {
    await f.parent.create(recursive:true);
    final temp=File(f.path+'.tmp');
    await temp.writeAsString(jsonEncode(data),flush:true);
    final backup=File(f.path+'.bak');
    if(await f.exists()) {
      if(await backup.exists()) await backup.delete();
      await f.rename(backup.path);
    }
    await temp.rename(f.path);
  }
  static Future<T> _locked<T>(Future<T> Function() action) {
    final future=_files.then((_)=>action());
    _files=future.then<void>((_) {},onError:(Object _,StackTrace __){});
    return future;
  }
  static String? _rule(String id) {
    if(!id.startsWith('auto-')) return null;
    try {
      final b=id.substring(5);
      final decoded=utf8.decode(base64Url.decode(b.padRight(((b.length+3)~/4)*4,'=')));
      final rule=decoded.split('|').first;
      return RegExp(r'^[a-z][a-z0-9-]{1,70}$').hasMatch(rule) && rule!='model'
        ? rule : null;
    } catch (_) { return null; }
  }
  static bool _safe(String text) =>
    !RegExp(r'@|\b(?:cnpj|cpf)\b|\b\d{11}\b|\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b',
      caseSensitive:false).hasMatch(text);
  static Map<String,dynamic>? _shareable(Map raw,{int revision=0}) {
    final id=''+(raw['id'] ?? '').toString();
    final rule=_rule(id);
    if(rule==null||id.length>190) return null;
    final technical=OfflineReasoning.rules.where((r)=>r.id==rule).firstOrNull;
    if(technical==null) return null;
    String take(String k,int max) {
      final s=''+(raw[k] ?? '').toString().trim().replaceAll(RegExp(r'\s+'),' ');
      return s.length<=max ? s : '';
    }
    // Canonical cloud key never contains the user's free-text title.
    final sharedId='auto-'+base64Url.encode(
      utf8.encode(rule+'|'+technical.title.toLowerCase())).replaceAll('=','');
    final title=technical.title,desc=take('description',220),
      risk=take('risk',350),consequence=take('possibleConsequence',350),
      recommendation=take('recommendation',650),priority=take('priority',15);
    if(title.isEmpty||desc.isEmpty||risk.isEmpty||recommendation.isEmpty||
       !['Baixa','Média','Alta','Crítica'].contains(priority)||
       ![title,desc,risk,consequence,recommendation].every(_safe)) return null;
    return {'id':sharedId,'ruleId':rule,'title':title,'description':desc,'risk':risk,
      'possibleConsequence':consequence,'recommendation':recommendation,
      'priority':priority,'baseVersion':revision};
  }
  static Future<List<Map<String,dynamic>>> cachedModels() async {
    final state=await _read(await _file('offline_knowledge_cache'));
    return [for(final r in (state['items'] is List?state['items'] as List:const []))
      if(r is Map) Map<String,dynamic>.from(r)];
  }
  /// Chamado após aprendizado local confirmado: enfileira sem depender da rede.
  static Future<void> queueApplied(Map<String,dynamic> local) async {
    final outbox=await _file('offline_knowledge_outbox');
    if(outbox==null) return;
    await _locked(() async {
      final state=await _read(outbox);
      final cache=await cachedModels();
      final canonical=_shareable(local);
      if(canonical==null) return;
      final id=canonical['id'] as String;
      final pending=<Map<String,dynamic>>[
        for(final r in (state['pending'] is List?state['pending'] as List:const []))
          if(r is Map) Map<String,dynamic>.from(r)];
      final old=pending.where((m)=>m['id']==id).firstOrNull;
      final remote=cache.where((m)=>m['id']==id).firstOrNull;
      final rawRevision=old?['baseVersion']??remote?['version']??0;
      final revision=rawRevision is num?rawRevision.toInt():int.tryParse('$rawRevision')??0;
      final model=_shareable(local,revision:revision);
      if(model==null) return;
      pending.removeWhere((m)=>m['id']==id);
      pending.insert(0,model);
      // Sem perda silenciosa em caso de fila cheia.
      if(pending.length>500) {
        throw StateError('Limite da fila online; correção local preservada.');
      }
      await _write(outbox,{...state,'pending':pending});
    });
    schedule(force:true);
  }
  static Future<void> _importOld() => _locked(() async {
    final outbox=await _file('offline_knowledge_outbox');
    if(outbox==null) return;
    final state=await _read(outbox);
    if(state['legacyImported']==true) return;
    final dir=await getApplicationSupportDirectory();
    final old=await _read(File(dir.path+'/offline_reasoning_learning_v1.json'));
    final pending=<Map<String,dynamic>>[
      for(final r in (state['pending'] is List?state['pending'] as List:const []))
        if(r is Map) Map<String,dynamic>.from(r)];
    final ids=pending.map((m)=>m['id']).toSet();
    if(old['templates'] is List) {
      for(final raw in old['templates'] as List) {
        if(raw is! Map) continue;
        final model=_shareable(raw);
        if(model!=null && ids.add(model['id']) && pending.length<500) pending.add(model);
      }
    }
    await _write(outbox,{...state,'pending':pending,'legacyImported':true});
  });
  static void schedule({bool force=false}) {
    if(!AuthService.isSignedIn || _active!=null) return;
    final now=DateTime.now();
    if(!force&&_lastAttempt!=null&&
      now.difference(_lastAttempt!)<const Duration(minutes:5)) return;
    _lastAttempt=now;
    unawaited(sync().catchError((Object _) {}));
  }
  static Future<void> sync() {
    if(_active!=null) return _active!;
    late final Future<void> future;
    future=_sync().whenComplete(() {if(identical(_active,future)) _active=null;});
    _active=future;
    return future;
  }
  static Future<void> _sync() async {
    final user=_user;
    if(user==null||!AuthService.isSignedIn||
      AuthService.currentUser?.role.toLowerCase()=='cliente') return;
    final endpoint=(await AppDatabase.instance.getSetting('management_panel_endpoint')).trim();
    if(!endpoint.startsWith('https://')) return;
    await _importOld();
    final outbox=await _file('offline_knowledge_outbox');
    final state=await _read(outbox);
    final pending=<Map<String,dynamic>>[
      for(final r in (state['pending'] is List?state['pending'] as List:const []))
        if(r is Map) Map<String,dynamic>.from(r)];
    final sent=pending.take(20).toList();
    final response=await AppsScriptHttp.postJson(Uri.parse(endpoint),
      {'action':'offline_knowledge_sync_v1','authToken':AuthService.sessionToken,
       'changes':sent,'cursor':0,'limit':80},timeout:const Duration(seconds:25));
    if(response.statusCode!=200) throw StateError('Central indisponível.');
    final body=jsonDecode(response.body);
    if(body is! Map||body['ok']!=true||body['accepted'] is! List||
      body['items'] is! List) throw StateError('Canal de modelos não instalado na Central.');
    if(user!=_user||!AuthService.isSignedIn) return;
    final accepted={
      for(final r in body['accepted'] as List) if(r is Map) r['id'].toString()
    };
    await _locked(() async {
      final latest=await _read(outbox);
      final queue=<Map<String,dynamic>>[
        for(final r in (latest['pending'] is List?latest['pending'] as List:const []))
          if(r is Map) Map<String,dynamic>.from(r)];
      queue.removeWhere((m)=>accepted.contains(m['id'])&&sent.any((s)=>
        s['id']==m['id']&&s['risk']==m['risk']&&s['recommendation']==m['recommendation']));
      if(outbox!=null) await _write(outbox,{...latest,'pending':queue});
      final cacheFile=await _file('offline_knowledge_cache');
      if(cacheFile==null) return;
      final previous=await _read(cacheFile);
      final byId=<String,Map<String,dynamic>>{
        for(final r in (previous['items'] is List?previous['items'] as List:const []))
          if(r is Map&&r['id'] is String) r['id'] as String:Map<String,dynamic>.from(r)
      };
      for(final r in body['items'] as List) {
        if(r is! Map || _shareable(r)==null) continue;
        byId[r['id'].toString()]=Map<String,dynamic>.from(r);
      }
      await _write(cacheFile,{'items':byId.values.toList().reversed.take(120).toList()});
    });
  }
}
