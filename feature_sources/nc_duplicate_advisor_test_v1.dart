import 'nc_duplicate_advisor_v1.dart';

void check(bool ok, String label) {
  if(!ok)throw StateError('NC_DUPLICADA: '+label);
}

Map<String,dynamic> row(String id,String company,String sector,
    String description,{String status='Aberta'})=> {
  'id':id,'company_id':company,'sector':sector,
  'description':description,'status':status,
};

void main() {
  final rows=[
    row('nc1','empresa-A','Produção','Esteira sem proteção'),
    row('nc2','empresa-A','Moagem','Moinho sem proteção'),
    row('nc3','empresa-B','Produção','Esteira sem proteção'),
    row('nc4','empresa-A','Produção','Esteira sem proteção',
        status:'Corrigida e validada'),
    row('nc5','empresa-A','Produção','Esteira sem proteção',
        status:'Concluída'),
    row('nc6','empresa-A','Produção','Andaime sem guarda-corpo'),
    row('nc7','empresa-A','Produção','Esteira transportadora sem proteção'),
    row('nc7','empresa-A','Produção','Esteira transportadora sem proteção'),
    {'id':'sem-empresa','description':'Esteira sem proteção'},
    {'company_id':'empresa-A','description':'Esteira sem proteção'},
  ];

  final hits=NcDuplicateAdvisor.suggest(
    companyId:'empresa-A',description:'Esteira transportadora sem proteção',
    sector:'Produção',existingOpenNcs:rows);
  check(hits.map((c)=>c.id).toSet().containsAll({'nc1','nc5','nc7'}),
    'sugere NC local por termos em comum mesmo com descrição diferente');
  check(hits.every((c)=>c.companyId=='empresa-A'),
    'jamais mistura dados de outras empresas');
  check(hits.every((c)=>c.sector=='Produção'),
    'setor diferente não deve ser sugerido');
  check(!hits.any((c)=>c.id=='nc4'),'exclui NC validada');
  check(!hits.any((c)=>c.id=='nc6'),'não confunde máquina e andaime');
  check(hits.where((c)=>c.id=='nc7').length==1,'ID não duplica');
  check(hits.any((c)=>c.id=='nc5'),
    'vistoria Concluída não equivale a NC corrigida');

  final accents=NcDuplicateAdvisor.suggest(
    companyId:'empresa-A',description:'Andaime sem guarda corpo',
    existingOpenNcs:rows,sector:'Produção');
  check(accents.any((c)=>c.id=='nc6'),'normalização de hífen e acentos');

  final different=NcDuplicateAdvisor.suggest(
    companyId:'empresa-A',description:'Serra circular sem coifa',
    existingOpenNcs:rows);
  check(different.isEmpty,'não criar falso positivo com objeto diverso');

  final short=NcDuplicateAdvisor.suggest(
    companyId:'empresa-A',description:'Proteção',
    existingOpenNcs:rows);
  check(short.isEmpty,'descrição genérica não gera alerta');

  final limit=NcDuplicateAdvisor.suggest(
    companyId:'empresa-A',description:'Esteira transportadora sem proteção',
    existingOpenNcs:rows,maxResults:1);
  check(limit.length==1,'limite preservado');

  var invalid=false;
  try {
    NcDuplicateAdvisor.suggest(companyId:'',description:'Esteira sem proteção',
      existingOpenNcs:rows);
  }catch(_){invalid=true;}
  check(invalid,'empresa obrigatória');
  print('NC_DUPLICADA_12_VERIFICACOES_OK');
}
