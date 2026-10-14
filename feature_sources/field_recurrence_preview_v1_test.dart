import 'field_recurrence_preview_v1.dart';
void expectField(bool ok,String message){if(!ok)throw StateError(message);}
void main(){
 const history=<FieldRecurrenceItem>[
  FieldRecurrenceItem('machine','A','ob1','Fabricação','Correia da prensa sem proteção'),
  FieldRecurrenceItem('fire','A','ob1','Fabricação','Extintor sem sinalização'),
  FieldRecurrenceItem('companyB','B','ob1','Fabricação','Correia da prensa exposta'),
  FieldRecurrenceItem('otherSite','A','ob2','Fabricação','Correia da prensa exposta'),
  FieldRecurrenceItem('otherSector','A','ob1','Manutenção','Correia da prensa exposta')
 ];
 final found=FieldRecurrencePreview.find(companyId:'A',worksiteId:'ob1',sector:'Fabricação',description:'Prensa com correia sem proteção',history:history);
 expectField(found.length==1&&found.single.item.id=='machine','isolar empresa, obra e setor');
 expectField(FieldRecurrencePreview.find(companyId:'A',worksiteId:'ob1',sector:'Fabricação',description:'Botão de emergência não funcionou',history:history).isEmpty,'nao misturar botoeira e extintor');
 expectField(FieldRecurrencePreview.find(companyId:'A',worksiteId:'ob1',sector:'Fabricação',description:'',history:history).isEmpty,'entrada vazia');
 expectField(FieldRecurrencePreview.normalize('PROTEÇÃO / Ruído')=='protecao ruido','acentos');
 print('Field recurrence smoke tests passed');
}
