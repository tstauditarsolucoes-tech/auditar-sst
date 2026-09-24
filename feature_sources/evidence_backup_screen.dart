import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../brand.dart';
import '../database.dart';
import '../models.dart';
import '../services/device_sync_service.dart';
import '../services/media_sync_service.dart';

enum BackupRecordState { pending, confirmed, unverified }
enum BackupPhotoState { pending, confirmed, recoverable, missing, unverified }

class BackupPhotoStateItem {
  final int number;
  final String path;
  final BackupPhotoState state;
  const BackupPhotoStateItem(this.number, this.path, this.state);
  String get label {
    switch (state) {
      case BackupPhotoState.confirmed:
        return 'Foto $number: backup confirmado';
      case BackupPhotoState.recoverable:
        return 'Foto $number: backup disponível; recuperar';
      case BackupPhotoState.pending:
        return 'Foto $number: salva aqui; envio pendente';
      case BackupPhotoState.missing:
        return 'Foto $number: arquivo não localizado';
      case BackupPhotoState.unverified:
        return 'Foto $number: backup não confirmado';
    }
  }
}

class BackupRecordItem {
  final String id;
  final String category;
  final String title;
  final DateTime date;
  final String roundId;
  final BackupRecordState state;
  final List<BackupPhotoStateItem> photos;
  const BackupRecordItem({
    required this.id,
    required this.category,
    required this.title,
    required this.date,
    required this.state,
    required this.photos,
    this.roundId = '',
  });
  bool get isProtected =>
      state == BackupRecordState.confirmed &&
      photos.every((p) => p.state == BackupPhotoState.confirmed ||
          p.state == BackupPhotoState.recoverable);
  String get recordLabel {
    switch (state) {
      case BackupRecordState.confirmed: return 'Registro confirmado na Central';
      case BackupRecordState.pending: return 'Registro salvo aqui; envio pendente';
      case BackupRecordState.unverified: return 'Registro salvo aqui; backup não confirmado';
    }
  }
}

class BackupCompanySnapshot {
  final List<BackupRecordItem> records;
  final String lastDataSync;
  final String mediaError;
  const BackupCompanySnapshot(this.records,this.lastDataSync,this.mediaError);
  int get confirmed => records.where((r)=>r.isProtected).length;
  int get pendingRecords => records.where((r)=>r.state == BackupRecordState.pending).length;
  int get photoCount => records.fold(0,(n,r)=>n+r.photos.length);
  int get backedPhotos => records.fold(0,(n,r)=>n+r.photos.where(
    (p)=>p.state == BackupPhotoState.confirmed ||
      p.state == BackupPhotoState.recoverable).length);
  int get missingPhotos => records.fold(0,(n,r)=>n+r.photos.where(
    (p)=>p.state == BackupPhotoState.missing).length);
  int get pendingPhotos => records.fold(0,(n,r)=>n+r.photos.where(
    (p)=>p.state == BackupPhotoState.pending ||
      p.state == BackupPhotoState.unverified).length);
}

/// Read-only verification from the existing local database and media catalog.
/// A global "sync completed" flag alone never proves that an individual photo
/// has been uploaded. Confirmed photo = matching media asset + Drive file ID.
class BackupStatusReader {
  static BackupRecordState recordState({
    required bool trackingAvailable,
    required bool? dirty,
    required bool hasSuccessfulSync,
  }) {
    if (!trackingAvailable || dirty == null || !hasSuccessfulSync) {
      return BackupRecordState.unverified;
    }
    return dirty ? BackupRecordState.pending : BackupRecordState.confirmed;
  }

  static BackupPhotoState photoState({
    required bool localExists,
    required bool sameCatalogPath,
    required bool hasDriveId,
  }) {
    if (sameCatalogPath && hasDriveId) {
      return localExists ? BackupPhotoState.confirmed :
        BackupPhotoState.recoverable;
    }
    if (localExists) return BackupPhotoState.pending;
    if (hasDriveId) return BackupPhotoState.unverified;
    return BackupPhotoState.missing;
  }

  static DateTime _date(Object? value) =>
      DateTime.tryParse('\${value ?? ''}') ?? DateTime.fromMillisecondsSinceEpoch(0);

