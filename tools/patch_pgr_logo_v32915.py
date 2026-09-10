#!/usr/bin/env python3
from pathlib import Path
import re
R=Path('app/Auditar_SST_v1_5_dashboard')
def rw(rel,fn):
 p=R/rel;s=p.read_text();s=fn(s);p.write_text(s)
def must(s,a,b):
 if a not in s: raise SystemExit('missing: '+a[:80])
 return s.replace(a,b,1)

def db(s):
 s=must(s,'version: 21,','version: 22,')
 s=s.replace("'company_id TEXT NOT NULL UNIQUE, '","'company_id TEXT NOT NULL, '",2)
 m="""    if (oldVersion < 21) {
      await _trySql(
        db,
        'ALTER TABLE companies ADD COLUMN weekly_report_enabled INTEGER NOT NULL DEFAULT 0',
      );
      await _trySql(
        db,
        'ALTER TABLE companies ADD COLUMN weekly_report_weekday INTEGER NOT NULL DEFAULT 5',
      );
    }
"""
 x=m+"""    if (oldVersion < 22) {
      await db.execute('DROP TABLE IF EXISTS pgr_documents_v22');
      await db.execute(
        'CREATE TABLE pgr_documents_v22('
        'id TEXT PRIMARY KEY, company_id TEXT NOT NULL, file_name TEXT NOT NULL, '
        'local_path TEXT, drive_file_id TEXT, file_size_bytes INTEGER NOT NULL DEFAULT 0, '
        'summary_json TEXT, analysis_json TEXT, updated_at TEXT NOT NULL)');
      await db.execute(
        'INSERT OR REPLACE INTO pgr_documents_v22 '
        '(id,company_id,file_name,local_path,drive_file_id,file_size_bytes,summary_json,analysis_json,updated_at) '
        'SELECT id,company_id,file_name,local_path,drive_file_id,file_size_bytes,summary_json,analysis_json,updated_at FROM pgr_documents');
      await db.execute('DROP TABLE pgr_documents');
      await db.execute('ALTER TABLE pgr_documents_v22 RENAME TO pgr_documents');
    }
"""
 s=must(s,m,x)
 a="""  Future<Map<String, Object?>?> getPgrDocument(String companyId) async {
    final db = await database;
    final rows = await db.query(
      'pgr_documents',
      where: 'company_id = ?',
      whereArgs: [companyId],
      limit: 1,
    );
    return rows.isEmpty ? null : Map<String, Object?>.from(rows.first);
  }
"""
 b="""  Future<List<Map<String, Object?>>> getPgrDocuments(String companyId) async {
    final db = await database;
    final rows = await db.query('pgr_documents', where: 'company_id = ?', whereArgs: [companyId], orderBy: 'updated_at DESC, file_name COLLATE NOCASE');
    return rows.map((row) => Map<String, Object?>.from(row)).toList();
  }

  Future<Map<String, Object?>?> getPgrDocument(String companyId) async {
    final rows = await getPgrDocuments(companyId);
    return rows.isEmpty ? null : rows.first;
  }
"""
 s=must(s,a,b)
 a="""  Future<void> updatePgrAnalysis({
    required String companyId,
    required String summaryJson,
    required String analysisJson,
  }) async {
    final db = await database;
    await db.update(
      'pgr_documents',
      {
        'summary_json': summaryJson,
        'analysis_json': analysisJson,
        'updated_at': DateTime.now().toUtc().toIso8601String(),
      },
      where: 'company_id = ?',
      whereArgs: [companyId],
    );
  }
"""
 b="""  Future<void> updatePgrAnalysis({required String companyId, String? documentId, required String summaryJson, required String analysisJson}) async {
    final db = await database;
    final byId = documentId != null && documentId.trim().isNotEmpty;
    await db.update('pgr_documents', {'summary_json': summaryJson, 'analysis_json': analysisJson, 'updated_at': DateTime.now().toUtc().toIso8601String()}, where: byId ? 'id = ?' : 'company_id = ?', whereArgs: [byId ? documentId : companyId]);
  }

  Future<void> deletePgrDocument(String documentId) async {
    final db = await database;
    await db.delete('pgr_documents', where: 'id = ?', whereArgs: [documentId]);
  }
"""
 return must(s,a,b)
rw('lib/database.dart',db)

