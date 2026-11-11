import 'android_unified_visit_metrics_v1.dart';

void check(bool value,String why) {
  if(!value)throw StateError('INDICADORES_VISTORIAS: $why');
}

Map<String,Object?> record(String id,String company,String round,
    String kind,{String status='Aberta',String? correctionStatus}) => {
  'id':id,'companyId':company,'status':status,
  'payload':{
    'roundId':round,'observationKind':kind,
    if(correctionStatus!=null)'correctionStatus':correctionStatus,
  },
};

void main() {
  final records=[
    record('r1','empresa-A','ronda-01','Conformidade'),
    record('r2','empresa-A','ronda-01','Condição insegura'),
    record('r3','empresa-A','ronda-01','Ato inseguro',status:'Corrigida'),
    record('r4','empresa-B','ronda-01','Não conformidade'),
    record('r4','empresa-B','ronda-01','Não conformidade'),
    record('r5','empresa-A','','Não conformidade'),
    <String,Object?>{'id':'x','companyId':'empresa-A','payload':'invalido'},
  ];
  final total=UnifiedVisitMetrics.calculate(records);
  check(total.rounds==2,'contar uma ronda por empresa, sem repetir achados');
  check(total.openIssues==2,'contar somente NCs abertas não repetidas');
  final withoutLinked=UnifiedVisitMetrics.calculate(records,
    existingIssueRecordIds:{'r2'});
  check(withoutLinked.rounds==2&&withoutLinked.openIssues==1,
    'não duplicar NC vinculada a outra tabela');
  final filtered=UnifiedVisitMetrics.calculate(records,
    companyIds:{'empresa-A'});
  check(filtered.rounds==1&&filtered.openIssues==1,
    'não misturar outras empresas no resumo');
  final linkedByCompany=UnifiedVisitMetrics.calculate(records,
    existingIssueRecordIds:{'empresa-B|r4'});
  check(linkedByCompany.openIssues==1,
    'referência de empresa específica não oculta outra NC');
  final alreadyCounted=UnifiedVisitMetrics.calculate(records,
    alreadyCountedRoundKeys:{'empresa-A|ronda-01'});
  check(alreadyCounted.rounds==1&&alreadyCounted.openIssues==2,
    'não somar ronda já incluída em outro contador');
  final notValidated=UnifiedVisitMetrics.calculate([
    record('c1','empresa-A','r2','Não conformidade',status:'Concluída'),
    record('c2','empresa-A','r2','Condição insegura',
      correctionStatus:'Validação pendente'),
    record('c3','empresa-A','r2','Não conformidade',
      correctionStatus:'Em correção'),
    record('c4','empresa-A','r2','Não conformidade',
      correctionStatus:'Validando'),
    record('c5','empresa-A','r2','Não conformidade',
      correctionStatus:'Resolvida'),
  ]);
  check(notValidated.rounds==1&&notValidated.openIssues==4,
    'vistoria finalizada, validação pendente e em correção continuam abertas');
  final empty=UnifiedVisitMetrics.calculate(const []);
  check(empty.rounds==0&&empty.openIssues==0,
    'consulta vazia não cria vistorias');
  print('INDICADORES_VISTORIAS_7_CENARIOS_OK');
}
