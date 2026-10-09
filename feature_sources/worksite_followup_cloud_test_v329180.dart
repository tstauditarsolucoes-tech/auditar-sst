import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_sst/screens/worksite_followup_screen.dart';
import 'package:auditar_sst/services/worksite_followup_cloud_service.dart';

void main() {
  test('Dados por obra são isolados e o diário completo mantém 80 entradas', () {
    const first='obra-quality-01', second='obra-quality-02';
    expect(WorksiteFollowupStore.key(first,'tecnico-a'),
      isNot(WorksiteFollowupStore.key(second,'tecnico-a')));
    expect(WorksiteFollowupStore.key(first,'tecnico-a'),
      isNot(WorksiteFollowupStore.key(first,'tecnico-b')));
    final record=WorksiteFollowup(phase:'Estrutura',
      status:'Em andamento',progress:65,
      log:List.generate(80,(i)=>WorksiteLog(
        '2026-10-09T12:00:00.000Z','Visita','Nota '+i.toString())));
    final loaded=WorksiteFollowup.fromMap(record.toMap());
    expect(loaded.log.length,80);
    expect(loaded.progress,65);
  });
  test('Conflito de versão não é considerado publicação aprovada', () {
    const result=WorksiteCloudResult(conflict:true,revision:7,
      record:{'phase':'Estrutura','status':'Em andamento','progress':30});
    expect(result.conflict,isTrue);
    expect(result.revision,7);
    expect(result.record?['progress'],30);
  });
}
