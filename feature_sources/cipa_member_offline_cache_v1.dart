import 'dart:convert';
import 'dart:io';
import 'dart:math';

import 'package:cryptography/cryptography.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:path_provider/path_provider.dart';

import 'cipa_member_draft_store.dart';
import 'cipa_member_identity.dart';
import 'cipa_member_portal_policy.dart';

/// Autorização do servidor é indispensável antes da primeira ativação offline.
/// O PIN só desbloqueia uma cópia que o próprio servidor já filtrou.
abstract class CipaOfflineSecretVault {
  Future<String?> read(String key);
  Future<void> write(String key,String value);
  Future<void> delete(String key);
}

class CipaSecureOfflineVault implements CipaOfflineSecretVault {
  const CipaSecureOfflineVault();
  static const FlutterSecureStorage _storage=FlutterSecureStorage();

  @override Future<String?> read(String key)=>_storage.read(key:key);
  @override Future<void> write(String key,String value)=>
    _storage.write(key:key,value:value);
  @override Future<void> delete(String key)=>_storage.delete(key:key);
}

class CipaOfflineSnapshot {
  const CipaOfflineSnapshot({required this.view,required this.syncedAt});
  final CipaMemberView view;
  final DateTime syncedAt;
}

class CipaOfflineSnapshotCodec {
  const CipaOfflineSnapshotCodec._();
  static const _maxItems=550;

  static Map<String,dynamic> encode(CipaOfflineSnapshot snapshot) {
    final profile=snapshot.view.profile;
    final v=snapshot.view;
    Map<String,dynamic> item(CipaMemberItem value)=> {
      'id':value.id,'companyId':value.companyId,
      'mandateId':value.mandateId,'type':value.type.name,
      'title':value.title,'description':value.description,
      'feedback':value.feedback,'reviewId':value.reviewId,
      'feedbackRead':value.feedbackRead,'status':value.status,
      'assignedMemberId':value.assignedMemberId,
      'visibleToAllMembers':value.visibleToAllMembers,
      'date':value.date?.toUtc().toIso8601String(),
      'dueDate':value.dueDate?.toUtc().toIso8601String(),
    };
    final rows=<CipaMemberItem>[
      ...v.meetings,...v.myActions,...v.notices,...v.trainings,
      ...v.documents,...v.observations,...v.reminders,
      ...v.scheduledInspections,
    ];
    if(rows.length>_maxItems)throw StateError('Lista offline muito extensa');
    return {
      'version':1,'syncedAt':snapshot.syncedAt.toUtc().toIso8601String(),
      'companyLabel':v.companyLabel,'mandateLabel':v.mandateLabel,
      'profile':{
        'userId':profile.userId,'companyId':profile.companyId,
        'mandateId':profile.mandateId,'memberId':profile.memberId,
        'workerId':profile.workerId,'fullName':profile.fullName,
        'cipaRole':profile.cipaRole,'representation':profile.representation,
        'jobTitle':profile.jobTitle,
      },
      'items':rows.map(item).toList(),
    };
  }