def pgrsvc(s):
 a="""    final support = await getApplicationSupportDirectory();
    final folder = Directory(p.join(support.path, 'pgr', company.id));
    await folder.create(recursive: true);
    final localFile = File(p.join(folder.path, 'PGR.pdf'));
    await localFile.writeAsBytes(bytes, flush: true);

    final existing = await AppDatabase.instance.getPgrDocument(company.id);
    final id = '${existing?['id'] ?? const Uuid().v4()}';
    var driveFileId = '${existing?['drive_file_id'] ?? ''}'.trim();
    try {
      driveFileId = await _upload(company, bytes);
    } catch (_) {
      // O PGR continua salvo no aparelho. A IA tentará enviar novamente.
    }
"""
 b="""    final id = const Uuid().v4();
    final support = await getApplicationSupportDirectory();
    final folder = Directory(p.join(support.path, 'pgr', company.id));
    await folder.create(recursive: true);
    final localFile = File(p.join(folder.path, '$id.pdf'));
    await localFile.writeAsBytes(bytes, flush: true);
    var driveFileId = '';
    try { driveFileId = await _upload(company, bytes, fileName: selected.name); } catch (_) {}
"""
 s=must(s,a,b)
 s=must(s,'driveId = await _upload(company, bytes);',"driveId = await _upload(company, bytes, fileName: '${document['file_name'] ?? 'PGR.pdf'}');")
 s=must(s,"""  static Future<String> _upload(Company company, Uint8List bytes) async {
    final response = await _post({
""","""  static Future<String> _upload(Company company, Uint8List bytes, {String? fileName}) async {
    final cleanName = (fileName ?? '').trim();
    final response = await _post({
""")
 s=must(s,"'fileName': 'PGR - ${company.name}.pdf',","'fileName': cleanName.isEmpty ? 'PGR - ${company.name}.pdf' : cleanName,")
 mark='  static Future<Map<String, dynamic>> _ai(\n'
 add="""  static Future<void> remove(Map<String, Object?> document) async {
    final id = '${document['id'] ?? ''}'.trim();
    if (id.isEmpty) return;
    final path = '${document['local_path'] ?? ''}'.trim();
    await AppDatabase.instance.deletePgrDocument(id);
    if (path.isNotEmpty) { try { final f=File(path); if (await f.exists()) await f.delete(); } catch (_) {} }
  }

"""+mark
 return must(s,mark,add)
rw('lib/services/pgr_service.dart',pgrsvc)

