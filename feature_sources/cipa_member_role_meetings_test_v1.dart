
import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_sst/services/cipa_member_role_meetings.dart';

void main(){
  test('Funções válidas possuem orientação própria sem conceder acessos',(){
    expect(CipaRoleGuide.roles.length,6);
    for(final role in CipaRoleGuide.roles){
      expect(CipaRoleGuide.summary(role).length,greaterThan(50));
      expect(CipaRoleGuide.firstSteps(role),isNotEmpty);
      expect(CipaRoleGuide.hint(role),isNotEmpty);
    }
    expect(CipaRoleGuide.summary('Admin da Central'),contains('Confirme'));
  });
  test('Presidente só empregador e vice só empregados',(){
    expect(CipaRoleGuide.consistent('Presidente','Empregador'),true);
    expect(CipaRoleGuide.consistent('Presidente','Empregados'),false);
    expect(CipaRoleGuide.consistent('Vice-presidente','Empregados'),true);
    expect(CipaRoleGuide.consistent('Vice-presidente','Empregador'),false);
    expect(CipaRoleGuide.consistent('Membro designado','Designado'),true);
    expect(CipaRoleGuide.consistent('Titular','Designado'),false);
    expect(CipaRoleGuide.consistent('Superadministrador','Empregador'),false);
  });
  test('Secretário é escolhido para cada reunião (sem função automática)',(){
    expect(CipaRoleGuide.summary('Secretário'),contains('CADA reunião'));
    expect(CipaRoleGuide.firstSteps('Secretário').first,
      contains('designação'));
  });
  test('Rascunho começa com alerta e exige relato real, não inventa assinatura',(){
    final text=CipaMinutesPractice(
      date:DateTime(2026,11,13),
      place:'Sala de reunião',agenda:'Ações preventivas',
      discussion:'Revisaram as saídas de emergência',
      decisions:'Verificar a sinalização no próximo encontro').build();
    expect(text,startsWith('RASCUNHO EDUCATIVO'));
    expect(text,contains('13/11/2026'));
    expect(text,contains('[CONFERIR DESIGNACAO]'));
    expect(text,contains('[CONFERIR LISTA REAL]'));
    expect(text,contains('assinatura dos presentes'));
    expect(text,contains('não cria ata oficial'));
  });
  test('Rascunho não aceita pauta ou decisão vazia e tipo desconhecido',(){
    expect(()=>CipaMinutesPractice(date:DateTime(2026,11,13),
      place:'Sala',agenda:'Pauta',discussion:'Discussão',decisions:'')
      .build(),throwsArgumentError);
    expect(()=>CipaMinutesPractice(date:DateTime(2026,11,13),
      place:'Sala',agenda:'Pauta',discussion:'Discussão',decisions:'Decisão',
      meetingType:'Assinada').build(),throwsArgumentError);
  });
  test('Modelo remove novas linhas arbitrárias e limita o comprimento',(){
    final text=CipaMinutesPractice(date:DateTime(2026,11,13),
      place:'Sala\nDiretoria',agenda:'Pauta',
      discussion:'Riscos discutidos',
      decisions:'Encaminhar ações').build();
    expect(text,contains('Sala Diretoria'));
    expect(()=>CipaMinutesPractice(date:DateTime(2026,11,13),
      place:'Sala',agenda:'a'*601,discussion:'Assunto',decisions:'Ações')
      .build(),throwsArgumentError);
  });
}
