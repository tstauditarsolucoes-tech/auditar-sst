// CI Dart puro: armazenamento de memoria FICTICIO, sem instalar no aplicativo.
import 'dart:async';
import 'native_draft_outbox.dart';
class MemoryStore implements NativeDraftJournalStore {
  List<NativeDraft> rows = [];
  @override
  Future<List<NativeDraft>> read() async => List<NativeDraft>.of(rows);
  @override
  Future<void> replaceAtomically(List<NativeDraft> all) async {
    rows = List<NativeDraft>.of(all);
  }
}
void check(bool valid, String why) {
  if (!valid) throw StateError(why);
}
const uuid='92000000-0000-4000-8000-000000000001';
const another='92000000-0000-4000-8000-000000000002';
NativeDraft sample(String id) => NativeDraft(
  requestId:id,kind:'inspection',
  payload:{'inspectionType':'vistoria','title':'Vistoria TESTE',
    'clientRequestId':id},
);
DraftResponse ack() => const DraftResponse(201,{
  'item':{'id':'d0000000-0000-4000-8000-000000000001'},
  'syncEnabled':false,'legacyQueueAcknowledged':false,
});
Future<void> expectThrows(Future<void> Function() action) async {
  var thrown=false;
  try{await action();}catch(_){thrown=true;}
  check(thrown,'Deveria rejeitar a operação insegura');
}
Future<void> main() async {
  final memory=MemoryStore();
  final first=NativeDraftOutbox(memory);
  await first.enqueue(sample(uuid));
  await first.enqueue(sample(uuid));
  check(memory.rows.length==1,'Mesmo UUID nao pode gerar duas operacoes');
  await expectThrows(()=>first.enqueue(NativeDraft(
    requestId:uuid,kind:'inspection',
    payload:{'clientRequestId':uuid,'title':'ALTERADO'},
  )));
  await expectThrows(()=>first.enqueue(sample('UUID_INVALIDO')));
  var attempts=0;
  final offline=await first.drain((draft)async{
    attempts++;throw const FormatException('Offline');
  });
  check(attempts==1&&offline.committed==0&&offline.stillPending==1,
      'Falha de rede nunca reconhece envio');
  check(memory.rows.single.requestId==uuid,'O UUID precisa permanecer');
  final reboot=NativeDraftOutbox(memory);
  final suspicious=await reboot.drain((draft)async=>const DraftResponse(201,{
    'item':{'id':'d0000000-0000-4000-8000-000000000001'},
    'syncEnabled':true,'legacyQueueAcknowledged':true,
  }));
  check(suspicious.committed==0&&suspicious.stillPending==1,
    'Resposta incompatível não é ACK');
  final sent=await reboot.drain((draft)async{
    check(draft.requestId==uuid,'Retentativa precisa manter UUID');
    return ack();
  });
  check(sent.committed==1&&sent.stillPending==0,
    'Só transação idempotente confirmada marca entregue');
  check(memory.rows.single.state==DraftState.acknowledged,
    'ACK persistido após sucesso do servidor');
  check(memory.rows.single.remoteId=='d0000000-0000-4000-8000-000000000001',
    'ID retornado pelo servidor deve ficar no diário novo');
  await reboot.enqueue(sample(another));
  final refused=await reboot.drain((draft)async=>const DraftResponse(401,null));
  check(refused.stillPending==1&&memory.rows.last.state==DraftState.pending,
    'Token expirado para todo o lote');
  final conflict=await reboot.drain((draft)async=>const DraftResponse(409,{
    'code':'IDEMPOTENCY_CONFLICT',
  }));
  check(conflict.conflicts==1&&memory.rows.last.state==DraftState.conflict,
    'Conteúdo divergente não pode ser reenviado automaticamente');
  check(memory.rows.first.state==DraftState.acknowledged,
    'Conflito de um registro não apaga sucesso anterior');
  print('NATIVE_DRAFT_OUTBOX_POLICY_CI_ONLY_OK');
}