  static Future<BackupCompanySnapshot> inspect(Company company) async {
    final app = AppDatabase.instance;
    final db = await app.database;
    final rows = await db.query('inspections',
      columns:['id','company_id','date','checklist_type','status'],
      where:'company_id = ?',whereArgs:[company.id],orderBy:'date DESC');
    final rounds = await db.query('sst_records',
      columns:['id','title','date','payload'],
      where:"company_id = ? AND type = 'OBSERVACAO_SEGURANCA'",
      whereArgs:[company.id],orderBy:'date DESC');
    final photos = await db.rawQuery(
      'SELECT p.id,p.path,a.inspection_id FROM evidence_photos p '
      'JOIN answers a ON a.id = p.answer_id '
      'JOIN inspections i ON i.id = a.inspection_id '
      'WHERE i.company_id = ?', [company.id]);
    final medias = await db.query('media_assets',
      columns:['entity_type','entity_id','local_path','drive_file_id'],
      where:'company_id = ? AND entity_type IN (?,?)',
      whereArgs:[company.id,'evidence_photo','round_photo']);
    final assetByKey=<String,Map<String,Object?>>{
      for(final a in medias)
        '${a['entity_type']}/${a['entity_id']}': a,
    };
    final photoByInspection=<String,List<Map<String,Object?>>>{};
    for(final p in photos){
      final id='${p['inspection_id'] ?? ''}';
      (photoByInspection[id] ??= <Map<String,Object?>>[]).add(p);
    }

    final exists=await db.rawQuery(
      "SELECT 1 FROM sqlite_master WHERE type = 'table' "
      "AND name = 'device_sync_changes' LIMIT 1");
    final tracking=exists.isNotEmpty;
    final dirtyByKey=<String,bool>{};
    if(tracking) {
      final changes=await db.query('device_sync_changes',
        columns:['table_name','record_id','dirty'],
        where:"table_name IN ('inspections','sst_records')");
      for(final row in changes) {
        dirtyByKey['${row['table_name']}/${row['record_id']}'] =
          row['dirty'] == 1;
      }
    }
    final success=(await app.getSetting('last_device_sync_success')).trim();
    final error=(await app.getSetting('media_sync_last_error')).trim();
    BackupPhotoStateItem photoStatus(String type,String id,String path,int num) {
      final asset=assetByKey['$type/$id'];
      final catalogPath='${asset?['local_path'] ?? ''}'.trim();
      final driveId='${asset?['drive_file_id'] ?? ''}'.trim();
      return BackupPhotoStateItem(num,path,photoState(
        localExists:path.isNotEmpty && File(path).existsSync(),
        sameCatalogPath:path.isNotEmpty && catalogPath == path,
        hasDriveId:driveId.isNotEmpty,
      ));
    }

    final result=<BackupRecordItem>[];
    for(final r in rows) {
      final id='${r['id'] ?? ''}'.trim();
      if(id.isEmpty) continue;
      final attached=photoByInspection[id] ?? const <Map<String,Object?>>[];
      result.add(BackupRecordItem(id:id,category:'Checklist',
        title:'Vistoria • ${DateFormat('dd/MM/yyyy').format(_date(r['date']))}',
        date:_date(r['date']),
        state:recordState(trackingAvailable:tracking,
          dirty:dirtyByKey['inspections/$id'],
          hasSuccessfulSync:success.isNotEmpty),
        photos:[for(var i=0;i<attached.length;i++)
          photoStatus('evidence_photo','${attached[i]['id'] ?? ''}',
            '${attached[i]['path'] ?? ''}'.trim(),i+1)]));
    }

    for(final r in rounds) {
      final id='${r['id'] ?? ''}'.trim();
      if(id.isEmpty) continue;
      Map<String,dynamic> data;
      try {
        final parsed=jsonDecode('${r['payload'] ?? ''}');
        if(parsed is! Map) continue;
        data=Map<String,dynamic>.from(parsed);
      } catch (_) {continue;}
      final group='${data['roundId'] ?? ''}'.trim();
      final kind='${data['roundType'] ?? ''}'.trim();
      if(group.isEmpty && kind!='RONDA_EXPRESSA' &&
        data['categories'] is! List) continue;
      final first='${data['photoPath'] ?? ''}'.trim();
      final second='${data['photoPath2'] ?? ''}'.trim();
      result.add(BackupRecordItem(id:id,category:'Ronda / vistoria de campo',
        title:'${r['title'] ?? 'Registro de campo'}',
        date:_date(r['date']), roundId:group,
        state:recordState(trackingAvailable:tracking,
          dirty:dirtyByKey['sst_records/$id'],
          hasSuccessfulSync:success.isNotEmpty),
        photos:[
          if(first.isNotEmpty) photoStatus('round_photo',id,first,1),
          if(second.isNotEmpty) photoStatus('round_photo',id+'_2',second,2),
        ]));
    }
    result.sort((a,b)=>b.date.compareTo(a.date));
    return BackupCompanySnapshot(result,success,error);
  }
}

