import 'android_unified_visit_metrics_v1.dart';

Map<String,Object?> record(String id,String company,String round,
    String kind,{String status='Aberta'}) => {
  'id':id, 'companyId':company, 'status':status,
  'payload':{'roundId':round,'observationKind':kind},
};

void main() {
  final records=[
    record('r1','empresa-A','ronda-01','Conformidade'),
    record('r2','empresa-A','ronda-01','Condição insegura'),
    record('r3','empresa-A','ronda-01','Ato inseguro',status:'Corrigida'),
    record('r4','empresa-B','ronda-01','Não conformidade'),
    record('r4','empresa-B','ronda-01','Não conformidade'), // repetido
    record('r5','empresa-A','','Não conformidade'), // avulsa: não é ronda
    {'id':'x','companyId':'empresa-A','payload':'invalido'},
  ];
  final sum=UnifiedVisitMetrics.calculate(records);
  assert(sum.rounds==2, 'cada ronda deve contar uma vez por empresa');
  assert(sum.openIssues==2, 'apenas NCs abertas e sem duplicidade');
  final linked=UnifiedVisitMetrics.calculate(records,
    existingIssueRecordIds:{'r2'});
  assert(linked.rounds==2 && linked.openIssues==1,
    'NC já refletida em checklist não pode ser duplicada');
  final empty=UnifiedVisitMetrics.calculate(const []);
  assert(empty.rounds==0 && empty.openIssues==0);
  print('UNIFIED_VISITS_METRICS_OK');
}
