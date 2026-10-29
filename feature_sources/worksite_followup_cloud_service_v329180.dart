import 'dart:convert';

import '../database.dart';
import 'apps_script_http.dart';
import 'auth_service.dart';

/// Transporte exclusivo do acompanhamento da obra; NÃO utiliza device_sync.
/// Nunca substitui o acompanhamento local ao receber dados remotos.
class WorksiteFollowupCloudService {
  WorksiteFollowupCloudService._();

  static String _versionKey(String companyId) {
    final user=Uri.encodeComponent(AppDatabase.activeUserId.toString());
    return 'worksite_followup_cloud_revision_v1_'+user+'_'+
      Uri.encodeComponent(companyId);
  }

  static Future<int> localVersion(String companyId) async {
    final raw=await AppDatabase.instance.getSetting(_versionKey(companyId));
    return int.tryParse(raw)??0;
  }

  static Future<void> adoptRemoteVersion(
      String companyId,int version) async {
    if(version<0) throw StateError('Revisão remota inválida.');
    await AppDatabase.instance.setSetting(_versionKey(companyId),'$version');
  }

  static Future<WorksiteCloudResult> read(String companyId) =>
      _exchange(companyId,'read');

  static Future<WorksiteCloudResult> publish(
      String companyId, Map<String,dynamic> local) =>
      _exchange(companyId,'save',local:local);

  static Future<WorksiteCloudResult> _exchange(
      String companyId,String mode,{Map<String,dynamic>? local}) async {
    if(!AuthService.isSignedIn||
       AuthService.currentUser?.role.toLowerCase()=='cliente'||
       !AuthService.canAccessCompany(companyId)) {
      throw StateError('Acesso restrito à equipe autorizada desta obra.');
    }
    final currentUser=AuthService.currentUser!.id;
    final currentSession=AuthService.sessionToken;
    final currentActiveUser=AppDatabase.activeUserId.toString();
    final endpoint=(await AppDatabase.instance
      .getSetting('management_panel_endpoint')).trim();
    if(!endpoint.startsWith('https://'))
      throw StateError('A Central não está configurada para conexão segura.');
    final baseline=await localVersion(companyId);
    final response=await AppsScriptHttp.postJson(Uri.parse(endpoint),{
      'action':'worksite_followup_sync_v1',
      'authToken':currentSession,
      'companyId':companyId,
      'mode':mode,
      if(mode=='save') 'baseVersion':baseline,
      if(local!=null) 'record':local,
    },timeout:const Duration(seconds:25));
    if(response.statusCode!=200) throw StateError('Central indisponível.');
    final raw=jsonDecode(response.body);
    if(raw is! Map) throw StateError('Resposta da Central inválida.');
    final body=Map<String,dynamic>.from(raw);
    final conflict=body['code']=='WORKSITE_CONFLICT';
    if(body['ok']!=true&&!conflict)
      throw StateError((body['message']??'Canal de obras não implantado.').toString());
    if(currentUser!=AuthService.currentUser?.id||
       currentSession!=AuthService.sessionToken||
       currentActiveUser!=AppDatabase.activeUserId.toString())
      throw StateError('A conta mudou durante a consulta. Nenhum dado local foi substituído.');
    final ver=body['version'];
    final revision=ver is int?ver:int.tryParse(ver.toString())??-1;
    if(revision<0) throw StateError('Revisão da Central inválida.');
    Map<String,dynamic>? result;
    if(body['record'] is Map) result=Map<String,dynamic>.from(body['record'] as Map);
    // Only a confirmed write advances our local base revision.
    if(mode=='save'&&!conflict) await adoptRemoteVersion(companyId,revision);
    return WorksiteCloudResult(
      conflict:conflict,revision:revision,record:result,
      updatedAt:(body['updatedAt']??'').toString(),
      updatedBy:(body['updatedBy']??'').toString());
  }
}

class WorksiteCloudResult {
  const WorksiteCloudResult({
    required this.conflict,
    required this.revision,
    this.record,
    this.updatedAt='',
    this.updatedBy='',
  });
  final bool conflict;
  final int revision;
  final Map<String,dynamic>? record;
  final String updatedAt,updatedBy;
}
