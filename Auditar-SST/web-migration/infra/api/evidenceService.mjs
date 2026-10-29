/**
 * FOTO FICTICIA PARA HOMOLOGACAO PRIVADA.
 * Filesystem dedicado em volume Docker, nunca Drive/Apps Script/producao.
 * Sem raiz explicitamente habilitada: endpoints negam acesso.
 */
import {randomUUID,createHash} from 'node:crypto';
import {mkdir,writeFile,unlink,open} from 'node:fs/promises';
import {constants} from 'node:fs';
import {join} from 'node:path';
import {ApiError,withTenant} from './ncService.mjs';

const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const TYPES={'image/jpeg':'jpg','image/png':'png','image/webp':'webp'};
const MAX=2*1024*1024;
function id(value){
  if(typeof value!=='string'||!UUID.test(value))throw new ApiError(400,'INVALID_ID','Identificador invalido');
  return value;
}
function bytes(payload){
  if(!Object.hasOwn(TYPES,payload.mimeType))throw new ApiError(415,'UNSUPPORTED_MEDIA','Imagem deve ser JPEG, PNG ou WebP');
  const value=payload.contentBase64;
  if(typeof value!=='string'||!value||value.length>Math.ceil(MAX/3)*4+4||
      value.length%4!==0||!/^[A-Za-z0-9+/]+={0,2}$/.test(value)){
    throw new ApiError(400,'INVALID_IMAGE','Imagem base64 invalida');
  }
  const buf=Buffer.from(value,'base64');
  if(!buf.length||buf.length>MAX||buf.toString('base64')!==value){
    throw new ApiError(413,'MEDIA_TOO_LARGE','Imagem invalida ou maior que 2 MB');
  }
  const jpeg=buf.length>=4&&buf[0]===0xff&&buf[1]===0xd8&&buf[2]===0xff;
  const png=buf.length>=8&&buf.subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10]));
  const webp=buf.length>=12&&buf.toString('ascii',0,4)==='RIFF'&&buf.toString('ascii',8,12)==='WEBP';
  if(!((payload.mimeType==='image/jpeg'&&jpeg)||(payload.mimeType==='image/png'&&png)||
    (payload.mimeType==='image/webp'&&webp)))throw new ApiError(415,'MEDIA_SIGNATURE','Assinatura da imagem nao confere');
  return buf;
}
function allowedRoot(value){
  if(typeof value!=='string'||!value.startsWith('/')||value.includes('..')||
      value==='/'||value.length>200)throw new ApiError(503,'STORAGE_DISABLED','Armazenamento privado indisponivel');
  return value;
}
function digest(buf){return createHash('sha256').update(buf).digest('hex');}
const returnFields='id,inspection_id,non_conformity_id,sha256,mime_type,size_bytes,kind,created_at';
async function visible(db,p,row){
  if(p.role!=='cliente')return;
  if(row.non_conformity_id){
    const result=await db.query(
      'SELECT n.id FROM sst.non_conformity n LEFT JOIN sst.inspection i '+
      'ON n.inspection_id=i.id AND n.company_id=i.company_id '+
      "WHERE n.company_id=$1 AND n.id=$2 AND (n.inspection_id IS NULL OR i.status='concluida')",
      [p.companyId,row.non_conformity_id]);
    if(result.rowCount)return;
  } else if(row.inspection_id) {
    const result=await db.query(
      "SELECT id FROM sst.inspection WHERE company_id=$1 AND id=$2 AND status='concluida'",
      [p.companyId,row.inspection_id]);
    if(result.rowCount)return;
  }
  throw new ApiError(404,'NOT_FOUND','Arquivo indisponivel');
}
export function createEvidenceService(pool,storageDir) {
  const requireStorage=()=>allowedRoot(storageDir);
  return {
    async upload(principal,payload={}){
      const root=requireStorage();
      const data=bytes(payload);
      const key=id(payload.clientRequestId);
      const inspectionId=payload.inspectionId? id(payload.inspectionId):null;
      const ncId=payload.nonConformityId? id(payload.nonConformityId):null;
      if(Number(Boolean(inspectionId))+Number(Boolean(ncId))!==1)throw new ApiError(400,'INVALID_LINK','Vincule foto a uma vistoria ou NC');
      const sha=digest(data);
      return withTenant(pool,principal,async(db,p)=>{
        const original=await db.query(
          'SELECT '+returnFields+' FROM sst.evidence WHERE company_id=$1 AND client_request_id=$2',
          [p.companyId,key],
        );
        if(original.rowCount){
          const e=original.rows[0];
          if(e.sha256!==sha||e.inspection_id!==inspectionId||e.non_conformity_id!==ncId||
              e.mime_type!==payload.mimeType){
            throw new ApiError(409,'IDEMPOTENCY_CONFLICT','Arquivo ja enviado com dados diferentes');
          }
          await visible(db,p,e);
          return {item:e,replayed:true};
        }
        if(inspectionId){
          if(p.role==='cliente')throw new ApiError(403,'FORBIDDEN','Cliente nao pode anexar em vistoria interna');
          const inspection=await db.query(
            'SELECT id FROM sst.inspection WHERE company_id=$1 AND id=$2',
            [p.companyId,inspectionId],
          );
          if(!inspection.rowCount)throw new ApiError(404,'NOT_FOUND','Vistoria indisponivel');
        }
        if(ncId){
          const nc=await db.query(
            "SELECT n.id FROM sst.non_conformity n LEFT JOIN sst.inspection i "+
            "ON n.inspection_id=i.id AND n.company_id=i.company_id "+
            "WHERE n.company_id=$1 AND n.id=$2 "+
            (p.role==='cliente'?"AND (n.inspection_id IS NULL OR i.status='concluida')":""),
            [p.companyId,ncId],
          );
          if(!nc.rowCount)throw new ApiError(404,'NOT_FOUND','NC indisponivel');
        }
        const objectKey=p.companyId+'/'+randomUUID()+'.'+TYPES[payload.mimeType];
        const companyDir=join(root,p.companyId);
        const path=join(root,objectKey);
        await mkdir(companyDir,{recursive:true,mode:0o700});
        await writeFile(path,data,{flag:'wx',mode:0o600});
        try{
          const rows=await db.query(
            'INSERT INTO sst.evidence(company_id,inspection_id,non_conformity_id,object_key,'+
            'sha256,mime_type,size_bytes,kind,client_request_id,created_by) '+
            "VALUES($1,$2,$3,$4,$5,$6,$7,'foto',$8,$9) RETURNING "+returnFields,
            [p.companyId,inspectionId,ncId,objectKey,sha,payload.mimeType,data.length,key,p.userId],
          );
          return {item:rows.rows[0],replayed:false};
        }catch(error){
          try{await unlink(path);}catch{/* Registro falhou; nao ocultar erro original */}
          throw error;
        }
      });
    },
    list(principal,query={}){
      const root=requireStorage();
      void root;
      const inspectionId=query.inspectionId? id(query.inspectionId):null;
      const ncId=query.nonConformityId? id(query.nonConformityId):null;
      if(Number(Boolean(inspectionId))+Number(Boolean(ncId))!==1)throw new ApiError(400,'INVALID_LINK','Informe vistoria ou NC');
      return withTenant(pool,principal,async(db,p)=>{
        const rows=await db.query(
          'SELECT '+returnFields+' FROM sst.evidence WHERE company_id=$1 AND '+
          (inspectionId?'inspection_id=$2':'non_conformity_id=$2')+
          ' ORDER BY created_at,id LIMIT 100',[p.companyId,inspectionId||ncId],
        );
        const filtered=[];
        for(const row of rows.rows){
          try{await visible(db,p,row);filtered.push(row);}
          catch(e){if(e.code!=='NOT_FOUND')throw e;}
        }
        return filtered;
      });
    },
    download(principal,fileId){
      const root=requireStorage();
      return withTenant(pool,principal,async(db,p)=>{
        const result=await db.query(
          'SELECT '+returnFields+',object_key FROM sst.evidence WHERE company_id=$1 AND id=$2',
          [p.companyId,id(fileId)],
        );
        if(!result.rowCount)throw new ApiError(404,'NOT_FOUND','Arquivo indisponivel');
        const row=result.rows[0];
        await visible(db,p,row);
        if(!row.object_key.startsWith(p.companyId+'/')||
            !/^[0-9a-f-]{36}\.(jpg|png|webp)$/.test(row.object_key.slice(37))){
          throw new ApiError(503,'MEDIA_UNAVAILABLE','Caminho privado invalido');
        }
        const handle=await open(join(root,row.object_key),constants.O_RDONLY|constants.O_NOFOLLOW);
        let data;
        try {
          const stat=await handle.stat();
          if(!stat.isFile()||stat.size>MAX||stat.size!==Number(row.size_bytes)){
            throw new ApiError(503,'MEDIA_UNAVAILABLE','Arquivo incompleto');
          }
          data=await handle.readFile();
        }finally{await handle.close();}
        if(digest(data)!==row.sha256)throw new ApiError(503,'MEDIA_UNAVAILABLE','Integridade de foto nao validada');
        return {data,mimeType:row.mime_type};
      });
    },
  };
}