def pgrscreen(s):
 s=must(s,'  Map<String, Object?>? document;\n  Map<String, dynamic>? analysis;','  List<Map<String, Object?>> documents = [];\n  Map<String, Object?>? document;\n  String? selectedDocumentId;\n  Map<String, dynamic>? analysis;')
 start=s.index('  Future<void> _load() async {'); end=s.index('\n\n  void _message',start)
 new="""  Future<void> _load() async {
    final docs = await AppDatabase.instance.getPgrDocuments(widget.company.id);
    final roles = await AppDatabase.instance.getCompanyRoles(widget.company.id, onlyActive: false);
    final reqs = await AppDatabase.instance.getTrainingRequirements(companyId: widget.company.id, onlyActive: false);
    Map<String, Object?>? selected;
    if (selectedDocumentId != null) {
      for (final row in docs) { if ('${row['id']}' == selectedDocumentId) { selected = row; break; } }
    }
    selected ??= docs.isEmpty ? null : docs.first;
    Map<String, dynamic>? parsed;
    final raw = '${selected?['analysis_json'] ?? ''}'.trim();
    if (raw.isNotEmpty) { try { final v=jsonDecode(raw); if (v is Map) parsed=Map<String,dynamic>.from(v); } catch (_) {} }
    if (!mounted) return;
    setState(() { documents=docs; document=selected; selectedDocumentId=selected==null?null:'${selected['id']}'; companyRoles=roles; requirements=reqs; analysis=parsed; lastAnswer=null; loading=false; });
  }"""
 s=s[:start]+new+s[end:]
 s=must(s,"""      final result = await PgrService.pickAndSave(widget.company);
      if (result == null) return;
      _message('PGR cadastrado. Agora você pode analisar com a IA.');
      await _load();
""","""      final result = await PgrService.pickAndSave(widget.company);
      if (result == null) return;
      selectedDocumentId = '${result['id']}';
      _message('PGR adicionado. Você pode adicionar outros ou analisar este com a IA.');
      await _load();
""")
 s=must(s,'        companyId: widget.company.id,\n        summaryJson:',"        companyId: widget.company.id,\n        documentId: '${doc['id']}',\n        summaryJson:")
 mark='  Future<void> _analyze() async {\n'
 add="""  Future<void> _selectDocument(Map<String, Object?> doc) async { if (!busy) { selectedDocumentId='${doc['id']}'; await _load(); } }

  Future<void> _removeDocument(Map<String, Object?> doc) async {
    if (busy) return;
    final ok=await showDialog<bool>(context: context,builder:(c)=>AlertDialog(title:const Text('Remover PGR?'),content:Text('Deseja remover “${doc['file_name'] ?? 'PGR'}” desta empresa?'),actions:[TextButton(onPressed:()=>Navigator.pop(c,false),child:const Text('Cancelar')),FilledButton(style:FilledButton.styleFrom(backgroundColor:Colors.red.shade700),onPressed:()=>Navigator.pop(c,true),child:const Text('Remover'))]));
    if (ok!=true) return;
    setState(()=>busy=true);
    try { await PgrService.remove(doc); if(selectedDocumentId=='${doc['id']}') selectedDocumentId=null; _message('PGR removido.'); await _load(); } catch(e) { _message('$e',error:true); } finally { if(mounted) setState(()=>busy=false); }
  }

"""+mark
 s=must(s,mark,add)
 s=must(s,"""  String get _fileSizeText {
    final bytes = (document?['file_size_bytes'] as num?)?.toDouble() ?? 0;
    return '${(bytes / 1048576.0).toStringAsFixed(1)} MB';
  }
""","""  String _fileSizeTextFor(Map<String,Object?> doc) {
    final bytes=(doc['file_size_bytes'] as num?)?.toDouble() ?? 0;
    return '${(bytes/1048576.0).toStringAsFixed(1)} MB';
  }
  String get _fileSizeText => document==null?'0.0 MB':_fileSizeTextFor(document!);
""")
 a=s.index('        Card(\n          child: Padding(\n            padding: const EdgeInsets.all(14),',s.index("Text('PGR Inteligente'"))
 b=s.index('\n        if (analysis != null)',a)
 card="""        Card(child:Padding(padding:const EdgeInsets.all(14),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
          Row(children:[const Icon(Icons.picture_as_pdf_rounded,color:Colors.red),const SizedBox(width:10),Expanded(child:Text(documents.isEmpty?'Nenhum PGR cadastrado':'PGRs cadastrados • ${documents.length}',style:const TextStyle(fontWeight:FontWeight.w900)))]),
          if(documents.isNotEmpty)...[const SizedBox(height:10),const Text('Toque em um documento para selecioná-lo. A IA usa o PGR selecionado.',style:TextStyle(fontSize:12,color:Colors.black54)),const SizedBox(height:8),
            ...documents.map((doc){ final sel='${doc['id']}'==selectedDocumentId; final analyzed='${doc['analysis_json'] ?? ''}'.trim().isNotEmpty; return Container(margin:const EdgeInsets.only(bottom:8),decoration:BoxDecoration(border:Border.all(color:sel?AuditarBrand.green:Colors.black12,width:sel?2:1),borderRadius:BorderRadius.circular(12)),child:ListTile(dense:true,onTap:busy?null:()=>_selectDocument(doc),leading:Icon(sel?Icons.check_circle_rounded:Icons.picture_as_pdf_outlined,color:sel?AuditarBrand.green:Colors.red),title:Text('${doc['file_name'] ?? 'PGR.pdf'}',maxLines:2,overflow:TextOverflow.ellipsis,style:const TextStyle(fontWeight:FontWeight.w800)),subtitle:Text('${_fileSizeTextFor(doc)}${analyzed?' • analisado pela IA':''}'),trailing:IconButton(tooltip:'Remover este PGR',onPressed:busy?null:()=>_removeDocument(doc),icon:const Icon(Icons.delete_outline_rounded,color:Colors.red)))); })],
          const SizedBox(height:4),Wrap(spacing:8,runSpacing:8,children:[FilledButton.icon(onPressed:busy?null:_pick,icon:const Icon(Icons.add_rounded),label:Text(documents.isEmpty?'Adicionar PGR':'Adicionar outro PGR')),if(document!=null)OutlinedButton.icon(onPressed:busy?null:_analyze,icon:const Icon(Icons.auto_awesome_rounded),label:const Text('Analisar selecionado com IA'))]),
          if(busy)...[const SizedBox(height:12),const LinearProgressIndicator()]
        ]))),"""
 return s[:a]+card+s[b:]
rw('lib/screens/pgr_screen.dart',pgrscreen)

