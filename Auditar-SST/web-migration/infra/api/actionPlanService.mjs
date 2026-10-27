/** Plano de Acao SST, piloto isolado em PostgreSQL de homologacao. */
import {createHash} from 'node:crypto';
import {ApiError,withTenant} from './ncService.mjs';

const UUID=/^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/i;
const STAFF=new Set(['adm','gestor','tecnico']);
const MANAGERS=new Set(['adm','gestor']);
const FLOW={
  aberta:['em_andamento','concluida','cancelada'],
  em_andamento:['concluida','cancelada'],
  concluida:[],
  cancelada:[],
};
function uuid(v,label) {
  if(typeof v!=='string'||!UUID.test(v))throw new ApiError(400,'INVALID_INPUT',label+' invalido');
  return v.toLowerCase();
}
function field(v,max,label,optional=false) {
  if(optional&&(v===undefined||v===null))return '';
  if(typeof v!=='string')throw new ApiError(400,'INVALID_INPUT',label+' invalido');
  const value=v.replace(/\s+/g,' ').trim();
  if(value.length>max||(!optional&&!value))throw new ApiError(400,'INVALID_INPUT',label+' invalido');
  return value;
}
function date(v) {
  if(v===null||v===undefined||v==='')return null;
  if(typeof v!=='string'||v.length>35||
     !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,3})?(?:Z|[+-]\d{2}:\d{2})$/.test(v)||
     !Number.isFinite(Date.parse(v))) {
    throw new ApiError(400,'INVALID_INPUT','Prazo ISO com fuso obrigatorio');
  }
  return new Date(v).toISOString();
}
function attributes(payload) {
  return {
    title:field(payload.title,180,'Titulo'),
    description:field(payload.description,4000,'Acao recomendada'),
    dueAt:date(payload.dueAt),
  };
}
function staff(p) {
  if(!STAFF.has(p.role))throw new ApiError(403,'FORBIDDEN','Plano interno da equipe');
}
function manager(p) {
  if(!MANAGERS.has(p.role))throw new ApiError(403,'FORBIDDEN','Somente gestao edita planos');
}
async function assignee(db,p,id) {
  const result=await db.query(
    'SELECT r.user_id FROM sst.user_company_role r '+
    'JOIN sst.app_user u ON u.id=r.user_id '+
    'WHERE r.company_id=$1 AND r.user_id=$2 AND r.active AND u.active '+
    "AND r.role IN ('adm','gestor','tecnico')",
    [p.companyId,id],
  );
  if(!result.rowCount)throw new ApiError(400,'INVALID_ASSIGNEE','Responsavel precisa ser membro ativo');
}
async function planRow(db,p,id,lock=false) {
  const result=await db.query(
    'SELECT id,company_id,non_conformity_id,title,description,assigned_to,created_by,'+
    'due_at,status,revision,created_at,updated_at,completed_at '+
    'FROM sst.action_plan WHERE company_id=$1 AND id=$2 '+(lock?'FOR UPDATE':''),
    [p.companyId,id],
  );
  if(!result.rowCount)throw new ApiError(404,'NOT_FOUND','Plano nao encontrado');
  const row=result.rows[0];
  if(p.role==='tecnico'&&row.assigned_to!==p.userId&&row.created_by!==p.userId) {
    throw new ApiError(404,'NOT_FOUND','Plano indisponivel');
  }
  return row;
}
async function event(db,p,planId,kind,message,revision,requestId=null) {
  await db.query(
    'INSERT INTO sst.action_plan_event '+
    '(company_id,action_plan_id,kind,message,resulting_revision,client_request_id,created_by) '+
    'VALUES ($1,$2,$3,$4,$5,$6,$7)',
    [p.companyId,planId,kind,message,revision,requestId,p.userId],
  );
}
function fingerprint(ncId,values,assignedTo) {
  return createHash('sha256').update(JSON.stringify([
    ncId,values.title,values.description,values.dueAt,assignedTo,
  ])).digest('hex');
}
export function createActionPlanService(pool) {
  return {
    list(principal,nonConformityId=null) {
      return withTenant(pool,principal,async(db,p)=>{
        staff(p);
        const id=nonConformityId?uuid(nonConformityId,'NC'):null;
        const params=[p.companyId];
        let where='WHERE a.company_id=$1 ';
        if(id){params.push(id);where+='AND a.non_conformity_id=$'+params.length+' ';}
        if(p.role==='tecnico'){
          params.push(p.userId);
          where+='AND (a.assigned_to=$'+params.length+' OR a.created_by=$'+params.length+') ';
        }
        const result=await db.query(
          'SELECT a.id,a.non_conformity_id,a.title,a.description,a.assigned_to,a.created_by,'+
          'a.due_at,a.status,a.revision,a.created_at,a.updated_at,a.completed_at,'+
          'u.display_name AS assigned_name,n.short_title AS nc_title '+
          'FROM sst.action_plan a JOIN sst.non_conformity n '+
          'ON n.company_id=a.company_id AND n.id=a.non_conformity_id '+
          'LEFT JOIN sst.app_user u ON u.id=a.assigned_to '+
          where+'ORDER BY a.updated_at DESC,a.id DESC LIMIT 150',
          params,
        );
        return result.rows;
      });
    },
    get(principal,id) {
      return withTenant(pool,principal,async(db,p)=>{
        staff(p);
        const plan=await planRow(db,p,uuid(id,'Plano'));
        const events=await db.query(
          'SELECT id,kind,message,created_by,created_at,resulting_revision '+
          'FROM sst.action_plan_event WHERE company_id=$1 AND action_plan_id=$2 '+
          'ORDER BY created_at,id',
          [p.companyId,plan.id],
        );
        return {plan,events:events.rows};
      });
    },
    create(principal,payload={}) {
      return withTenant(pool,principal,async(db,p)=>{
        staff(p);
        const ncId=uuid(payload.nonConformityId,'NC');
        const requestId=uuid(payload.clientRequestId,'Chave de envio');
        const data=attributes(payload);
        const assignedTo=payload.assignedTo?
          uuid(payload.assignedTo,'Responsavel'):p.userId;
        if(p.role==='tecnico'&&assignedTo!==p.userId){
          throw new ApiError(403,'FORBIDDEN','Tecnico so cria plano para si');
        }
        await assignee(db,p,assignedTo);
        const nc=await db.query(
          'SELECT id FROM sst.non_conformity WHERE company_id=$1 AND id=$2',
          [p.companyId,ncId],
        );
        if(!nc.rowCount)throw new ApiError(404,'NOT_FOUND','NC indisponivel');
        const hash=fingerprint(ncId,data,assignedTo);
        const created=await db.query(
          'INSERT INTO sst.action_plan '+
          '(company_id,non_conformity_id,title,description,assigned_to,created_by,'+
          'due_at,client_request_id,request_fingerprint) '+
          'VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9) '+
          'ON CONFLICT (company_id,client_request_id) DO NOTHING '+
          'RETURNING id,non_conformity_id,title,description,assigned_to,due_at,status,revision',
          [p.companyId,ncId,data.title,data.description,assignedTo,p.userId,
            data.dueAt,requestId,hash],
        );
        if(created.rowCount) {
          await event(db,p,created.rows[0].id,'criada','',1);
          return created.rows[0];
        }
        const existing=await db.query(
          'SELECT id,non_conformity_id,title,description,assigned_to,due_at,status,revision,'+
          'request_fingerprint FROM sst.action_plan WHERE company_id=$1 AND client_request_id=$2',
          [p.companyId,requestId],
        );
        if(!existing.rowCount||existing.rows[0].request_fingerprint!==hash){
          throw new ApiError(409,'IDEMPOTENCY_CONFLICT','Chave de envio usada por outro plano');
        }
        const {request_fingerprint:_ignored,...safe}=existing.rows[0];
        return safe;
      });
    },
    edit(principal,id,payload={}) {
      return withTenant(pool,principal,async(db,p)=>{
        manager(p);
        const current=await planRow(db,p,uuid(id,'Plano'),true);
        if(['concluida','cancelada'].includes(current.status)){
          throw new ApiError(409,'INVALID_STATE','Plano ja encerrado');
        }
        if(!Number.isSafeInteger(payload.expectedRevision)||
           payload.expectedRevision!==current.revision) {
          throw new ApiError(409,'STALE_REVISION','Plano alterado em outro acesso');
        }
        const data=attributes(payload);
        const assignedTo=payload.assignedTo?
          uuid(payload.assignedTo,'Responsavel'):current.assigned_to;
        await assignee(db,p,assignedTo);
        const updated=await db.query(
          'UPDATE sst.action_plan SET title=$3,description=$4,assigned_to=$5,due_at=$6,'+
          'revision=revision+1,updated_at=now() WHERE company_id=$1 AND id=$2 '+
          'RETURNING id,non_conformity_id,title,description,assigned_to,due_at,status,revision',
          [p.companyId,current.id,data.title,data.description,assignedTo,data.dueAt],
        );
        await event(db,p,current.id,'editada','',updated.rows[0].revision);
        return updated.rows[0];
      });
    },
    status(principal,id,payload={}) {
      return withTenant(pool,principal,async(db,p)=>{
        staff(p);
        const planId=uuid(id,'Plano');
        const requestId=uuid(payload.clientRequestId,'Chave de envio');
        const next=payload.status;
        if(typeof next!=='string'||!Object.hasOwn(FLOW,next)){
          throw new ApiError(400,'INVALID_INPUT','Status invalido');
        }
        const message=field(payload.message,1200,'Comentario',true);
        if(next==='cancelada'&&!message) {
          throw new ApiError(400,'INVALID_INPUT','Cancelamento exige motivo');
        }
        const previous=await db.query(
          'SELECT action_plan_id,kind,message,resulting_revision '+
          'FROM sst.action_plan_event WHERE company_id=$1 AND client_request_id=$2',
          [p.companyId,requestId],
        );
        if(previous.rowCount){
          const old=previous.rows[0];
          if(old.action_plan_id!==planId||old.kind!==next||old.message!==message){
            throw new ApiError(409,'IDEMPOTENCY_CONFLICT','Envio divergente');
          }
          await planRow(db,p,planId); // Revalida acesso mesmo em reenvio.
          return {id:planId,status:next,revision:old.resulting_revision,replayed:true};
        }
        const current=await planRow(db,p,planId,true);
        if(p.role==='tecnico'&&current.assigned_to!==p.userId){
          throw new ApiError(403,'FORBIDDEN','Somente responsavel ou gestor altera andamento');
        }
        if(!Number.isSafeInteger(payload.expectedRevision)||
           payload.expectedRevision!==current.revision) {
          throw new ApiError(409,'STALE_REVISION','Plano alterado em outro acesso');
        }
        if(!FLOW[current.status].includes(next)){
          throw new ApiError(409,'INVALID_STATE','Transicao nao permitida');
        }
        const updated=await db.query(
          'UPDATE sst.action_plan SET status=$3,revision=revision+1,updated_at=now(),'+
          "completed_at=CASE WHEN $3='concluida' THEN now() ELSE completed_at END "+
          'WHERE company_id=$1 AND id=$2 RETURNING id,status,revision',
          [p.companyId,planId,next],
        );
        await event(db,p,planId,next,message,updated.rows[0].revision,requestId);
        return updated.rows[0];
      });
    },
  };
}