class EvidenceBackupScreen extends StatefulWidget {
  final Company company;
  const EvidenceBackupScreen({super.key,required this.company});
  @override State<EvidenceBackupScreen> createState()=>_EvidenceBackupScreenState();
}

class _EvidenceBackupScreenState extends State<EvidenceBackupScreen> {
  BackupCompanySnapshot? snapshot;
  bool busy=false;
  String progress='';
  @override void initState(){super.initState();_refresh();}
  Future<void> _refresh() async {
    try {
      final next=await BackupStatusReader.inspect(widget.company);
      if(mounted) setState(()=>snapshot=next);
    } catch(e) {
      if(mounted) _notice('Não foi possível consultar o estado local: $e');
    }
  }
  void _notice(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content:Text(message),duration:const Duration(seconds:5)));
  }
  Future<void> _sendPending() async {
    if(busy)return;
    setState(() {busy=true;progress='Enviando registros pendentes...';});
    try {
      // Reconcile only local files; never clear an existing remote backup just
      // because this device doesn't have that photo.
      final current=snapshot;
      if(current!=null){
        for(final item in current.records) {
          if(item.category!='Ronda / vistoria de campo')continue;
          for(final pic in item.photos) {
            if(pic.path.isEmpty || !await File(pic.path).exists()) continue;
            await MediaSyncService.registerRoundPhoto(
              companyId:widget.company.id,
              recordId:item.id+(pic.number==2?'_2':''),
              localPath:pic.path);
          }
        }
      }
      await DeviceSyncService.synchronize(force:true);
      if(mounted)setState(()=>progress='Enviando fotos pendentes...');
      await MediaSyncService.uploadPending(limit:40);
      await _refresh();
      if(mounted) {
        final error=(snapshot?.mediaError ?? '').trim();
        _notice(error.isEmpty?'Conferência concluída. Veja os indicadores de cada foto.':
          'Envio concluído com pendências: $error');
      }
    } catch(e) {
      if(mounted)_notice('Envio pendente: $e. Os dados locais foram mantidos.');
    } finally {
      if(mounted)setState(() {busy=false;progress='';});
    }
  }
  Future<void> _restoreMissing() async {
    if(busy)return;
    final current=snapshot;
    if(current==null)return;
    final targets=current.records.where((r)=>r.photos.any(
      (p)=>p.state==BackupPhotoState.recoverable)).take(10).toList();
    if(targets.isEmpty) { _notice('Nenhuma foto com recuperação pendente.'); return; }
    setState(() {busy=true; progress='Recuperando fotos com backup...';});
    var recovered=0;
    try{
      final rounds=<String>{};
      for(final r in targets){
        if(r.category=='Checklist') {
          recovered+=await MediaSyncService.restoreInspectionMedia(r.id);
        } else if(r.roundId.isNotEmpty && rounds.add(r.roundId)) {
          recovered+=await MediaSyncService.restoreRoundMedia(
            companyId:widget.company.id,roundId:r.roundId);
        }
      }
      await _refresh();
      if(mounted)_notice('$recovered arquivo(s) recuperado(s). Os registros foram preservados.');
    }catch(e) {
      if(mounted)_notice('Recuperação não concluída: $e');
    }finally{if(mounted)setState(() {busy=false;progress='';});}
  }

  Widget _stat(String title,String value,Color color)=>Expanded(
    child:Container(padding:const EdgeInsets.all(12),
      decoration:BoxDecoration(color:color.withValues(alpha:.08),
        borderRadius:BorderRadius.circular(12)),
      child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
        Text(value,style:TextStyle(color:color,fontSize:20,fontWeight:FontWeight.w900)),
        Text(title,style:const TextStyle(fontSize:11.5)),
      ])));

  Color _recordColor(BackupRecordState state)=>
    state==BackupRecordState.confirmed?AuditarBrand.greenDark:
      state==BackupRecordState.pending?const Color(0xFFAD6409):Colors.blueGrey;
  Color _photoColor(BackupPhotoState state)=>switch(state){
    BackupPhotoState.confirmed=>AuditarBrand.greenDark,
    BackupPhotoState.recoverable=>const Color(0xFF1E7192),
    BackupPhotoState.pending=>const Color(0xFFAD6409),
    BackupPhotoState.unverified=>const Color(0xFFAD6409),
    BackupPhotoState.missing=>const Color(0xFFD93025),
  };
  @override Widget build(BuildContext context) {
    final s=snapshot;
    return Scaffold(
      appBar:AppBar(title:const Text('Proteção de vistorias e fotos'),
        actions:[IconButton(tooltip:'Conferir novamente',onPressed:busy?null:_refresh,
          icon:const Icon(Icons.refresh_outlined))]),
      body:s==null?const Center(child:CircularProgressIndicator()):
        Column(children:[
          Padding(padding:const EdgeInsets.fromLTRB(14,10,14,6),
            child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
              Text(widget.company.name,style:const TextStyle(
                fontSize:17,fontWeight:FontWeight.w900)),
              const SizedBox(height:8),
              Row(children:[
                _stat('Registros protegidos','${s.confirmed}/${s.records.length}',
                  AuditarBrand.greenDark),
                const SizedBox(width:8),
                _stat('Fotos com backup','${s.backedPhotos}/${s.photoCount}',
                  AuditarBrand.navy),
                const SizedBox(width:8),
                _stat('Fotos não localizadas','${s.missingPhotos}',
                  const Color(0xFFD93025)),
              ]),
              const SizedBox(height:8),
              const Text('Registro e fotografia são verificados separadamente. '
                'A foto só aparece como protegida quando há confirmação no catálogo do Drive. '
                'O PDF enviado por e-mail não é backup dos registros editáveis.',
                style:TextStyle(fontSize:11.5,color:Colors.black54)),
              if(s.mediaError.isNotEmpty) Padding(
                padding:const EdgeInsets.only(top:6),child:Text(
                  'Última pendência das fotos: ${s.mediaError}',
                  style:const TextStyle(fontSize:12,color:Color(0xFF9E4C00)))),
              if(busy) Padding(padding:const EdgeInsets.only(top:8),
                child:Row(children:[const SizedBox(width:15,height:15,
                    child:CircularProgressIndicator(strokeWidth:2)),
                  const SizedBox(width:8),Expanded(child:Text(progress))])),
              const SizedBox(height:8),
              Row(children:[
                Expanded(child:FilledButton.icon(onPressed:busy?null:_sendPending,
                  icon:const Icon(Icons.cloud_upload_outlined),
                  label:const Text('Enviar pendentes'))),
                const SizedBox(width:8),
                OutlinedButton.icon(onPressed:busy?null:_restoreMissing,
                  icon:const Icon(Icons.cloud_download_outlined),
                  label:const Text('Recuperar fotos')),
              ]),
            ])),
          Expanded(child:s.records.isEmpty
            ?const Center(child:Text('Nenhuma vistoria encontrada nesta empresa.'))
            :ListView.builder(itemCount:s.records.length,
              itemBuilder:(context,index){
                final item=s.records[index];
                return Card(margin:const EdgeInsets.fromLTRB(12,5,12,5),
                  child:Padding(padding:const EdgeInsets.all(12),
                    child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
                      Text(item.title,maxLines:2,overflow:TextOverflow.ellipsis,
                        style:const TextStyle(fontWeight:FontWeight.w800)),
                      const SizedBox(height:3),
                      Text('${item.category} • ${DateFormat('dd/MM/yyyy HH:mm').format(item.date)}',
                        style:const TextStyle(fontSize:11.5,color:Colors.black54)),
                      const SizedBox(height:6),
                      Row(children:[Icon(item.state==BackupRecordState.confirmed
                        ?Icons.cloud_done_outlined:Icons.save_outlined,size:17,
                        color:_recordColor(item.state)),
                        const SizedBox(width:6),
                        Expanded(child:Text(item.recordLabel,style:TextStyle(
                          color:_recordColor(item.state),fontSize:12))) ]),
                      for(final photo in item.photos) Padding(
                        padding:const EdgeInsets.only(top:5),
                        child:Row(children:[
                          Icon(photo.state==BackupPhotoState.confirmed
                            ?Icons.cloud_done_outlined:
                            photo.state==BackupPhotoState.missing
                              ?Icons.error_outline:Icons.cloud_upload_outlined,
                            size:17,color:_photoColor(photo.state)),
                          const SizedBox(width:6),
                          Expanded(child:Text(photo.label,style:TextStyle(
                            color:_photoColor(photo.state),fontSize:12))),
                        ])),
                      if(item.photos.isEmpty)const Padding(
                        padding:EdgeInsets.only(top:5),
                        child:Text('Sem foto anexada neste registro.',
                          style:TextStyle(fontSize:11.5,color:Colors.black54))),
                    ])));
              })),
        ]));
  }
}
