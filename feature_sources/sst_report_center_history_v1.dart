import 'dart:convert';
import 'dart:math';

import 'sst_report_center_models.dart';

/// Arquivos históricos locais imutáveis, separados por empresa e usuário.
/// Não envia registros à Central nem interfere nas NCs/vistorias.
class SstFieldVisitSummary {
  const SstFieldVisitSummary({
    required this.id,required this.archivedAt,required this.visitDate,
    required this.location,required this.technician,required this.reviewed,
    required this.total,required this.partial,
  });
  final String id,archivedAt,visitDate,location,technician;
  final int reviewed,total;
  final bool partial;
  Map<String,dynamic> toJson()=> {
    'id':id,'archivedAt':archivedAt,'visitDate':visitDate,
    'location':location,'technician':technician,'reviewed':reviewed,
    'total':total,'partial':partial,
  };
  factory SstFieldVisitSummary.fromJson(Map<String,dynamic> data) {
    final id=(data['id']??'').toString();
    if(!RegExp(r'^[a-z0-9-]{8,80}$').hasMatch(id)) {
      throw const FormatException('Identificador histórico inválido.');
    }
    final reviewed=data['reviewed'],total=data['total'];
    if(reviewed is! int || total is! int ||
        reviewed<0||total<1||reviewed>total) {
      throw const FormatException('Contagem do histórico inválida.');
    }
    return SstFieldVisitSummary(
      id:id,
      archivedAt:(data['archivedAt']??'').toString(),
      visitDate:(data['visitDate']??'').toString(),
      location:(data['location']??'').toString(),
      technician:(data['technician']??'').toString(),
      reviewed:reviewed,total:total,
      partial:data['partial']==true,
    );
  }
}
class SstFieldVisitArchive {
  const SstFieldVisitArchive({required this.summary,required this.draft});
  final SstFieldVisitSummary summary;
  final SstFieldDraft draft;
}

/// Adaptador injetável para testar sem banco real. Salva no settings local.
class SstFieldReportHistory {
  const SstFieldReportHistory({required this.read,required this.write});
  final Future<String> Function(String key) read;
  final Future<void> Function(String key,String value) write;

  static String _prefix(String companyId,String userId,
    SstFieldReportKind kind) =>
      'field_report_history_v1_${Uri.encodeComponent(userId)}_'
      '${Uri.encodeComponent(companyId)}_${kind.name}';

  static String indexKey(String companyId,String userId,
      SstFieldReportKind kind)=>'${_prefix(companyId,userId,kind)}_index';

  static String visitKey(String companyId,String userId,
      SstFieldReportKind kind,String id) {
    if(!RegExp(r'^[a-z0-9-]{8,80}$').hasMatch(id)) {
      throw const FormatException('Identificador inválido.');
    }
    return '${_prefix(companyId,userId,kind)}_item_$id';
  }

  static String newId() {
    final part=DateTime.now().microsecondsSinceEpoch.toRadixString(36);
    final random=Random.secure().nextInt(0x7fffffff).toRadixString(36);
    return '$part-$random';
  }

  Future<List<SstFieldVisitSummary>> list({
    required String companyId,required String userId,
    required SstFieldReportKind kind,
  }) async {
    final raw=await read(indexKey(companyId,userId,kind));
    if(raw.trim().isEmpty)return const [];
    final json=jsonDecode(raw);
    if(json is! Map || json['version']!=1||
       json['companyId']!=companyId ||
       json['userId']!=userId ||
       json['kind']!=kind.name ||
       json['items'] is! List) {
      throw const FormatException('Índice de visitas inválido.');
    }
    final items=<SstFieldVisitSummary>[];
    final ids=<String>{};
    for(final row in json['items'] as List) {
      if(row is! Map)throw const FormatException('Visita inválida.');
      final summary=SstFieldVisitSummary.fromJson(
        Map<String,dynamic>.from(row));
      if(!ids.add(summary.id)) {
        throw const FormatException('Visita duplicada no histórico.');
      }
      items.add(summary);
    }
    return List.unmodifiable(items);
  }

  /// Grava o snapshot antes do índice; o rascunho ativo não é alterado.
  Future<SstFieldVisitSummary> archive({
    required SstFieldDraft draft,
    required String userId,
    required String id,
  }) async {
    if(draft.kind==SstFieldReportKind.monthly||!draft.hasEnoughForPdf) {
      throw StateError('Revise os dados essenciais antes de arquivar.');
    }
    final existing=await list(
      companyId:draft.companyId,userId:userId,kind:draft.kind);
    for(final item in existing) {
      if(item.id==id) {
        final saved=await open(
          companyId:draft.companyId,userId:userId,kind:draft.kind,id:id);
        if(jsonEncode(saved.draft.toJson())!=jsonEncode(draft.toJson())) {
          throw StateError('Esta visita já foi arquivada com outro conteúdo.');
        }
        return item;
      }
    }
    if(existing.length>=500) {
      throw StateError('Limite local de visitas atingido. Exporte o histórico.');
    }
    final summary=SstFieldVisitSummary(
      id:id,
      archivedAt:DateTime.now().toUtc().toIso8601String(),
      visitDate:draft.date,
      location:draft.location,
      technician:draft.technician,
      reviewed:draft.reviewed,
      total:SstFieldTemplates.of(draft.kind).questions.length,
      partial:draft.isPartial,
    );
    final row=jsonEncode({
      'version':1,
      'companyId':draft.companyId,
      'userId':userId,
      'kind':draft.kind.name,
      'id':id,
      'summary':summary.toJson(),
      'draft':draft.toJson(),
    });
    await write(visitKey(draft.companyId,userId,draft.kind,id),row);
    await write(indexKey(draft.companyId,userId,draft.kind),jsonEncode({
      'version':1,'companyId':draft.companyId,'userId':userId,
      'kind':draft.kind.name,
      'items':[summary.toJson(),...existing.map((e)=>e.toJson())],
    }));
    return summary;
  }

  /// Abre somente visitas previamente indexadas neste escopo.
  Future<SstFieldVisitArchive> open({
    required String companyId,required String userId,
    required SstFieldReportKind kind,required String id,
  }) async {
    final index=await list(companyId:companyId,userId:userId,kind:kind);
    final found=index.where((e)=>e.id==id).toList();
    if(found.length!=1)throw StateError('Visita não encontrada neste acesso.');
    final raw=await read(visitKey(companyId,userId,kind,id));
    if(raw.trim().isEmpty)throw StateError(
      'Registro da visita indisponível no armazenamento local.');
    final json=jsonDecode(raw);
    if(json is! Map||json['version']!=1||
       json['companyId']!=companyId||json['userId']!=userId||
       json['kind']!=kind.name||json['id']!=id||
       json['draft'] is! Map||json['summary'] is! Map) {
      throw const FormatException('Arquivo não pertence ao acesso atual.');
    }
    final fromFile=SstFieldVisitSummary.fromJson(
      Map<String,dynamic>.from(json['summary'] as Map));
    if(jsonEncode(found.first.toJson())!=jsonEncode(fromFile.toJson())) {
      throw const FormatException('Índice histórico não corresponde ao arquivo.');
    }
    final draft=SstFieldDraft.fromJson(
      Map<String,dynamic>.from(json['draft'] as Map),
      expectedKind:kind,expectedCompanyId:companyId);
    return SstFieldVisitArchive(summary:fromFile,draft:draft);
  }
}
