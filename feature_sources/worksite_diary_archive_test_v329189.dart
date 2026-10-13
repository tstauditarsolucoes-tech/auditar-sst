import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_sst/screens/worksite_followup_screen.dart';

void main(){
  WorksiteLog entry(int i)=>WorksiteLog(
    '2026-10-13T12:00:00.'+i.toString().padLeft(3,'0')+'Z',
    'Visita','Registro '+i.toString());
  test('arquivo separado por obra e usuário',(){
    expect(WorksiteDiaryArchive.key('quality-35','tst'),
      isNot(WorksiteDiaryArchive.key('quality-36','tst')));
    expect(WorksiteDiaryArchive.key('quality-35','tst'),
      isNot(WorksiteDiaryArchive.key('quality-35','outro')));
  });
  test('81 registros conservam 80 atuais e 1 antigo',(){
    final record=WorksiteFollowup(log:[for(var i=0;i<81;i++)entry(i)]);
    expect(WorksiteDiaryArchive.recent(record).log.length,80);
    expect(WorksiteDiaryArchive.overflow(record).length,1);
    expect(WorksiteDiaryArchive.overflow(record).single.note,'Registro 80');
    expect(WorksiteDiaryArchive.recent(record).toMap()['log'],hasLength(80));
  });
  test('nova tentativa não duplica entrada no arquivo',(){
    final old=[entry(81),entry(82)];
    final merged=WorksiteDiaryArchive.unique(old,[entry(82),entry(83)]);
    expect(merged.length,3);
    expect(merged.last.note,'Registro 83');
  });
  test('com 80 registros não há perda nem arquivo adicional',(){
    final record=WorksiteFollowup(log:[for(var i=0;i<80;i++)entry(i)]);
    expect(WorksiteDiaryArchive.overflow(record),isEmpty);
    expect(WorksiteDiaryArchive.recent(record).log.length,80);
  });
}
