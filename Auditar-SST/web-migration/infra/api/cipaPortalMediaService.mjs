/**
 * Private staging-only photo evidence for identified CIPA observations.
 * Never writes to legacy Drive, Apps Script or the production database.
 */
import {randomUUID,createHash} from 'node:crypto';
import {mkdir,writeFile,unlink,open} from 'node:fs/promises';
import {constants} from 'node:fs';
import {join} from 'node:path';
import {ApiError,withTenant,assertPrincipal} from './ncService.mjs';
import {withCipaMember,portalId,portalText} from './cipaPortalService.mjs';

const TYPES=Object.freeze({'image/jpeg':'jpg','image/png':'png','image/webp':'webp'});
const MAX=2*1024*1024;
const publicFields='id,entry_id,author_account_id,mime_type,sha256,size_bytes,created_at';
function digest(value){return createHash('sha256').update(value).digest('hex');}
function storageRoot(value){
  if(typeof value!=='string'||!value.startsWith('/')||value==='/'||value.includes('..')||value.length>200){
    throw new ApiError(503,'STORAGE_DISABLED','Armazenamento privado indisponivel');
  }
  return value;
}
function decodePhoto(payload){
  if(!Object.hasOwn(TYPES,payload.mimeType))throw new ApiError(415,'UNSUPPORTED_MEDIA','Use foto JPEG, PNG ou WebP');
  const encoded=payload.contentBase64;
  if(typeof encoded!=='string'||encoded.length<8||encoded.length>Math.ceil(MAX/3)*4+4||
      encoded.length%4!==0||!/^[A-Za-z0-9+/]+={0,2}$/.test(encoded)){
    throw new ApiError(400,'INVALID_IMAGE','Foto codificada incorretamente');
  }
  const data=Buffer.from(encoded,'base64');
  if(!data.length||data.length>MAX||data.toString('base64')!==encoded)throw new ApiError(413,'MEDIA_TOO_LARGE','Foto acima de 2 MB ou invalida');
  const jpeg=data.length>=4&&data[0]===255&&data[1]===216&&data[2]===255;
  const png=data.length>=8&&data.subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10]));
  const webp=data.length>=12&&data.toString('ascii',0,4)==='RIFF'&&data.toString('ascii',8,12)==='WEBP';
  if(!((payload.mimeType==='image/jpeg'&&jpeg)||(payload.mimeType==='image/png'&&png)||
      (payload.mimeType==='image/webp'&&webp)))throw new ApiError(415,'MEDIA_SIGNATURE','Formato da foto nao confere');
  return data;
}
function staff(p){
  assertPrincipal(p);
  if(!['adm','gestor','tecnico'].includes(p.role))throw new ApiError(403,'FORBIDDEN','Acesso exclusivo da equipe tecnica');
}
export function createCipaPortalMediaService(pool,storageDir){
  return {
    async upload(p,mandateId,body={}){
      const root=storageRoot(storageDir),id=portalId(mandateId),requestId=portalId(body.clientRequestId);
      const location=portalText(body.location,140),description=portalText(body.description,1600);
      const bytes=decodePhoto(body),sha=digest(bytes),message='Local: '+location+'\nSituacao observada: '+description;
      return withCipaMember(pool,p,async db=>{
        const mandate=(await db.query('SELECT status FROM sst.cipa_mandate WHERE company_id=$1 AND id=$2',[p.companyId,id])).rows[0];
        if(!mandate)throw new ApiError(404,'NOT_FOUND','Mandato indisponivel');
        if(mandate.status==='encerrado')throw new ApiError(409,'CLOSED_MANDATE','Mandato encerrado');
        const fingerprint=digest(JSON.stringify([p.accountId,id,location,description,body.mimeType,sha]));
        const previous=(await db.query('SELECT '+publicFields+',request_fingerprint FROM sst.cipa_portal_photo WHERE company_id=$1 AND client_request_id=$2',
          [p.companyId,requestId])).rows[0];
        if(previous){
          if(previous.request_fingerprint!==fingerprint)throw new ApiError(409,'IDEMPOTENCY_CONFLICT','Foto ja enviada com conteudo diferente');
          const {request_fingerprint:_,...item}=previous;return {item,replayed:true};
        }
        const entryData={mandateId:id,kind:'observacao',message};
        const entryFingerprint=digest(JSON.stringify([p.accountId,entryData]));
        const newEntry=await db.query('INSERT INTO sst.cipa_portal_entry(company_id,mandate_id,author_account_id,kind,message,client_request_id,request_fingerprint) '+
          'VALUES($1,$2,$3,$4,$5,$6,$7) ON CONFLICT(company_id,client_request_id) DO NOTHING RETURNING id',
          [p.companyId,id,p.accountId,'observacao',message,requestId,entryFingerprint]);
        let entryId=newEntry.rows[0]?.id;
        if(!entryId){
          const old=(await db.query('SELECT id,request_fingerprint FROM sst.cipa_portal_entry WHERE company_id=$1 AND client_request_id=$2',[p.companyId,requestId])).rows[0];
          if(!old||old.request_fingerprint!==entryFingerprint)throw new ApiError(409,'IDEMPOTENCY_CONFLICT','Chave ja utilizada');
          entryId=old.id;
        }
        const objectKey='cipa-portal/'+p.companyId+'/'+randomUUID()+'.'+TYPES[body.mimeType];
        const path=join(root,objectKey);
        await mkdir(join(root,'cipa-portal',p.companyId),{recursive:true,mode:0o700});
        await writeFile(path,bytes,{flag:'wx',mode:0o600});
        try{
          const inserted=await db.query('INSERT INTO sst.cipa_portal_photo(company_id,mandate_id,entry_id,author_account_id,object_key,mime_type,sha256,size_bytes,client_request_id,request_fingerprint) '+
            'VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10) ON CONFLICT(company_id,client_request_id) DO NOTHING RETURNING '+publicFields,
            [p.companyId,id,entryId,p.accountId,objectKey,body.mimeType,sha,bytes.length,requestId,fingerprint]);
          if(inserted.rowCount)return {item:inserted.rows[0],replayed:false};
          await unlink(path);
          const replay=(await db.query('SELECT '+publicFields+',request_fingerprint FROM sst.cipa_portal_photo WHERE company_id=$1 AND client_request_id=$2',
            [p.companyId,requestId])).rows[0];
          if(!replay||replay.request_fingerprint!==fingerprint)throw new ApiError(409,'IDEMPOTENCY_CONFLICT','Foto ja enviada com conteudo diferente');
          const {request_fingerprint:_,...item}=replay;return {item,replayed:true};
        }catch(error){
          await unlink(path).catch(()=>{});
          throw error;
        }
      });
    },
    async download(p,photoId,isStaff=false){
      const root=storageRoot(storageDir),id=portalId(photoId);
      if(isStaff)staff(p);
      return (isStaff?withTenant:withCipaMember)(pool,p,async db=>{
        const row=(await db.query('SELECT '+publicFields+',object_key FROM sst.cipa_portal_photo WHERE company_id=$1 AND id=$2',
          [p.companyId,id])).rows[0];
        if(!row)throw new ApiError(404,'NOT_FOUND','Foto indisponivel');
        const expected='cipa-portal/'+p.companyId+'/';
        if(!row.object_key.startsWith(expected)||
           !/^[0-9a-f-]{36}\.(jpg|png|webp)$/.test(row.object_key.slice(expected.length))){
          throw new ApiError(503,'MEDIA_UNAVAILABLE','Caminho privado invalido');
        }
        const handle=await open(join(root,row.object_key),constants.O_RDONLY|constants.O_NOFOLLOW);
        let data;
        try{
          const stat=await handle.stat();
          if(!stat.isFile()||stat.size!==Number(row.size_bytes)||stat.size>MAX)throw new ApiError(503,'MEDIA_UNAVAILABLE','Arquivo incompleto');
          data=await handle.readFile();
        }finally{await handle.close();}
        if(digest(data)!==row.sha256)throw new ApiError(503,'MEDIA_UNAVAILABLE','Integridade da foto invalida');
        return {mimeType:row.mime_type,data};
      });
    },
  };
}
