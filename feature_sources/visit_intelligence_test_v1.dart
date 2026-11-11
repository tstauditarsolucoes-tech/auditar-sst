import 'visit_intelligence_v1.dart';

void check(bool success,String message){
  if(!success)throw StateError('VISITA_INTELIGENTE: $message');
}
Map<String,Object?> row(String id,String company,String round,
    String kind,{String sector='Produção',
      String description='Proteção da correia ausente',
      String status='Aberta',String? correctionStatus}) => {
  'id':id,'companyId':company,'status':status,
  'payload':{
    'roundId':round,
    'observationKind':kind,
    'sector':sector,
    'description':description,
    if(correctionStatus!=null)'correctionStatus':correctionStatus,
  }
};

void main() {
  final data=[
    row('a1','empresa-A','r1','Não conformidade'),
    row('a2','empresa-A','r2','Nao conformidade'),
    row('a2','empresa-A','r2','Nao conformidade'),
    row('b1','empresa-B','r1','Não conformidade'),
    row('a3','empresa-A','r2','Conformidade'),
    row('a4','empresa-A','r3','Não conformidade',
      status:'Concluída',sector:'Expedição',
      description:'Piso escorregadio na entrada'),
    row('a5','empresa-A','r3','Condição insegura',
      correctionStatus:'Resolvida'),
    row('a6','empresa-A','r4','Risco',
      sector:'Moagem',description:'Partes móveis expostas no moinho',
      correctionStatus:'Validação pendente'),
    row('a7','empresa-A','','Não conformidade'),
    <String,Object?>{'id':'a8','companyId':'empresa-A','payload':'invalido'},
  ];
  final summary=VisitIntelligence.fromLocalRondas(
    companyId:'empresa-A',records:data);
  check(summary.savedRounds==4,'não misturar empresas ou contar achados como rondas');
  check(summary.openObservations==4,
    'observações abertas são únicas e visita concluída não fecha NC');
  check(summary.recurrenceCandidates==2,
    'recorrência precisa de descrição e setor iguais em rondas diferentes');
  check(summary.items.length==4,'exibir itens disponíveis sem inventar');
  check(summary.items.every((x)=>x.id!='b1'),
    'não expor dado de outra empresa');
  check(summary.items.any((x)=>x.id=='a4'),
    'vistoria concluída ainda requer avaliação da NC');

  final other=VisitIntelligence.fromLocalRondas(
    companyId:'empresa-B',records:data);
  check(other.savedRounds==1&&other.openObservations==1,
    'isolamento por empresa');
  check(other.recurrenceCandidates==0,'não sugerir recorrência entre empresas');

  final noData=VisitIntelligence.fromLocalRondas(
    companyId:'empresa-A',records:const []);
  check(!noData.hasLocalData&&noData.items.isEmpty,
    'sem dados não significa empresa sem riscos');

  final sameRound=VisitIntelligence.fromLocalRondas(
    companyId:'empresa-A',records:[
      row('s1','empresa-A','r1','Não conformidade'),
      row('s2','empresa-A','r1','Condição insegura'),
    ]);
  check(sameRound.recurrenceCandidates==0,
    'duas observações na mesma ronda não são recorrência');

  final missing=VisitIntelligence.fromLocalRondas(
    companyId:'empresa-A',records:[
      row('d1','empresa-A','r1','Não conformidade',
        sector:'',description:''),
      row('d2','empresa-A','r2','Não conformidade',
        sector:'',description:''),
    ]);
  check(missing.recurrenceCandidates==0,
    'sem setor/descrição não classificar como recorrente');

  final limited=VisitIntelligence.fromLocalRondas(
    companyId:'empresa-A',records:data,maxVisible:2);
  check(limited.openObservations==4&&limited.items.length==2,
    'limitar visualização sem alterar totais');

  var invalid=false;
  try{VisitIntelligence.fromLocalRondas(companyId:'',records:[]);}
  catch(_){invalid=true;}
  check(invalid,'não permitir consulta sem identidade de empresa');
  print('VISITA_INTELIGENTE_TESTES_ISOLAMENTO_RECORRENCIA_OK');
}
