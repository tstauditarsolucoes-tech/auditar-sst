/** Pure, disabled-by-default legacy CIPA read adapter. No DB, network or production writes. */
import {createHash} from 'node:crypto';

export const LEGACY_CIPA_TYPES=Object.freeze({
  CIPA_MANDATO:'mandate',CIPA_MEMBRO:'member',CIPA_REUNIAO:'meeting',
  CIPA_ATA:'minutes',CIPA_ACAO:'action',CIPA_DOCUMENTO:'document',
  CIPA_COMISSAO_ELEITORAL:'election_committee'
});
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
function requireUuid(value,label){if(typeof value!=='string'||!UUID.test(value))throw new TypeError(label+' must be UUID');return value.toLowerCase();}
function requireText(value,label,max=240){if(typeof value!=='string'||!value.trim()||value.length>max)throw new TypeError(label+' invalid');return value.trim();}
function plainObject(value){return value!==null&&typeof value==='object'&&!Array.isArray(value);}
export function normalizeLegacyCipaRecord(record,expectedCompanyId){
  if(!plainObject(record))throw new TypeError('record must be object');
  const companyId=requireUuid(expectedCompanyId,'expectedCompanyId');
  if(requireUuid(record.companyId,'companyId')!==companyId)throw new Error('TENANT_MISMATCH');
  const type=requireText(record.type,'type',50);
  if(!Object.hasOwn(LEGACY_CIPA_TYPES,type))throw new Error('UNSUPPORTED_CIPA_TYPE');
  const id=requireUuid(record.id,'id');
  const title=requireText(record.title,'title');
  if(record.payload!==undefined&&!plainObject(record.payload))throw new TypeError('payload must be object');
  const payload=record.payload??{};
  // Only metadata. Attachments, signatures and free-form payload are deliberately not exported.
  const source={system:'flutter_sst_record',companyId,type,id};
  const fingerprint=createHash('sha256').update(JSON.stringify([source,title,record.status??null,record.priority??null,record.date??null,record.dueDate??null])).digest('hex');
  return Object.freeze({source,kind:LEGACY_CIPA_TYPES[type],title,status:typeof record.status==='string'?record.status:null,
    priority:typeof record.priority==='string'?record.priority:null,date:typeof record.date==='string'?record.date:null,
    dueDate:typeof record.dueDate==='string'?record.dueDate:null,fingerprint,
    // No automatic mapping from legacy IDs to portal IDs.
    portalId:null,requiresMapping:true});
}
export function prepareLegacyCipaPreview(records,expectedCompanyId,{enabled=false}={}){
  if(enabled!==true)throw new Error('LEGACY_CIPA_PREVIEW_DISABLED');
  if(!Array.isArray(records)||records.length>1000)throw new TypeError('records must be array of at most 1000');
  const seen=new Set(),normalized=[];
  for(const record of records){
    const row=normalizeLegacyCipaRecord(record,expectedCompanyId);
    const key=[row.source.companyId,row.source.type,row.source.id].join(':');
    if(seen.has(key))throw new Error('DUPLICATE_SOURCE_RECORD');
    seen.add(key);normalized.push(row);
  }
  return Object.freeze({mode:'preview_only',count:normalized.length,records:normalized});
}
