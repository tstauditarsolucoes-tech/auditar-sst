import 'dart:async';
import 'package:flutter_test/flutter_test.dart';
import '../lib/services/treatment_outbox.dart';

void main(){
  late Map<String,String> data;
  late TreatmentOutbox queue;
  const record={'type':'mensagem','message':'Conferir proteção'};
  setUp((){data={};queue=TreatmentOutbox(read:(k)async=>data[k],write:(k,v)async{data[k]=v;});});
  test('durable restart and uncertain response reuse the same id',()async{
    final id=await queue.enqueue('scope','A','GERAL','Geral',record);
    await queue.flush('scope',(_)async=>throw TimeoutException('offline'));
    final restored=TreatmentOutbox(read:(k)async=>data[k],write:(k,v)async{data[k]=v;});
    expect((await restored.list('scope')).single['record']['requestId'],id);
    final ids=<String>[];
    expect(await restored.flush('scope',(x)async{ids.add(x['record']['requestId'] as String);}),1);
    expect(ids,[id]);expect(await restored.list('scope'),isEmpty);
  });
  test('concurrent enqueue during send is not overwritten',()async{
    await queue.enqueue('s','A','GERAL','Geral',record);
    final gate=Completer<void>(),started=Completer<void>();
    final sending=queue.flush('s',(_)async{started.complete();await gate.future;});
    await started.future;
    final next=queue.enqueue('s','B','GERAL','Outra',record);
    gate.complete();await sending;final id=await next;
    expect((await queue.list('s')).single['id'],id);
  });
  test('rejection stops automatic retries and preserves ordered queue',()async{
    await queue.enqueue('s','A','GERAL','Geral',record);int calls=0;
    Future<void> reject(Map<String,dynamic> _)async{calls++;throw TreatmentRejected('Sem acesso');}
    await queue.flush('s',reject);await queue.flush('s',reject);expect(calls,1);
    expect((await queue.list('s')).single['blocked'],true);
    await queue.retry('s');expect(await queue.flush('s',(_)async{}),1);
  });
  test('account and endpoint scopes remain isolated',()async{
    final a=TreatmentOutbox.scope('https://one','a');
    final b=TreatmentOutbox.scope('https://one','b');
    final c=TreatmentOutbox.scope('https://two','a');
    expect({a,b,c}.length,3);
    await queue.enqueue(a,'A','GERAL','Geral',record);
    expect(await queue.list(b),isEmpty);expect(await queue.list(c),isEmpty);
    await queue.flush(a,(_)async=>throw TreatmentScopeChanged());
    expect((await queue.list(a)).length,1);
  });
  test('confirmed message is identified by its ID, not by other queued messages',() async {
    final first=await queue.enqueue('s','A','GERAL','Geral',record);
    final second=await queue.enqueue('s','B','GERAL','Geral',record);
    await queue.flush('s',(item)async{
      if(item['id']==second)throw TimeoutException('offline');
    });
    final remaining=await queue.list('s');
    expect(remaining.any((item)=>item['id']==first),isFalse);
    expect(remaining.any((item)=>item['id']==second),isTrue);
  });
  test('storage failure does not claim a durable enqueue',()async{
    final broken=TreatmentOutbox(read:(k)async=>null,write:(k,v)async=>throw StateError('disk'));
    await expectLater(broken.enqueue('s','A','GERAL','Geral',record),throwsStateError);
  });
  test('ack save failure keeps the original retry id',()async{
    final id=await queue.enqueue('s','A','GERAL','Geral',record);
    final broken=TreatmentOutbox(read:(k)async=>data[k],write:(k,v)async=>throw StateError('disk'));
    await expectLater(broken.flush('s',(_)async{}),throwsStateError);
    expect((await queue.list('s')).single['id'],id);
  });
  test('corrupt data is not overwritten',()async{
    data['s']='broken';
    await expectLater(queue.enqueue('s','A','GERAL','Geral',record),throwsFormatException);
    expect(data['s'],'broken');
  });
}
