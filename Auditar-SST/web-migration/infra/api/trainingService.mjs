/** Treinamentos, DDS e Integracao: piloto isolado sem certificados nem dados do legado. */
import {createHash} from 'node:crypto';
import {ApiError,withTenant} from './ncService.mjs';
const UUID=/^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/i;
const KINDS=new Set(['treinamento','dds','integracao']);
const STAFF=new Set(['adm','gestor','tecnico']);
const MANAGERS=new Set(['adm','gestor']);
function uuid(v,name){
  if(typeof v!=='string'||!UUID.test(v))throw new ApiError(400,'INVALID_INPUT',name+' invalido');
  return v.toLowerCase();
}
function text(v,max,name,optional=false){
  if(optional&&(v===null||v===undefined))return '';
  if(typeof v!=='string')throw new ApiError(400,'INVALID_INPUT',name+' invalido');
  const val=v.replace(/\s+/g,' ').trim();
  if(val.length>max||(!optional&&!val))throw new ApiError(400,'INVALID_INPUT',name+' invalido');
  return val;
}
function when(v){
  if(v===null||v===undefined||v==='')return null;
  if(typeof v!=='string'||v.length>35||
    !/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,3})?(?:Z|[+-]\d\d:\d\d)$/.test(v)||
    !Number.isFinite(Date.parse(v)))throw new ApiError(400,'INVALID_INPUT','Data ISO e fuso obrigatorios');
  return new Date(v).toISOString();
}
function count(v,max,name,min=0){
  if(v===null||v===undefined||v==='')return null;
  if(!Number.isInteger(v)||v<min||v>max)throw new ApiError(400,'INVALID_INPUT',name+' invalido');
  return v;
}
function attributes(payload){
  if(!KINDS.has(payload.kind))throw new ApiError(400,'INVALID_INPUT','Tipo de atividade invalido');
  return {
    kind:payload.kind,
    title:text(payload.title,200,'Titulo'),
    sector:text(payload.sector,180,'Setor',true),
    nrReference:text(payload.nrReference,100,'Referencia NR',true),
    instructor:text(payload.instructor,180,'Instrutor',true),
    plannedAt:when(payload.plannedAt),
    durationMinutes:count(payload.durationMinutes,1440,'Duracao',1),
    participantsCount:count(payload.participantsCount,10000,'Quantidade de participantes'),
  };
}
function requireStaff(p){
  if(!STAFF.has(p.role))throw new ApiError(403,'FORBIDDEN','Area interna da equipe');
}
function canManage(p,row){
  if(!MANAGERS.has(p.role)&&row.created_by!==p.userId)
    throw new ApiError(403,'FORBIDDEN','Somente o criador ou a gestao');
}
function fingerprint(data){return createHash('sha256').update(JSON.stringify(Object.values(data))).digest('hex');}
async function row(db,p,id,lock=false){
  const r=await db.query(
    'SELECT id,company_id,kind,title,sector,nr_reference,instructor,planned_at,'+
    'duration_minutes,participants_count,status,revision,created_by,created_at,updated_at,completed_at '+
    'FROM sst.training_session WHERE company_id=$1 AND id=$2 '+(lock?'FOR UPDATE':''),
    [p.companyId,id]);
  if(!r.rowCount)throw new ApiError(404,'NOT_FOUND','Atividade indisponivel');
  return r.rows[0];
}
async function log(db,p,id,kind,message,revision,requestId=null){
  await db.query(
    'INSERT INTO sst.training_event '+
    '(company_id,training_id,kind,message,resulting_revision,client_request_id,created_by) '+
    'VALUES ($1,$2,$3,$4,$5,$6,$7)',
    [p.companyId,id,kind,message,revision,requestId,p.userId]);
}
export function createTrainingService(pool){
  return {
    list(principal,kind=null){
      return withTenant(pool,principal,async(db,p)=>{
        requireStaff(p);
        if(kind!==null&&!KINDS.has(kind))throw new ApiError(400,'INVALID_INPUT','Filtro invalido');
        const args=[p.companyId];
        if(kind)args.push(kind);
        const r=await db.query(
          'SELECT id,kind,title,sector,nr_reference,instructor,planned_at,duration_minutes,'+
          'participants_count,status,revision,created_by,created_at,updated_at,completed_at '+
          'FROM sst.training_session WHERE company_id=$1 '+
          (kind?'AND kind=$2 ':'')+
          'ORDER BY updated_at DESC,id DESC LIMIT 150',args);
        return r.rows;
      });
    },
    get(principal,id){
      return withTenant(pool,principal,async(db,p)=>{
        requireStaff(p);
        const training=await row(db,p,uuid(id,'Atividade'));
        const events=await db.query(
          'SELECT id,kind,message,resulting_revision,created_by,created_at '+
          'FROM sst.training_event WHERE company_id=$1 AND training_id=$2 '+
          'ORDER BY created_at,id',[p.companyId,training.id]);
        const attendance=await db.query(
          'SELECT id,display_name,presence,note,created_at FROM sst.training_attendance '+
          'WHERE company_id=$1 AND training_id=$2 ORDER BY created_at,id LIMIT 100',
          [p.companyId,training.id]);
        return {training,events:events.rows,attendance:attendance.rows};
      });
    },
    create(principal,payload={}){
      return withTenant(pool,principal,async(db,p)=>{
        requireStaff(p);
        const a=attributes(payload);
        const requestId=uuid(payload.clientRequestId,'Chave de envio');
        const hash=fingerprint(a);
        const inserted=await db.query(
          'INSERT INTO sst.training_session '+
          '(company_id,kind,title,sector,nr_reference,instructor,planned_at,'+
          'duration_minutes,participants_count,created_by,client_request_id,request_fingerprint) '+
          'VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12) '+
          'ON CONFLICT (company_id,client_request_id) DO NOTHING '+
          'RETURNING id,kind,title,sector,nr_reference,instructor,planned_at,duration_minutes,'+
          'participants_count,status,revision',
          [p.companyId,a.kind,a.title,a.sector,a.nrReference,a.instructor,a.plannedAt,
            a.durationMinutes,a.participantsCount,p.userId,requestId,hash]);
        if(inserted.rowCount){
          await log(db,p,inserted.rows[0].id,'criada','',1);
          return inserted.rows[0];
        }
        const existing=await db.query(
          'SELECT id,kind,title,sector,nr_reference,instructor,planned_at,duration_minutes,'+
          'participants_count,status,revision,request_fingerprint '+
          'FROM sst.training_session WHERE company_id=$1 AND client_request_id=$2',
          [p.companyId,requestId]);
        if(!existing.rowCount||existing.rows[0].request_fingerprint!==hash)
          throw new ApiError(409,'IDEMPOTENCY_CONFLICT','Chave de envio reutilizada');
        const {request_fingerprint:_discard,...result}=existing.rows[0];
        return result;
      });
    },
    addParticipant(principal,id,payload={}){
      return withTenant(pool,principal,async(db,p)=>{
        requireStaff(p);
        const trainingId=uuid(id,'Treinamento');
        const requestId=uuid(payload.clientRequestId,'Chave de envio');
        const name=text(payload.displayName,180,'Nome ficticio');
        const presence=payload.presence||'nao_confirmada';
        if(!['declarada','nao_confirmada'].includes(presence))
          throw new ApiError(400,'INVALID_INPUT','Marcacao de presenca invalida');
        const note=text(payload.note,500,'Observacao',true);
        const hash=createHash('sha256').update(JSON.stringify([
          trainingId,p.userId,name,presence,note,
        ])).digest('hex');
        const activity=await row(db,p,trainingId,true);
        canManage(p,activity);
        const original=await db.query(
          'SELECT id,training_id,display_name,presence,note,request_fingerprint '+
          'FROM sst.training_attendance WHERE company_id=$1 AND client_request_id=$2',
          [p.companyId,requestId]);
        if(original.rowCount){
          if(original.rows[0].request_fingerprint!==hash)
            throw new ApiError(409,'IDEMPOTENCY_CONFLICT','Registro enviado com outros dados');
          const {request_fingerprint:_omit,...safe}=original.rows[0];
          return safe;
        }
        const size=await db.query(
          'SELECT count(*)::integer AS n FROM sst.training_attendance '+
          'WHERE company_id=$1 AND training_id=$2',[p.companyId,trainingId]);
        if(size.rows[0].n>=100)throw new ApiError(413,'ATTENDANCE_LIMIT',
          'Lista de teste limitada a 100 registros');
        const inserted=await db.query(
          'INSERT INTO sst.training_attendance '+
          '(company_id,training_id,display_name,presence,note,created_by,client_request_id,request_fingerprint) '+
          'VALUES($1,$2,$3,$4,$5,$6,$7,$8) '+
          'RETURNING id,training_id,display_name,presence,note,created_at',
          [p.companyId,trainingId,name,presence,note,p.userId,requestId,hash]);
        return inserted.rows[0];
      });
    },
    edit(principal,id,payload={}){
      return withTenant(pool,principal,async(db,p)=>{
        requireStaff(p);
        const current=await row(db,p,uuid(id,'Atividade'),true);
        canManage(p,current);
        if(current.status!=='planejado')throw new ApiError(409,'INVALID_STATE','Atividade encerrada');
        if(!Number.isSafeInteger(payload.expectedRevision)||payload.expectedRevision!==current.revision)
          throw new ApiError(409,'STALE_REVISION','Dados alterados em outra tela');
        const a=attributes({...payload,kind:current.kind});
        const r=await db.query(
          'UPDATE sst.training_session SET title=$3,sector=$4,nr_reference=$5,instructor=$6,'+
          'planned_at=$7,duration_minutes=$8,participants_count=$9,revision=revision+1,'+
          'updated_at=now() WHERE company_id=$1 AND id=$2 '+
          'RETURNING id,kind,title,sector,nr_reference,instructor,planned_at,duration_minutes,'+
          'participants_count,status,revision',
          [p.companyId,current.id,a.title,a.sector,a.nrReference,a.instructor,a.plannedAt,
           a.durationMinutes,a.participantsCount]);
        await log(db,p,current.id,'editada','',r.rows[0].revision);
        return r.rows[0];
      });
    },
    status(principal,id,payload={}){
      return withTenant(pool,principal,async(db,p)=>{
        requireStaff(p);
        const activityId=uuid(id,'Atividade');
        const requestId=uuid(payload.clientRequestId,'Chave de envio');
        const next=payload.status;
        if(!['realizado','cancelado'].includes(next))
          throw new ApiError(400,'INVALID_INPUT','Status invalido');
        const message=text(payload.message,1200,'Observacao',true);
        if(next==='cancelado'&&!message)
          throw new ApiError(400,'INVALID_INPUT','Cancelamento exige motivo');
        const current=await row(db,p,activityId,true);
        canManage(p,current);
        const prior=await db.query(
          'SELECT training_id,kind,message,resulting_revision FROM sst.training_event '+
          'WHERE company_id=$1 AND client_request_id=$2',[p.companyId,requestId]);
        if(prior.rowCount){
          const old=prior.rows[0];
          if(old.training_id!==activityId||old.kind!==next||old.message!==message)
            throw new ApiError(409,'IDEMPOTENCY_CONFLICT','Reenvio divergente');
          return {id:activityId,status:next,revision:old.resulting_revision,replayed:true};
        }
        if(current.status!=='planejado')
          throw new ApiError(409,'INVALID_STATE','Atividade ja encerrada');
        if(!Number.isSafeInteger(payload.expectedRevision)||payload.expectedRevision!==current.revision)
          throw new ApiError(409,'STALE_REVISION','Atividade alterada em outra tela');
        if(next==='realizado'&&(current.duration_minutes===null||current.participants_count===null))
          throw new ApiError(400,'INCOMPLETE_ACTIVITY','Informe duracao e quantidade de participantes antes de concluir');
        const updated=await db.query(
          'UPDATE sst.training_session SET status=$3::varchar,revision=revision+1,updated_at=now(),'+
          "completed_at=CASE WHEN $3::varchar='realizado' THEN now() ELSE completed_at END "+
          'WHERE company_id=$1 AND id=$2 RETURNING id,status,revision',
          [p.companyId,activityId,next]);
        await log(db,p,activityId,next,message,updated.rows[0].revision,requestId);
        return updated.rows[0];
      });
    },
  };
}
