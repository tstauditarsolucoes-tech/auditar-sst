/**
 * Agenda SST: primeiro contrato isolado para homologacao.
 * Identidade da sessao e tenant sao injetados pelo backend, nunca do browser.
 */
import { ApiError, withTenant } from './ncService.mjs';
const UUID=/^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/i;
const PRIORITIES=new Set(['baixa','media','alta','critica']);
const STAFF=new Set(['adm','gestor','tecnico']);
const MANAGERS=new Set(['adm','gestor']);
function uuid(value,name) {
  if(typeof value!=='string'||!UUID.test(value)) {
    throw new ApiError(400,'INVALID_INPUT',name+' invalido');
  }
  return value.toLowerCase();
}
function field(value,max,label,allowEmpty=false) {
  if(allowEmpty&&(value===undefined||value===null))return '';
  if(typeof value!=='string')throw new ApiError(400,'INVALID_INPUT',label+' deve ser texto');
  const cleaned=value.replace(/\s+/g,' ').trim();
  if(cleaned.length>max||(!allowEmpty&&!cleaned)) {
    throw new ApiError(400,'INVALID_INPUT',label+' invalido');
  }
  return cleaned;
}
function requireStaff(p) {
  if(!STAFF.has(p.role))throw new ApiError(403,'FORBIDDEN','Agenda restrita a equipe');
}
function requireManager(p) {
  if(!MANAGERS.has(p.role))throw new ApiError(403,'FORBIDDEN','Somente gestao altera designacao');
}
function when(value) {
  if(value===null||value===undefined||value==='')return null;
  if(typeof value!=='string'||value.length>35||
      !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,3})?(?:Z|[+-]\d{2}:\d{2})$/.test(value)){
    throw new ApiError(400,'INVALID_INPUT','Prazo deve ter fuso e horario ISO');
  }
  const parsed=new Date(value);
  if(Number.isNaN(parsed.getTime()))throw new ApiError(400,'INVALID_INPUT','Prazo invalido');
  return parsed.toISOString();
}
function attributes(payload){
  if(!PRIORITIES.has(payload.priority)) {
    throw new ApiError(400,'INVALID_INPUT','Prioridade invalida');
  }
  return {
    title:field(payload.title,200,'Titulo'),
    description:field(payload.description,4000,'Descricao',true),
    priority:payload.priority,
    dueAt:when(payload.dueAt),
  };
}
async function checkAssignee(db,p,assignedTo){
  const active=await db.query(
    'SELECT r.user_id FROM sst.user_company_role r '+
    'JOIN sst.app_user u ON u.id=r.user_id '+
    'WHERE r.company_id=$1 AND r.user_id=$2 AND r.active=true AND u.active=true '+
    "AND r.role IN ('tecnico','gestor','adm')",
    [p.companyId,assignedTo],
  );
  if(!active.rowCount)throw new ApiError(400,'INVALID_ASSIGNEE','Tecnico nao vinculado a empresa');
}
async function event(db,p,id,kind,message=''){
  await db.query(
    'INSERT INTO sst.task_event (company_id,task_id,kind,message,created_by) '+
    'VALUES ($1,$2,$3,$4,$5)',
    [p.companyId,id,kind,message,p.userId],
  );
}
function access(p,row){
  if(p.role==='tecnico'&&row.assigned_to!==p.userId&&row.assigned_by!==p.userId) {
    throw new ApiError(404,'NOT_FOUND','Tarefa indisponivel');
  }
}
async function rowById(db,p,id,lock=false){
  const result=await db.query(
    'SELECT id,title,description,priority,status,assigned_to,assigned_by,due_at,'+
    'revision,created_at,updated_at,completed_at '+
    'FROM sst.task WHERE company_id=$1 AND id=$2 '+(lock?'FOR UPDATE':''),
    [p.companyId,id],
  );
  if(!result.rowCount)throw new ApiError(404,'NOT_FOUND','Tarefa indisponivel');
  access(p,result.rows[0]);
  return result.rows[0];
}
function equalsExisting(existing,data,assignedTo){
  if(existing.title!==data.title||existing.description!==data.description||
      existing.priority!==data.priority||existing.assigned_to!==assignedTo||
      (existing.due_at?new Date(existing.due_at).toISOString():null)!==data.dueAt){
    throw new ApiError(409,'IDEMPOTENCY_CONFLICT','Identificador ja utilizado com outra tarefa');
  }
}
export function createTaskService(pool){
  return {
    assignees(principal) {
      return withTenant(pool,principal,async(db,p)=>{
        requireManager(p);
        const result=await db.query(
          'SELECT r.user_id,r.role,u.display_name FROM sst.user_company_role r '+
          'JOIN sst.app_user u ON u.id=r.user_id '+
          'WHERE r.company_id=$1 AND r.active AND u.active '+
          "AND r.role IN ('tecnico','gestor','adm') ORDER BY u.display_name,r.user_id LIMIT 200",
          [p.companyId],
        );
        return result.rows;
      });
    },
    list(principal) {
      return withTenant(pool,principal,async(db,p)=>{
        requireStaff(p);
        const result=await db.query(
          'SELECT t.id,t.title,t.description,t.priority,t.status,t.assigned_to,'+
          't.assigned_by,t.due_at,t.revision,t.created_at,t.updated_at,t.completed_at,'+
          'u.display_name AS assigned_name FROM sst.task t '+
          'LEFT JOIN sst.app_user u ON u.id=t.assigned_to '+
          'WHERE t.company_id=$1 '+
          (p.role==='tecnico'?'AND (t.assigned_to=$2 OR t.assigned_by=$2) ':'')+
          'ORDER BY t.updated_at DESC,t.id DESC LIMIT 150',
          p.role==='tecnico'?[p.companyId,p.userId]:[p.companyId],
        );
        return result.rows;
      });
    },
    get(principal,id) {
      return withTenant(pool,principal,async(db,p)=>{
        requireStaff(p);
        const task=await rowById(db,p,uuid(id,'Tarefa'));
        const history=await db.query(
          'SELECT id,kind,message,created_by,created_at FROM sst.task_event '+
          'WHERE company_id=$1 AND task_id=$2 ORDER BY created_at,id',
          [p.companyId,task.id],
        );
        return {task,events:history.rows};
      });
    },
    create(principal,payload={}) {
      return withTenant(pool,principal,async(db,p)=>{
        requireStaff(p);
        const data=attributes(payload);
        const requestId=uuid(payload.clientRequestId,'Chave de envio');
        const assignedTo=payload.assignedTo?uuid(payload.assignedTo,'Tecnico designado'):p.userId;
        if(p.role==='tecnico'&&assignedTo!==p.userId) {
          throw new ApiError(403,'FORBIDDEN','Tecnico so pode criar tarefa para si');
        }
        await checkAssignee(db,p,assignedTo);
        const created=await db.query(
          'INSERT INTO sst.task '+
          '(company_id,title,description,priority,assigned_to,assigned_by,due_at,client_request_id) '+
          'VALUES ($1,$2,$3,$4,$5,$6,$7,$8) '+
          'ON CONFLICT (company_id,client_request_id) WHERE client_request_id IS NOT NULL '+
          'DO NOTHING RETURNING id,title,description,priority,assigned_to,due_at,status,revision',
          [p.companyId,data.title,data.description,data.priority,assignedTo,
            p.userId,data.dueAt,requestId],
        );
        if(created.rowCount) {
          await event(db,p,created.rows[0].id,'criada');
          return created.rows[0];
        }
        const original=await db.query(
          'SELECT id,title,description,priority,assigned_to,due_at,status,revision '+
          'FROM sst.task WHERE company_id=$1 AND client_request_id=$2',
          [p.companyId,requestId],
        );
        if(!original.rowCount)throw new ApiError(409,'IDEMPOTENCY_CONFLICT','Envio duplicado divergente');
        equalsExisting(original.rows[0],data,assignedTo);
        return original.rows[0];
      });
    },
    edit(principal,id,payload={}) {
      return withTenant(pool,principal,async(db,p)=>{
        requireManager(p);
        const task=await rowById(db,p,uuid(id,'Tarefa'),true);
        if(['concluida','cancelada'].includes(task.status)) {
          throw new ApiError(409,'INVALID_STATE','Tarefa fechada');
        }
        if(!Number.isInteger(payload.expectedRevision)||payload.expectedRevision!==task.revision) {
          throw new ApiError(409,'STALE_REVISION','Tarefa mudou em outro acesso');
        }
        const data=attributes(payload);
        const assignedTo=payload.assignedTo?uuid(payload.assignedTo,'Tecnico designado'):task.assigned_to;
        await checkAssignee(db,p,assignedTo);
        const updated=await db.query(
          'UPDATE sst.task SET title=$3,description=$4,priority=$5,due_at=$6,'+
          'assigned_to=$7,revision=revision+1,updated_at=now() '+
          'WHERE company_id=$1 AND id=$2 '+
          'RETURNING id,title,description,priority,assigned_to,due_at,status,revision',
          [p.companyId,task.id,data.title,data.description,data.priority,data.dueAt,assignedTo],
        );
        await event(db,p,task.id,'editada');
        return updated.rows[0];
      });
    },
    status(principal,id,payload={}) {
      return withTenant(pool,principal,async(db,p)=>{
        requireStaff(p);
        const task=await rowById(db,p,uuid(id,'Tarefa'),true);
        if(p.role==='tecnico'&&task.assigned_to!==p.userId) {
          throw new ApiError(403,'FORBIDDEN','Somente designado altera andamento');
        }
        const allowed={
          aberta:['em_andamento','concluida','cancelada'],
          em_andamento:['concluida','cancelada'],
          concluida:[],
          cancelada:[],
        };
        const next=payload.status;
        if(typeof next!=='string'||!allowed[task.status]?.includes(next)) {
          throw new ApiError(409,'INVALID_STATE','Transicao de tarefa nao permitida');
        }
        const message=field(payload.message,1200,'Comentario',true);
        if(next==='cancelada'&&!message) {
          throw new ApiError(400,'INVALID_INPUT','Cancelar exige motivo');
        }
        const updated=await db.query(
          'UPDATE sst.task SET status=$3::varchar,revision=revision+1,updated_at=now(),'+
          "completed_at=CASE WHEN $3::varchar='concluida' THEN now() ELSE completed_at END "+
          'WHERE company_id=$1 AND id=$2 RETURNING id,status,revision',
          [p.companyId,task.id,next],
        );
        await event(db,p,task.id,next,message);
        return updated.rows[0];
      });
    },
  };
}
