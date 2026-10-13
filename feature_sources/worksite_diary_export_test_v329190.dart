import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_sst/screens/worksite_followup_screen.dart';

void main(){
  WorksiteLog log(int i)=>WorksiteLog(
    '2026-10-13T12:00:00.'+i.toString().padLeft(3,'0')+'Z',
    'Vistoria','Registro '+i.toString());

  test('diário completo reúne registros antigos e atuais sem truncar',(){
    final current=[for(var i=21;i<101;i++)log(i)];
    final old=[for(var i=0;i<21;i++)log(i)];
    final result=WorksiteDiaryArchive.exportText(
      'Construtora Quality - Obra 35','Acabamento',current,old);
    expect(result,contains('Total de lançamentos: 101'));
    expect(result,contains('Registro 0'));
    expect(result,contains('Registro 100'));
    expect(result,contains('Obra 35'));
    expect(result,contains('Acabamento'));
    expect(result.indexOf('Registro 100'),lessThan(result.indexOf('Registro 0')));
    expect(current.length,80); // Export must not mutate existing lists.
    expect(old.length,21);
  });
  test('sem entradas informa vazio, sem inventar registros',(){
    final result=WorksiteDiaryArchive.exportText('Obra A','Estrutura',[],[]);
    expect(result,contains('Nenhum lançamento registrado'));
    expect(result,contains('Total de lançamentos: 0'));
  });
  test('preserva diferença entre registro de obra A e obra B',(){
    final a=WorksiteDiaryArchive.exportText('Obra A','Estrutura',[log(1)],[]);
    final b=WorksiteDiaryArchive.exportText('Obra B','Fundação',[log(2)],[]);
    expect(a,contains('Obra A'));
    expect(a,isNot(contains('Obra B')));
    expect(b,contains('Obra B'));
    expect(b,isNot(contains('Registro 1')));
  });
}
