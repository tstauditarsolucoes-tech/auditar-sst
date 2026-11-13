import 'dart:convert';
import 'dart:io';
import 'dart:math';
import 'dart:typed_data';

import 'package:cryptography/cryptography.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:path_provider/path_provider.dart';

/// Apenas o conteúdo desta vistoria (incluindo até 2 fotos já reduzidas).
/// Não contém token de sessão, e-mail, dados de pessoas nem chave da Central.
class CipaInspectionDraft {
  const CipaInspectionDraft({
    required this.requestId,required this.category,required this.place,
    required this.answers,required this.observation,required this.photos,
    required this.savedAt,
  });
  final String requestId,category,place,observation;
  final List<String?> answers;
  final List<Uint8List> photos;
  final DateTime savedAt;

  Map<String,dynamic> toJson()=>{
    'version':1,'requestId':requestId,'category':category,'place':place,
    'answers':answers,'observation':observation,
    'photos':photos.map(base64Encode).toList(),
    'savedAt':savedAt.toUtc().toIso8601String(),
  };

  static CipaInspectionDraft? fromJson(Map<String,dynamic> data){
    if(data['version']!=1)return null;
    final id=(data['requestId']??'').toString();
    final topic=(data['category']??'').toString();
    final place=(data['place']??'').toString();
    final note=(data['observation']??'').toString();
    final answers=data['answers'],images=data['photos'];
    final saved=DateTime.tryParse((data['savedAt']??'').toString());
    if(!RegExp(r'^[A-Za-z0-9_-]{16,120}$').hasMatch(id)||
       topic.isEmpty||topic.length>80||place.length>120||
       note.length>250||saved==null||answers is! List||
       answers.length!=3||images is! List||images.length>2)return null;
    if(DateTime.now().difference(saved.toUtc()).inDays>7)return null;
    const choices=['Sim','Não','Não sei/não verifiquei'];
    if(answers.any((v)=>v!=null&&!choices.contains(v)))return null;
    final photos=<Uint8List>[];
    try {
      for(final item in images) {
        if(item is! String||item.length>950000)return null;
        final bytes=base64Decode(item);
        if(bytes.length>700000)return null;
        photos.add(bytes);
      }
    }catch(_){return null;}
    return CipaInspectionDraft(requestId:id,category:topic,place:place,
      answers:answers.cast<String?>().toList(),
      observation:note,photos:photos,savedAt:saved.toUtc());
  }
}

/// AES-256-GCM autenticado. Qualquer adulteração de arquivo é recusada.
class CipaDraftCipher {
  static final AesGcm algorithm=AesGcm.with256bits();

  static Future<String> seal(Map<String,dynamic> data,List<int> key) async {
    if(key.length!=32)throw StateError('Chave inválida');
    final nonce=List<int>.generate(12,(_)=>Random.secure().nextInt(256));
    final box=await algorithm.encrypt(utf8.encode(jsonEncode(data)),
      secretKey:SecretKey(key),nonce:nonce);
    return jsonEncode({
      'format':1,'nonce':base64Encode(box.nonce),
      'ciphertext':base64Encode(box.cipherText),
      'tag':base64Encode(box.mac.bytes),
    });
  }

  static Future<Map<String,dynamic>> open(String encrypted,List<int> key) async {
    if(key.length!=32)throw StateError('Chave inválida');
    final wrapper=jsonDecode(encrypted);
    if(wrapper is! Map||wrapper['format']!=1)throw StateError('Rascunho inválido');
    final box=SecretBox(
      base64Decode(wrapper['ciphertext'] as String),
      nonce:base64Decode(wrapper['nonce'] as String),
      mac:Mac(base64Decode(wrapper['tag'] as String)));
    final plain=await algorithm.decrypt(box,secretKey:SecretKey(key));
    final decoded=jsonDecode(utf8.decode(plain));
    if(decoded is! Map)throw StateError('Rascunho inválido');
    return Map<String,dynamic>.from(decoded);
  }
}

/// Key no armazenamento seguro do SO; somente ciphertext vai para arquivo.
/// Isolado por usuário + empresa + mandato + membro, inclusive no mesmo celular.
/// Resumo de um rascunho local, sem chave nem foto em texto claro.
class CipaStoredDraft {
  const CipaStoredDraft({
    this.draft,this.scheduleId,this.draftId,this.isLegacyFree=false,
    this.warning='',
  });
  final CipaInspectionDraft? draft;
  final String? scheduleId,draftId;
  final bool isLegacyFree;
  final String warning;
  bool get canResume=>draft!=null&&warning.isEmpty;
  bool get complete=>draft!=null&&draft!.place.trim().length>=2 &&
    draft!.answers.length==3&&draft!.answers.every((v)=>v!=null);
  String get displayPlace=>draft?.place.trim().isNotEmpty==true?
    draft!.place.trim():'Local não informado';
}
class CipaMemberDraftStore {
  CipaMemberDraftStore({
    required this.accountId,required this.companyId,
    required this.mandateId,required this.memberId,
    this.scheduleId,this.draftId,
    FlutterSecureStorage? secure,
    Future<Directory> Function()? directory,
    Future<List<int>> Function(bool create)? keyProvider,
  }):_secure=secure??const FlutterSecureStorage(),
     _directory=directory??getApplicationSupportDirectory,
     _keyProvider=keyProvider;

