import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:auditar_cipa_membro/services/cipa_member_api.dart';

const server='https://script.google.com/macros/s/example/exec';
const memberProfile={
  'userId':'user-1','companyId':'empresa-A','mandateId':'mandato-A',
  'memberId':'membro-1','workerId':'worker-1','fullName':'Ana Santos',
  'cipaRole':'Titular','representation':'Empregados','jobTitle':'Operadora',
};
Map<String,Object?> row(String id,String title,{
  String company='empresa-A',String mandate='mandato-A',
  String member='membro-1',bool shared=false,
})=>{
  'id':id,'title':title,'companyId':company,'mandateId':mandate,
  'assignedMemberId':member,'visibleToAllMembers':shared,
  'status':'Pendente',
};

void main(){
  test('Recusa itens de empresa, mandato e pessoas diferentes',() async {
    final calls=<String>[];
    final client=MockClient((http.Request req) async {
      final input=jsonDecode(req.body) as Map<String,dynamic>;
      calls.add(input['action'].toString());
      if(input['action']=='cipa_member_verify') {
        return http.Response(jsonEncode({
          'ok':true,'sessionToken':'x'*90,
        }),200,headers:const {'content-type':'application/json; charset=utf-8'});
      }
      if(input['action']=='cipa_member_dashboard') {
        return http.Response(jsonEncode({
          'ok':true,'profile':memberProfile,
          'companyName':'Empresa A','mandateTitle':'2026/2027',
          'meetings':[row('meeting-A','Convocação própria'),
            row('meeting-B','Reunião de outro membro',member:'membro-2')],
          'actions':[
            row('a1','Tarefa própria'),
            row('a2','Tarefa de outra empresa',company:'empresa-B'),
            row('a3','Tarefa de outro mandato',mandate:'mandato-B'),
            row('a4','Tarefa de outro membro',member:'membro-2'),
            {'id':'a5','title':'Ação sem vínculo comprovado'}
          ],
          'notices':[
            row('n1','Aviso público',member:'',shared:true),
            row('n2','Aviso não publicado',member:'',shared:false),
          ],
          'documents':[row('d1','Documento permitido',member:'',shared:true)],
          'trainings':[row('t1','Treinamento próprio')],
          'observations':[
            {...row('o1','Observação própria'),
              'status':'Orientação enviada',
              'feedback':'Observe a passagem apenas de local seguro.'},
            {...row('o2','Observação de outra empresa',company:'empresa-B'),
              'feedback':'Dado privado de outra empresa.'},
            {...row('o3','Observação de outro integrante',member:'membro-2'),
              'feedback':'Dado privado de outro membro.'},
          ],
          'reminders':[row('r1','Lembrete pessoal')],
        }),200,headers:const {'content-type':'application/json; charset=utf-8'});
      }
      return http.Response('{"ok":false,"code":"ACCESS_DENIED"}',200);
    });
    final api=CipaMemberApi(endpoint:server,client:client);
    await api.verifyCode('ana@example.test','12345678');
    final view=await api.dashboard();
    expect(view.profile.displayName,'Ana Santos — Titular da CIPA');
    expect(view.companyLabel,'Empresa A');
    expect(view.mandateLabel,'2026/2027');
    expect(view.myActions.map((x)=>x.id),['a1']);
    expect(view.meetings.map((x)=>x.id),['meeting-A']);
    expect(view.notices.map((x)=>x.id),['n1']);
    expect(view.documents.map((x)=>x.id),['d1']);
    expect(view.trainings.length,1);
    expect(view.observations.length,1);
    expect(view.observations.single.status,'Orientação enviada');
    expect(view.observations.single.feedback,
      'Observe a passagem apenas de local seguro.');
    expect(view.observations.single.feedback.contains('Dado privado'),false);
    expect(view.reminders.length,1);
    expect(calls,['cipa_member_verify','cipa_member_dashboard']);
    api.dispose();
  });

  test('Sessão revogada apaga acesso pessoal',() async {
    var revoked=0;
    final client=MockClient((http.Request req) async {
      final request=jsonDecode(req.body) as Map<String,dynamic>;
      if(request['action']=='cipa_member_verify')return http.Response(
        jsonEncode({'ok':true,'sessionToken':'y'*90}),200,headers:const {'content-type':'application/json; charset=utf-8'});
      return http.Response(jsonEncode({
        'ok':false,'code':'SESSION_INVALID'}),200,headers:const {'content-type':'application/json; charset=utf-8'});
    });
    final api=CipaMemberApi(endpoint:server,client:client,
      onSessionRevoked:()=>revoked++);
    await api.verifyCode('ana@example.test','12345678');
    expect(api.hasSession,true);
    await expectLater(api.dashboard(),throwsStateError);
    expect(api.hasSession,false);
    expect(revoked,1);
    api.dispose();
  });
}