  static CipaOfflineSnapshot decode(Map<String,dynamic> json) {
    if(json['version']!=1)throw StateError('Versão offline incompatível');
    final raw=json['profile'];
    if(raw is! Map)throw StateError('Perfil ausente');
    final p=Map<String,dynamic>.from(raw);
    String get(String name)=>(p[name]??'').toString();
    final profile=CipaMemberProfileContract.fromVerifiedMembership(
      authenticatedUserId:get('userId'),
      grantedCompanyId:get('companyId'),
      grantedMandateId:get('mandateId'),
      grantedMemberId:get('memberId'),
      membershipUserId:get('userId'),
      membershipCompanyId:get('companyId'),
      membershipMandateId:get('mandateId'),
      membershipMemberId:get('memberId'),
      membershipWorkerId:get('workerId'),
      fullName:get('fullName'),cipaRole:get('cipaRole'),
      representation:get('representation'),jobTitle:get('jobTitle'),
      userActive:true,mandateActive:true,memberActive:true,
    );
    final syncedAt=DateTime.tryParse((json['syncedAt']??'').toString());
    if(profile==null||syncedAt==null)throw StateError('Vínculo offline inválido');
    final rawItems=json['items'];
    if(rawItems is! List||rawItems.length>_maxItems)
      throw StateError('Registros offline inválidos');
    final records=<CipaMemberItem>[];
    for(final rawItem in rawItems){
      if(rawItem is! Map)throw StateError('Registro offline inválido');
      final r=Map<String,dynamic>.from(rawItem);
      String field(String key)=>(r[key]??'').toString();
      final types=CipaMemberItemType.values.where(
        (type)=>type.name==field('type')).toList();
      if(types.length!=1||field('id').trim().isEmpty||
         field('companyId')!=profile.companyId||
         field('mandateId')!=profile.mandateId)
        throw StateError('Registro fora do vínculo');
      final t=types.single;
      final assigned=field('assignedMemberId');
      final shared=r['visibleToAllMembers']==true;
      final isPrivate=t==CipaMemberItemType.action||
        t==CipaMemberItemType.meeting||
        t==CipaMemberItemType.training||
        t==CipaMemberItemType.observation||
        t==CipaMemberItemType.reminder||
        t==CipaMemberItemType.scheduledInspection;
      if(isPrivate?assigned!=profile.memberId:!shared)
        throw StateError('Registro não autorizado');
      final date=field('date'),due=field('dueDate');
      records.add(CipaMemberItem(
        id:field('id'),type:t,title:field('title'),
        companyId:field('companyId'),mandateId:field('mandateId'),
        assignedMemberId:assigned,visibleToAllMembers:shared,
        description:field('description'),feedback:field('feedback'),
        reviewId:field('reviewId'),feedbackRead:r['feedbackRead']==true,
        status:field('status'),
        date:date.isEmpty?null:DateTime.tryParse(date),
        dueDate:due.isEmpty?null:DateTime.tryParse(due),
      ));
    }
    return CipaOfflineSnapshot(
      syncedAt:syncedAt.toUtc(),
      view:CipaMemberPortalRules.build(verifiedProfile:profile,
        records:records,
        companyLabel:(json['companyLabel']??'Empresa CIPA').toString(),
        mandateLabel:(json['mandateLabel']??'Mandato').toString()),
    );
  }
}

/// Consulta offline opcional: PIN pessoal + KeyStore + arquivo AES-256-GCM.
/// Nunca persiste sessão, senha de e-mail ou chave de sincronização do app SST.
/// Ao trocar de mandato, conta ou empresa, invalida o conteúdo anterior.
class CipaMemberOfflineCache {
  CipaMemberOfflineCache({
    CipaOfflineSecretVault? vault,
    Future<Directory> Function()? directory,
    DateTime Function()? clock,
  }):_vault=vault??const CipaSecureOfflineVault(),
     _directory=directory??getApplicationSupportDirectory,
     _clock=clock??DateTime.now;
  final CipaOfflineSecretVault _vault;
  final Future<Directory> Function() _directory;
  final DateTime Function() _clock;
  static const Duration validity=Duration(hours:24);
  static const int maxWrongPins=5;
  static const int _iterations=120000;

  static bool validPin(String value)=>RegExp(r'^\d{6}$').hasMatch(value);
  static bool validEmail(String value)=>
    RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$').hasMatch(value.trim());

  Future<String> _label(String email) async {
    if(!validEmail(email))throw StateError('Informe o e-mail cadastrado');
    final d=await Sha256().hash(utf8.encode(email.trim().toLowerCase()));
    return base64UrlEncode(d.bytes).replaceAll('=','');
  }
  Future<String> _path(String email) async {
    final dir=await _directory();
    return '${dir.path}/cipa_offline_${await _label(email)}.enc';
  }
  Future<String> _key(String email,String name) async=>
    'cipa_offline_${await _label(email)}_$name';
  Future<String> _scope(CipaMemberView view) async {
    final p=view.profile;
    final hash=await Sha256().hash(utf8.encode([
      p.userId,p.companyId,p.mandateId,p.memberId,
    ].join('|')));
    return base64UrlEncode(hash.bytes).replaceAll('=','');
  }
  Future<List<int>> _derivePin(String pin,List<int> salt) async {
    final k=await Pbkdf2(macAlgorithm:Hmac.sha256(),
      iterations:_iterations,bits:256).deriveKey(
        secretKey:SecretKey(utf8.encode(pin)),nonce:salt);
    return k.extractBytes();
  }
  static bool _equals(List<int> a,List<int> b){
    if(a.length!=b.length)return false;
    var diff=0;
    for(var i=0;i<a.length;i++)diff|=a[i]^b[i];
    return diff==0;
  }
  Future<List<int>> _getKey(String email) async {
    final value=await _vault.read(await _key(email,'aes'));
    if(value==null)throw StateError('Cache offline não autorizado');
    final data=base64Decode(value);
    if(data.length!=32)throw StateError('Chave local inválida');
    return data;
  }
  Future<bool> isEnabled(String email) async {
    if(!validEmail(email))return false;
    final path=await _path(email);
    return await File(path).exists()&&
      await _vault.read(await _key(email,'aes'))!=null&&
      await _vault.read(await _key(email,'pin'))!=null;
  }

