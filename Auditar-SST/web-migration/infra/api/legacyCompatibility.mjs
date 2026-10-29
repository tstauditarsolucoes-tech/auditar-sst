/**
 * Auditoria de COMPATIBILIDADE, nao sincronizador.
 * Aceita so totais sem nomes, IDs de registros, fotos, textos ou credenciais.
 * Nao conecta ao banco nem confirma ACK de pendencias do SQLite.
 */
import {ApiError} from './ncService.mjs';

const LEGACY_TABLES=Object.freeze([
  'companies','worksites','sectors','workers','training_controls',
  'training_requirements','checklist_templates','checklist_items',
  'cipa_elections','cipa_candidates','cipa_voters','inspections',
  'answers','non_conformities','action_plans','sst_records',
]);
const TARGETS=Object.freeze({
  companies:'sst.company',
  inspections:'sst.inspection',
  non_conformities:'sst.non_conformity',
});
const MAX_COUNT=10_000_000;
const PERMITTED_FIELDS=['marker','source','platform','tables'];
const TABLE_FIELDS=['name','count','pendingDeletes'];

function ownKeys(value,allowed){
  return value && typeof value==='object' && !Array.isArray(value) &&
    Object.keys(value).every(key=>allowed.includes(key));
}
function requireAdm(principal){
  if(principal?.role!=='adm'){
    throw new ApiError(403,'FORBIDDEN','Somente ADM do ambiente novo de homologacao');
  }
}
export function legacyCompatibilityCapabilities(principal){
  requireAdm(principal);
  return {
    mode:'DRY_RUN_METADATA_ONLY',
    writeEnabled:false,legacySyncModified:false,
    source:'Flutter SQLite + Apps Script',
    destination:'Node + PostgreSQL de homologacao',
    tableCount:LEGACY_TABLES.length,
    mappedStructures:Object.keys(TARGETS).length,
    dataImportEnabled:false,
    note:'Nao substituir endpoint, credenciais nem fila local de sincronizacao.',
  };
}
export function inspectLegacyManifest(principal,manifest){
  requireAdm(principal);
  if(!ownKeys(manifest,PERMITTED_FIELDS)||
     manifest.marker!=='SST_LEGACY_METADATA_ONLY'||
     manifest.source!=='legacy-device-sync-v1'||
     !['android','windows'].includes(manifest.platform)||
     !Array.isArray(manifest.tables)||
     manifest.tables.length===0||manifest.tables.length>LEGACY_TABLES.length){
    throw new ApiError(422,'INVALID_MANIFEST','Somente manifesto de contagens, sem registros.');
  }
  const seen=new Set();
  const results=[];
  for(const entry of manifest.tables){
    if(!ownKeys(entry,TABLE_FIELDS)||
       !TABLE_FIELDS.every(key=>Object.hasOwn(entry,key))||
       !LEGACY_TABLES.includes(entry.name)||seen.has(entry.name)||
       !Number.isSafeInteger(entry.count)||entry.count<0||entry.count>MAX_COUNT||
       !Number.isSafeInteger(entry.pendingDeletes)||entry.pendingDeletes<0||
       entry.pendingDeletes>MAX_COUNT){
      throw new ApiError(422,'INVALID_MANIFEST','Tabela, contagem ou campos nao permitidos.');
    }
    seen.add(entry.name);
    results.push({
      table:entry.name,
      target:TARGETS[entry.name]||null,
      status:TARGETS[entry.name]?'REQUIRES_FIELD_AND_ID_MAPPING':'NOT_IMPLEMENTED',
      records:entry.count,
      queuedDeletes:entry.pendingDeletes,
    });
  }
  // Mesmo tabelas com estruturas parecidas NAO estao liberadas para importar:
  // regras de tenant, conflito, IDs, historico, arquivos e row versions nao conferidas.
  return {
    assessment:'BLOCKED_FOR_REAL_SYNC',
    safeToSwitchEndpoint:false,
    writesPerformed:0,
    localQueueAcknowledged:0,
    remoteChangesApplied:0,
    platform:manifest.platform,
    totals:{
      tablesChecked:results.length,
      records:results.reduce((sum,item)=>sum+item.records,0),
      queuedDeletes:results.reduce((sum,item)=>sum+item.queuedDeletes,0),
      tablesWithoutTarget:results.filter(item=>!item.target).length,
    },
    tables:results,
    additionalBlockers:[
      'Identidades e IDs: mapear empresas, usuarios e perfis sem perda',
      'Outbox offline: ACK, idempotencia e conflitos ainda nao equivalentes',
      'Fotos, assinaturas e documentos: migracao cifrada e hashes pendentes',
      'Restauracao e rollback de backup real ainda nao homologados',
    ],
  };
}
