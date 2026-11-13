import 'dart:convert';
import 'dart:io';
import 'dart:math';
import 'dart:typed_data';
import 'package:cryptography/cryptography.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:path_provider/path_provider.dart';

import 'cipa_member_draft_store.dart';
import 'cipa_member_mural_model.dart';

/// Mural coletivo NÃO tem cache offline. Só o relato próprio não enviado
/// pode ser salvo com AES-GCM e chave no cofre do dispositivo.
class CipaMuralDraft {
  const CipaMuralDraft({required this.id,required this.place,
    required this.detail,required this.savedAt,this.photo});
  final String id,place,detail;
  final DateTime savedAt;
  final Uint8List? photo;
  Map<String,dynamic> toJson()=>{
    'version':1,'id':id,'place':place,'detail':detail,
    'savedAt':savedAt.toUtc().toIso8601String(),
    'photo':photo==null?'':base64Encode(photo!),
  };
  static CipaMuralDraft fromJson(Map<String,dynamic> json,{DateTime? now}){
    if(json['version']!=1)throw StateError('Versão incompatível.');
    String v(String key)=>(json[key]??'').toString();
    final created=DateTime.tryParse(v('savedAt'));
    final date=(now??DateTime.now()).toUtc();
    if(!RegExp(r'^[A-Za-z0-9_-]{16,120}$').hasMatch(v('id'))||
       v('place').trim().length<2||v('place').length>120||
       v('detail').trim().length<12||v('detail').length>900||
       created==null||created.isAfter(date.add(const Duration(minutes:5)))||
       date.difference(created).inHours>168)
      throw StateError('Rascunho expirado ou inválido. Confira os dados.');
    final encoded=v('photo');
    if(encoded.length>340000)throw StateError('Foto muito grande.');
    final jpeg=encoded.isEmpty?null:Uint8List.fromList(base64Decode(encoded));
    if(jpeg!=null&&!CipaMuralCodec.validPhoto(jpeg))
      throw StateError('Imagem do rascunho inválida.');
    return CipaMuralDraft(id:v('id'),place:v('place'),
      detail:v('detail'),savedAt:created.toUtc(),photo:jpeg);
  }
}
class CipaMuralDraftStore {
  CipaMuralDraftStore({required this.accountId,required this.companyId,
    required this.mandateId,required this.memberId,
    FlutterSecureStorage? secure,Future<Directory> Function()? directory,
    Future<List<int>> Function(bool create)? keyProvider,
    DateTime Function()? clock,
  }):_secure=secure??const FlutterSecureStorage(),
    _directory=directory??getApplicationSupportDirectory,
    _keyProvider=keyProvider,_clock=clock??DateTime.now;
  final String accountId,companyId,mandateId,memberId;
  final FlutterSecureStorage _secure;
  final Future<Directory> Function() _directory;
  final Future<List<int>> Function(bool create)? _keyProvider;
  final DateTime Function() _clock;
  static const int maxDrafts=10;

  Future<String> _hash(String value) async{
    final dig=await Sha256().hash(utf8.encode(value));
    return base64UrlEncode(dig.bytes).replaceAll('=','');
  }
  Future<String> _scope()=>_hash([
    accountId,companyId,mandateId,memberId].join('|'));
  Future<String> _prefix()async=>'cipa_mural_'+await _scope()+'_';
  Future<String> _file(String id)async{
    if(!RegExp(r'^[A-Za-z0-9_-]{16,120}$').hasMatch(id))
      throw StateError('Identificador inválido.');
    return (await _directory()).path+'/'+
      (await _prefix())+(await _hash(id))+'.enc';
  }
  Future<List<int>> _key(bool create)async{
    if(_keyProvider!=null)return _keyProvider(create);
    final name='cipa_mural_key_'+await _scope();
    var encoded=await _secure.read(key:name);
    if(encoded==null){
      if(!create)throw StateError('Chave local não encontrada.');
      final rng=Random.secure();
      encoded=base64Encode(List.generate(32,(_)=>rng.nextInt(256)));
      await _secure.write(key:name,value:encoded);
    }
    final key=base64Decode(encoded);
    if(key.length!=32)throw StateError('Chave local inválida.');
    return key;
  }
  Future<List<File>> _files()async{
    final dir=await _directory();
    if(!await dir.exists())return [];
    final prefix=await _prefix();
    final files=<File>[];
    await for(final item in dir.list()){
      if(item is File&&item.uri.pathSegments.last.startsWith(prefix)&&
         item.path.endsWith('.enc'))files.add(item);
    }
    if(files.length>maxDrafts)throw StateError(
      'Limite de rascunhos locais excedido.');
    return files;
  }
  Future<void> save(CipaMuralDraft draft)async{
    CipaMuralDraft.fromJson(draft.toJson(),now:_clock());
    final path=await _file(draft.id);
    if(!await File(path).exists()&&(await _files()).length>=maxDrafts)
      throw StateError('Máximo de 10 rascunhos. Envie ou remova um.');
    final dir=await _directory();
    if(!await dir.exists())await dir.create(recursive:true);
    final encoded=await CipaDraftCipher.seal(draft.toJson(),
      await _key(true));
    final temporary=File(path+'.next');
    await temporary.writeAsString(encoded,flush:true);
    await temporary.rename(path);
  }
  Future<List<CipaMuralDraft>> list()async{
    final files=await _files();
    if(files.isEmpty)return const [];
    final key=await _key(false);
    final results=<CipaMuralDraft>[];
    for(final file in files){
      final data=await CipaDraftCipher.open(
        await file.readAsString(),key);
      final draft=CipaMuralDraft.fromJson(data,now:_clock());
      if(await _file(draft.id)!=file.path)
        throw StateError('Rascunho pertence a outro registro.');
      results.add(draft);
    }
    results.sort((a,b)=>a.savedAt.compareTo(b.savedAt));
    return results;
  }
  Future<int> count()=>_files().then((items)=>items.length);
  Future<void> delete(String id)async{
    final file=File(await _file(id));
    if(await file.exists())await file.delete();
  }
  Future<void> clearAll()async{
    final dir=await _directory();
    if(await dir.exists()){
      final prefix=await _prefix();
      await for(final entry in dir.list()){
        if(entry is File&&entry.uri.pathSegments.last.startsWith(prefix))
          await entry.delete();
      }
    }
    if(_keyProvider==null)
      await _secure.delete(key:'cipa_mural_key_'+await _scope());
  }
}