  final String accountId,companyId,mandateId,memberId;
  final String? scheduleId,draftId;
  final FlutterSecureStorage _secure;
  final Future<Directory> Function() _directory;
  final Future<List<int>> Function(bool create)? _keyProvider;

  Future<String> _hash(String value) async {
    final result=await Sha256().hash(utf8.encode(value));
    return base64UrlEncode(result.bytes).replaceAll('=','');
  }
  Future<String> _personHash()=>_hash(
    [accountId,companyId,mandateId,memberId].join('|'));
  Future<String> _prefix() async=>'cipa_draft_${await _personHash()}';
  Future<String> _filePath() async {
    final directory=await _directory();
    final prefix=await _prefix();
    final task=await _hash(scheduleId??(
      draftId==null?'vistoria_livre':'vistoria_livre_$draftId'));
    return '${directory.path}/${prefix}_${task}.enc';
  }
  Future<List<int>> _key({required bool create}) async {
    if(_keyProvider!=null)return _keyProvider(create);
    final keyName='cipa_draft_key_${await _personHash()}';
    String? value=await _secure.read(key:keyName);
    if(value==null){
      if(!create)throw StateError('Chave do rascunho não encontrada');
      final source=Random.secure();
      value=base64Encode(List<int>.generate(32,(_)=>source.nextInt(256)));
      await _secure.write(key:keyName,value:value);
    }
    final key=base64Decode(value);
    if(key.length!=32)throw StateError('Chave do rascunho inválida');
    return key;
  }

  Future<void> save(CipaInspectionDraft draft) async {
    if(draftId!=null&&(draft.requestId!=draftId||scheduleId!=null))
      throw StateError('Vistoria local incompatível');
    final encoded=await CipaDraftCipher.seal(draft.toJson(),
      await _key(create:true));
    final path=await _filePath();
    final tmp=File('$path.next');
    await tmp.writeAsString(encoded,flush:true);
    // Substituição atômica no diretório interno do aplicativo Android.
    await tmp.rename(path);
  }

  Future<CipaInspectionDraft?> load() async {
    final file=File(await _filePath());
    if(!await file.exists())return null;
    final decoded=await CipaDraftCipher.open(
      await file.readAsString(),await _key(create:false));
    final draft=CipaInspectionDraft.fromJson(decoded);
    if(draftId!=null&&draft?.requestId!=draftId)
      throw StateError('Rascunho fora do registro original');
    return draft;
  }

  /// Lista arquivos cifrados do integrante. Preserva rascunhos órfãos ou
  /// corrompidos como avisos; nunca os envia ou exclui automaticamente.
  Future<List<CipaStoredDraft>> listForMember({
    Set<String> scheduledIds=const <String>{},
  }) async {
    final directory=await _directory();
    if(!await directory.exists())return const [];
    final prefix=await _prefix();
    final allowed=<String,String>{};
    for(final id in scheduledIds){
      allowed['${prefix}_${await _hash(id)}.enc']=id;
    }
    final legacyName='${prefix}_${await _hash('vistoria_livre')}.enc';
    final records=<CipaStoredDraft>[];
    await for(final entity in directory.list(followLinks:false)){
      if(entity is! File)continue;
      final name=entity.uri.pathSegments.last;
      if(!name.startsWith('${prefix}_')||!name.endsWith('.enc'))continue;
      try {
        final plain=await CipaDraftCipher.open(
          await entity.readAsString(),await _key(create:false));
        final draft=CipaInspectionDraft.fromJson(plain);
        if(draft==null){
          records.add(const CipaStoredDraft(
            warning:'Rascunho vencido ou não recuperável'));
          continue;
        }
        final freeName=
          '${prefix}_${await _hash('vistoria_livre_${draft.requestId}')}.enc';
        if(name==freeName){
          records.add(CipaStoredDraft(draft:draft,draftId:draft.requestId));
        }else if(name==legacyName){
          records.add(CipaStoredDraft(draft:draft,isLegacyFree:true));
        }else if(allowed.containsKey(name)){
          records.add(CipaStoredDraft(draft:draft,scheduleId:allowed[name]));
        }else{
          records.add(CipaStoredDraft(draft:draft,
            warning:'Agendamento indisponível. Procure o TST.'));
        }
      }catch(_){
        records.add(const CipaStoredDraft(
          warning:'Arquivo protegido não pôde ser aberto'));
      }
      if(records.length>100){
        throw StateError('Muitos arquivos locais; solicite suporte.');
      }
    }
    records.sort((a,b)=>(b.draft?.savedAt??DateTime(1970)).compareTo(
      a.draft?.savedAt??DateTime(1970)));
    return records;
  }
  Future<void> clear() async {
    final file=File(await _filePath());
    if(await file.exists())await file.delete();
  }

  /// Revogação/saída intencional remove todos os rascunhos deste vínculo.
  Future<void> clearAllForMember() async {
    final directory=await _directory();
    if(!await directory.exists()){
      await _secure.delete(key:'cipa_draft_key_${await _personHash()}');
      return;
    }
    final prefix=await _prefix();
    await for(final entity in directory.list()){
      if(entity is File&&entity.uri.pathSegments.last.startsWith(prefix+'_'))
        await entity.delete();
    }
    await _secure.delete(key:'cipa_draft_key_${await _personHash()}');
  }
}