def media(s):
 mark='  static Future<int> pendingCount() async {\n'
 add="""  static Future<void> registerCompanyLogo({required String companyId, required String localPath}) async {
    if(companyId.trim().isEmpty || localPath.trim().isEmpty) return;
    final db=await AppDatabase.instance.database; final id=_assetId('company_logo',companyId);
    await db.insert('media_assets',{'id':id,'company_id':companyId,'entity_type':'company_logo','entity_id':companyId,'local_path':localPath,'drive_file_id':'','file_name':p.basename(localPath),'mime_type':_mimeTypeFor(localPath),'updated_at':DateTime.now().toUtc().toIso8601String()},conflictAlgorithm:ConflictAlgorithm.replace);
  }

  static Future<void> clearCompanyLogo(String companyId) async {
    if(companyId.trim().isEmpty) return;
    final db=await AppDatabase.instance.database; final id=_assetId('company_logo',companyId);
    await db.insert('media_assets',{'id':id,'company_id':companyId,'entity_type':'company_logo','entity_id':companyId,'local_path':'','drive_file_id':'','file_name':'','mime_type':'','updated_at':DateTime.now().toUtc().toIso8601String()},conflictAlgorithm:ConflictAlgorithm.replace);
  }

"""+mark
 s=must(s,mark,add)
 mark='    final evidence = await db.rawQuery(\n'
 add="""    final logos=await db.query('companies',columns:['id','logo_path'],where:'logo_path IS NOT NULL AND logo_path <> ""');
    for(final row in logos){ final id='${row['id'] ?? ''}'.trim(); final lp='${row['logo_path'] ?? ''}'.trim(); if(id.isNotEmpty && lp.isNotEmpty) await _ensureAsset(db,companyId:id,entityType:'company_logo',entityId:id,localPath:lp); }

"""+mark
 s=must(s,mark,add)
 a="""    } else if (entityType == 'responsible_signature') {
      await db.update(
        'inspections',
        {'responsible_signature_path': path},
        where: 'id = ?',
        whereArgs: [entityId],
      );
    }
"""
 b="""    } else if (entityType == 'responsible_signature') {
      await db.update(
        'inspections',
        {'responsible_signature_path': path},
        where: 'id = ?',
        whereArgs: [entityId],
      );
    } else if (entityType == 'company_logo') {
      await db.update('companies', {'logo_path': path}, where: 'id = ?', whereArgs: [entityId]);
    }
"""
 return must(s,a,b)
rw('lib/services/media_sync_service.dart',media)

def companies(s):
 s=must(s,"import '../services/storage_service.dart';","import '../services/device_sync_service.dart';\nimport '../services/media_sync_service.dart';\nimport '../services/storage_service.dart';")
 a=s.index('  Future<void> _chooseLogo(Company company) async {'); b=s.index('\n\n  Future<void> _deleteCompany',a)
 new="""  Future<void> _chooseLogo(Company company) async {
    final image=await picker.pickImage(source:ImageSource.gallery,imageQuality:90,maxWidth:1600); if(image==null)return;
    final old=company.logoPath; final stored=await StorageService.persistImage(image.path,folder:'logos_empresas');
    await AppDatabase.instance.updateCompanyLogo(company.id,stored); await MediaSyncService.registerCompanyLogo(companyId:company.id,localPath:stored);
    var synced=false; try { await DeviceSyncService.synchronize(force:true); synced=true; } catch(_) {}
    if(old!=null&&old.isNotEmpty&&old!=stored){try{final f=File(old);if(await f.exists())await f.delete();}catch(_){}}
    await _load(); if(!mounted)return; ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(synced?'Logo salva e sincronizada. Ela será recuperada após reinstalar o app.':'Logo salva. A sincronização com a Central ficou pendente.')));
  }

  Future<void> _removeLogo(Company company) async {
    final old=company.logoPath; await AppDatabase.instance.updateCompanyLogo(company.id,null); await MediaSyncService.clearCompanyLogo(company.id); try{await DeviceSyncService.synchronize(force:true);}catch(_){}
    if(old!=null&&old.isNotEmpty){try{final f=File(old);if(await f.exists())await f.delete();}catch(_){}} await _load();
  }"""
 return s[:a]+new+s[b:]
rw('lib/screens/companies_screen.dart',companies)

rw('pubspec.yaml',lambda s:must(s,'version: 3.29.14+157','version: 3.29.15+158'))
print('v3.29.15: múltiplos PGRs, remoção e logo persistente aplicados')