  /// Só chamar após uma autenticação individual online confirmada.
  Future<void> enroll(String email,String pin,CipaMemberView verified) async {
    if(!validPin(pin))throw StateError('Defina um PIN de 6 números');
    if(!validEmail(email))throw StateError('E-mail inválido');
    final rand=Random.secure();
    final key=List<int>.generate(32,(_)=>rand.nextInt(256));
    final salt=List<int>.generate(16,(_)=>rand.nextInt(256));
    final hash=await _derivePin(pin,salt);
    // O conteúdo novo é escrito antes de liberar o PIN da conta.
    final payload=CipaOfflineSnapshotCodec.encode(CipaOfflineSnapshot(
      view:verified,syncedAt:_clock().toUtc()));
    final encrypted=await CipaDraftCipher.seal(payload,key);
    final path=await _path(email);
    final temp=File('$path.next');
    await temp.writeAsString(encrypted,flush:true);
    await temp.rename(path);
    await _vault.write(await _key(email,'aes'),base64Encode(key));
    await _vault.write(await _key(email,'pin'),
      '${base64Encode(salt)}:${base64Encode(hash)}');
    await _vault.write(await _key(email,'scope'),await _scope(verified));
    await _vault.write(await _key(email,'fails'),'0');
  }

  /// Atualiza automaticamente SOMENTE com resposta online válida do servidor.
  Future<void> updateFromServer(String email,CipaMemberView verified) async {
    if(!await isEnabled(email))return;
    final scope=await _vault.read(await _key(email,'scope'));
    if(scope!=await _scope(verified)){
      await clear(email); // nunca abrir dados de outro mandato com PIN antigo
      return;
    }
    final encrypted=await CipaDraftCipher.seal(
      CipaOfflineSnapshotCodec.encode(CipaOfflineSnapshot(
        view:verified,syncedAt:_clock().toUtc())),
      await _getKey(email));
    final path=await _path(email);
    final tmp=File('$path.next');
    await tmp.writeAsString(encrypted,flush:true);
    await tmp.rename(path);
  }

  Future<CipaOfflineSnapshot> unlock(String email,String pin) async {
    if(!await isEnabled(email))throw StateError(
      'Offline não foi ativado nesta conta neste aparelho');
    final failName=await _key(email,'fails');
    final failures=int.tryParse(await _vault.read(failName)??'0')??0;
    if(failures>=maxWrongPins)throw StateError(
      'Acesso offline bloqueado. Entre com código por e-mail.');
    final record=await _vault.read(await _key(email,'pin'));
    final parts=record?.split(':')??[];
    if(parts.length!=2)throw StateError('PIN local não configurado');
    if(!validPin(pin)){
      await _vault.write(failName,'${failures+1}');
      throw StateError('PIN offline incorreto');
    }
    final actual=await _derivePin(pin,base64Decode(parts[0]));
    if(!_equals(actual,base64Decode(parts[1]))){
      await _vault.write(failName,'${failures+1}');
      throw StateError('PIN offline incorreto');
    }
    final file=File(await _path(email));
    final plain=await CipaDraftCipher.open(
      await file.readAsString(),await _getKey(email));
    final snapshot=CipaOfflineSnapshotCodec.decode(plain);
    final now=_clock().toUtc();
    if(snapshot.syncedAt.isAfter(now.add(const Duration(minutes:5)))||
       now.difference(snapshot.syncedAt)>validity)
      throw StateError('Dados offline vencidos. Conecte-se para atualizar.');
    if(await _scope(snapshot.view)!=
       await _vault.read(await _key(email,'scope')))
      throw StateError('Conta/mandato do cache não confere.');
    await _vault.write(failName,'0');
    return snapshot;
  }

  Future<void> clear(String email) async {
    if(!validEmail(email))return;
    for(final suffix in ['aes','pin','scope','fails']){
      await _vault.delete(await _key(email,suffix));
    }
    final path=await _path(email);
    final file=File(path);
    if(await file.exists())await file.delete();
  }
}
