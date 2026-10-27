import test from 'node:test';
import assert from 'node:assert/strict';
import {nativeDraftPayload} from './nativeDraftContract.mjs';
const key='93000000-0000-4000-8000-000000000001';
test('contrato nativo exige clientRequestId e so aceita campos novos',()=>{
 const draft={inspectionType:'vistoria',title:'Vistoria CI',description:'',sector:'',
   location:'',clientRequestId:key};
 assert.deepEqual(nativeDraftPayload(draft,'inspection'),draft);
 const finding={shortTitle:'NC CI',description:'Exemplo ficticio',recommendation:'',
   probability:2,severity:3,recurring:false,clientRequestId:key};
 assert.deepEqual(nativeDraftPayload(finding,'finding'),finding);
 for(const bad of [
   {...draft,companyId:'20000000-0000-4000-8000-000000000002'},
   {...draft,role:'adm'},{...draft,syncKey:'legado'},
   {...draft,changes:[]},{...draft,rows:[]},{...draft,deviceId:'x'},
   {...draft,clientRequestId:'invalid'},{...draft,clientRequestId:null},
   {...draft,clientRequestId:undefined},[],
 ]){
   assert.throws(()=>nativeDraftPayload(bad,'inspection'),err=>err.status===400);
 }
 assert.throws(()=>nativeDraftPayload({...finding,inspectionId:'forjado'},'finding'),e=>e.status===400);
 assert.throws(()=>nativeDraftPayload(draft,'legacy'),e=>e.status===400);
});
