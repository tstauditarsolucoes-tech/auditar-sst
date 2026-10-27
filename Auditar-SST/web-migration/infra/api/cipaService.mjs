/** CIPA WEB: cadastro administrativo isolado de homologacao. Nao atesta cumprimento da NR-5. */
import {createHash} from 'node:crypto';
import {ApiError,withTenant} from './ncService.mjs';
const UUID=/^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/i;
const STAFF=new Set(['adm','gestor','tecnico']);
const MANAGERS=new Set(['adm','gestor']);
const REPRESENTATION=new Set(['empregados','empregador','designado']);
const SEATS=new Set(['titular','suplente','designado']);
function uuid(x,label){
  if(typeof x!=='string'||!UUID.test(x))throw new ApiError(400,'INVALID_INPUT',label+' invalido');
  return x.toLowerCase();
}
function field(x,max,label,optional=false){
  if(optional&&(x===null||x===undefined))return '';
  if(typeof x!=='string')throw new ApiError(400,'INVALID_INPUT',label+' invalido');
  const v=x.replace(/\s+/g,' ').trim();
  if(v.length>max||(!optional&&!v))throw new ApiError(400,'INVALID_INPUT',label+' invalido');
  return v;
}
function calendarDate(v,label){
  if(typeof v!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(v)||
     !Number.isFinite(Date.parse(v))||new Date(v).toISOString().slice(0,10)!==v)
    throw new ApiError(400,'INVALID_INPUT',label+' invalida');
  return v;
}
function optionalDate(v,label){return v===null||v===undefined||v===''?null:calendarDate(v,label);}
function moment(v){
  if(typeof v!=='string'||v.length>35||
    !/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,3})?(?:Z|[+-]\d\d:\d\d)$/.test(v)||
    !Number.isFinite(Date.parse(v)))
    throw new ApiError(400,'INVALID_INPUT','Horario ISO com fuso obrigatorio');
  return new Date(v).toISOString();
}
function fingerprint(data){return createHash('sha256').update(JSON.stringify(data)).digest('hex');}
function staff(p){if(!STAFF.has(p.role))throw new ApiError(403,'FORBIDDEN','CIPA restrita a equipe');}
function managers(p){if(!MANAGERS.has(p.role))throw new ApiError(403,'FORBIDDEN','Operacao reservada a gestao');}
function mandateData(payload){
  const start=calendarDate(payload.startsOn,'Inicio');
  const end=calendarDate(payload.endsOn,'Termino');
  if(end<start)throw new ApiError(400,'INVALID_INPUT','Termino anterior ao inicio');
  return {
    name:field(payload.name,180,'Identificacao'),
    startsOn:start,endsOn:end,electionOn:optionalDate(payload.electionOn,'Eleicao'),
  };
}
function memberData(payload){
  const representation=payload.representation;
  const seat=payload.seat;
  if(!REPRESENTATION.has(representation)||!SEATS.has(seat)||
     ((representation==='designado')!==(seat==='designado')))
    throw new ApiError(400,'INVALID_INPUT','Representacao ou cargo invalido');
  return {displayName:field(payload.displayName,180,'Identificacao'),
          representation,seat};
}
function meetingData(payload){
  return {title:field(payload.title,200,'Assunto'),scheduledAt:moment(payload.scheduledAt)};
}
async function loadMandate(db,p,id,lock=false){
  const x=await db.query(
    'SELECT id,name,starts_on,ends_on,election_on,status,revision,created_by,created_at,updated_at '+
    'FROM sst.cipa_mandate WHERE company_id=$1 AND id=$2 '+(lock?'FOR UPDATE':''),
    [p.companyId,id]);
  if(!x.rowCount)throw new ApiError(404,'NOT_FOUND','Mandato nao encontrado');
  return x.rows[0];
}
async function loadMeeting(db,p,id,lock=false){
  const x=await db.query(
    'SELECT id,mandate_id,title,scheduled_at,summary,status,revision,created_by,created_at,updated_at '+
    'FROM sst.cipa_meeting WHERE company_id=$1 AND id=$2 '+(lock?'FOR UPDATE':''),
    [p.companyId,id]);
  if(!x.rowCount)throw new ApiError(404,'NOT_FOUND','Reuniao nao encontrada');
  return x.rows[0];
}
async function event(db,p,mandateId,kind,message='',sourceId=null){
  await db.query(
    'INSERT INTO sst.cipa_event (company_id,mandate_id,kind,message,source_id,created_by) '+
    'VALUES ($1,$2,$3,$4,$5,$6)',
    [p.companyId,mandateId,kind,message,sourceId,p.userId]);
}
export function createCipaService(pool){
  return {
    list(principal){
      return withTenant(pool,principal,async(db,p)=>{
        staff(p);
        const q=await db.query(
          'SELECT id,name,starts_on,ends_on,election_on,status,revision,created_at,updated_at '+
          'FROM sst.cipa_mandate WHERE company_id=$1 '+
          'ORDER BY starts_on DESC,id DESC LIMIT 100',[p.companyId]);
        return q.rows;
      });
    },
    get(principal,id){
      return withTenant(pool,principal,async(db,p)=>{
        staff(p);
        const mandate=await loadMandate(db,p,uuid(id,'Mandato'));
        const members=await db.query(
          'SELECT id,display_name,representation,seat,created_at '+
          'FROM sst.cipa_member WHERE company_id=$1 AND mandate_id=$2 '+
          'ORDER BY created_at,id LIMIT 100',[p.companyId,mandate.id]);
        const meetings=await db.query(
          'SELECT id,title,scheduled_at,summary,status,revision,created_by,created_at '+
          'FROM sst.cipa_meeting WHERE company_id=$1 AND mandate_id=$2 '+
          'ORDER BY scheduled_at DESC,id DESC LIMIT 100',[p.companyId,mandate.id]);
        const events=await db.query(
          'SELECT id,kind,message,source_id,created_by,created_at '+
          'FROM sst.cipa_event WHERE company_id=$1 AND mandate_id=$2 '+
          'ORDER BY created_at,id LIMIT 300',[p.companyId,mandate.id]);
        return {mandate,members:members.rows,meetings:meetings.rows,events:events.rows};
      });
    },
    create(principal,payload={}){
      return withTenant(pool,principal,async(db,p)=>{
        staff(p);
        const data=mandateData(payload);
        const requestId=uuid(payload.clientRequestId,'Chave de envio');
        const hash=fingerprint([p.userId,data]);
        const created=await db.query(
          'INSERT INTO sst.cipa_mandate '+
          '(company_id,name,starts_on,ends_on,election_on,created_by,client_request_id,request_fingerprint) '+
          'VALUES ($1,$2,$3,$4,$5,$6,$7,$8) '+
          'ON CONFLICT (company_id,client_request_id) DO NOTHING '+
          'RETURNING id,name,starts_on,ends_on,election_on,status,revision',
          [p.companyId,data.name,data.startsOn,data.endsOn,data.electionOn,p.userId,requestId,hash]);
        if(created.rowCount){
          await event(db,p,created.rows[0].id,'mandato_criado');
          return created.rows[0];
        }
        const prior=await db.query(
          'SELECT id,name,starts_on,ends_on,election_on,status,revision,request_fingerprint '+
          'FROM sst.cipa_mandate WHERE company_id=$1 AND client_request_id=$2',
          [p.companyId,requestId]);
        if(!prior.rowCount||prior.rows[0].request_fingerprint!==hash)
          throw new ApiError(409,'IDEMPOTENCY_CONFLICT','Identificador de envio ja utilizado');
        const {request_fingerprint:_hash,...safe}=prior.rows[0];
        return safe;
      });
    },
    addMember(principal,mandateId,payload={}){
      return withTenant(pool,principal,async(db,p)=>{
        staff(p);
        const id=uuid(mandateId,'Mandato');
        const data=memberData(payload);
        const requestId=uuid(payload.clientRequestId,'Chave de envio');
        const hash=fingerprint([p.userId,id,data]);
        const mandate=await loadMandate(db,p,id,true);
        if(mandate.status==='encerrado')throw new ApiError(409,'INVALID_STATE','Mandato encerrado');
        const inserted=await db.query(
          'INSERT INTO sst.cipa_member '+
          '(company_id,mandate_id,display_name,representation,seat,created_by,client_request_id,request_fingerprint) '+
          'VALUES ($1,$2,$3,$4,$5,$6,$7,$8) '+
          'ON CONFLICT (company_id,client_request_id) DO NOTHING '+
          'RETURNING id,mandate_id,display_name,representation,seat',
          [p.companyId,id,data.displayName,data.representation,data.seat,p.userId,requestId,hash]);
        if(inserted.rowCount){
          await event(db,p,id,'membro_adicionado',data.representation+' / '+data.seat,inserted.rows[0].id);
          return inserted.rows[0];
        }
        const old=await db.query(
          'SELECT id,mandate_id,display_name,representation,seat,request_fingerprint '+
          'FROM sst.cipa_member WHERE company_id=$1 AND client_request_id=$2',
          [p.companyId,requestId]);
        if(!old.rowCount||old.rows[0].request_fingerprint!==hash)
          throw new ApiError(409,'IDEMPOTENCY_CONFLICT','Registro duplicado divergente');
        const {request_fingerprint:_hash,...safe}=old.rows[0];
        return safe;
      });
    },
    addMeeting(principal,mandateId,payload={}){
      return withTenant(pool,principal,async(db,p)=>{
        staff(p);
        const id=uuid(mandateId,'Mandato');
        const data=meetingData(payload);
        const requestId=uuid(payload.clientRequestId,'Chave de envio');
        const hash=fingerprint([p.userId,id,data]);
        const mandate=await loadMandate(db,p,id,true);
        if(mandate.status==='encerrado')throw new ApiError(409,'INVALID_STATE','Mandato encerrado');
        const inserted=await db.query(
          'INSERT INTO sst.cipa_meeting '+
          '(company_id,mandate_id,title,scheduled_at,created_by,client_request_id,request_fingerprint) '+
          'VALUES ($1,$2,$3,$4,$5,$6,$7) ON CONFLICT (company_id,client_request_id) DO NOTHING '+
          'RETURNING id,mandate_id,title,scheduled_at,summary,status,revision',
          [p.companyId,id,data.title,data.scheduledAt,p.userId,requestId,hash]);
        if(inserted.rowCount){
          await event(db,p,id,'reuniao_agendada',data.title,inserted.rows[0].id);
          return inserted.rows[0];
        }
        const old=await db.query(
          'SELECT id,mandate_id,title,scheduled_at,summary,status,revision,request_fingerprint '+
          'FROM sst.cipa_meeting WHERE company_id=$1 AND client_request_id=$2',
          [p.companyId,requestId]);
        if(!old.rowCount||old.rows[0].request_fingerprint!==hash)
          throw new ApiError(409,'IDEMPOTENCY_CONFLICT','Registro duplicado divergente');
        const {request_fingerprint:_hash,...safe}=old.rows[0];
        return safe;
      });
    },
    decideMeeting(principal,meetingId,payload={}){
      return withTenant(pool,principal,async(db,p)=>{
        staff(p);
        const id=uuid(meetingId,'Reuniao');
        const next=payload.status;
        if(!['realizada','cancelada'].includes(next))
          throw new ApiError(400,'INVALID_INPUT','Situacao invalida');
        const summary=field(payload.summary,4000,'Resumo',true);
        if(!summary)throw new ApiError(400,'INVALID_INPUT','Resumo ou motivo obrigatorio');
        const meeting=await loadMeeting(db,p,id,true);
        if(!MANAGERS.has(p.role)&&meeting.created_by!==p.userId)
          throw new ApiError(403,'FORBIDDEN','Somente o criador ou a gestao');
        if(meeting.status!=='planejada')
          throw new ApiError(409,'INVALID_STATE','Reuniao ja encerrada');
        if(!Number.isSafeInteger(payload.expectedRevision)||payload.expectedRevision!==meeting.revision)
          throw new ApiError(409,'STALE_REVISION','Reuniao mudou em outro acesso');
        const mandate=await loadMandate(db,p,meeting.mandate_id);
        if(mandate.status==='encerrado')
          throw new ApiError(409,'INVALID_STATE','Mandato encerrado');
        const updated=await db.query(
          'UPDATE sst.cipa_meeting SET status=$3::varchar,summary=$4,revision=revision+1,'+
          'updated_at=now() WHERE company_id=$1 AND id=$2 '+
          'RETURNING id,status,revision',
          [p.companyId,id,next,summary]);
        await event(db,p,meeting.mandate_id,next==='realizada'?'reuniao_realizada':'reuniao_cancelada',
          summary.slice(0,1200),id);
        return updated.rows[0];
      });
    },
    mandateStatus(principal,mandateId,payload={}){
      return withTenant(pool,principal,async(db,p)=>{
        managers(p);
        const id=uuid(mandateId,'Mandato');
        const current=await loadMandate(db,p,id,true);
        if(!Number.isSafeInteger(payload.expectedRevision)||payload.expectedRevision!==current.revision)
          throw new ApiError(409,'STALE_REVISION','Mandato mudou em outro acesso');
        const next=payload.status;
        if((next!=='ativo'||current.status!=='preparacao')&&
           (next!=='encerrado'||current.status!=='ativo'))
          throw new ApiError(409,'INVALID_STATE','Mudanca de status nao permitida');
        const note=field(payload.note,1200,'Observacao',true);
        if(next==='encerrado'&&!note)
          throw new ApiError(400,'INVALID_INPUT','Encerramento exige motivo');
        const updated=await db.query(
          'UPDATE sst.cipa_mandate SET status=$3::varchar,revision=revision+1,'+
          'updated_at=now() WHERE company_id=$1 AND id=$2 RETURNING id,status,revision',
          [p.companyId,id,next]);
        await event(db,p,id,next==='ativo'?'mandato_ativo':'mandato_encerrado',note);
        return updated.rows[0];
      });
    },
  };
}
