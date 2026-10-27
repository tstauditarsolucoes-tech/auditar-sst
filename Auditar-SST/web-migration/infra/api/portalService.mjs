import {randomUUID} from 'node:crypto';
import {ApiError,withTenant} from './ncService.mjs';

const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const STAFF=['tecnico','gestor','adm'];
const MANAGERS=['gestor','adm'];
function checkId(id) {
  if(!UUID.test(id||''))throw new ApiError(400,'INVALID_ID','Identificador invalido');
  return id;
}
function requireRole(p,roles) {
  if(!roles.includes(p.role))throw new ApiError(403,'FORBIDDEN','Perfil sem permissao');
}
function value(input,max,field,optional=false) {
  if(typeof input!=='string') throw new ApiError(400,'INVALID_INPUT',field+' deve ser texto');
  const txt=input.replace(/\s+/g,' ').trim();
  if(txt.length>max||(!optional&&!txt))throw new ApiError(400,'INVALID_INPUT',field+' invalido');
  return txt;
}
async function threadAccess(db,p,id,lock=false) {
  const result=await db.query(
    'SELECT id,subject,status,created_by,created_at,updated_at FROM sst.support_thread WHERE company_id=$1 AND id=$2'+(lock?' FOR UPDATE':''),
    [p.companyId,checkId(id)],
  );
  if(!result.rowCount|| (p.role==='cliente'&&result.rows[0].created_by!==p.userId)){
    throw new ApiError(404,'NOT_FOUND','Solicitacao indisponivel');
  }
  return result.rows[0];
}

export function createPortalService(pool) {
  return {
    dashboard(principal) {
      return withTenant(pool,principal,async (db,p)=>{
        const [counts,pending,timeline]=await Promise.all([
          db.query('SELECT status,count(*)::integer AS total FROM sst.non_conformity WHERE company_id=$1 GROUP BY status',[p.companyId]),
          db.query(
            'SELECT id,short_title,description,probability,severity,status,updated_at FROM sst.non_conformity '+
            "WHERE company_id=$1 AND status <> 'validada' ORDER BY probability*severity DESC,updated_at DESC LIMIT 25",
            [p.companyId],
          ),
          db.query(
            'SELECT e.id,e.kind,e.message,e.created_at,n.id AS nc_id,n.short_title '+
            'FROM sst.nc_treatment_event e JOIN sst.non_conformity n ON n.id=e.non_conformity_id AND n.company_id=e.company_id '+
            'WHERE e.company_id=$1 ORDER BY e.created_at DESC,e.id DESC LIMIT 30',[p.companyId],
          ),
        ]);
        return {counts:counts.rows,pending:pending.rows,timeline:timeline.rows};
      });
    },
    threads(principal) {
      return withTenant(pool,principal,async (db,p)=>{
        const rows=await db.query(
          'SELECT id,subject,status,created_by,updated_at,created_at FROM sst.support_thread '+
          'WHERE company_id=$1 AND ($2::boolean=false OR created_by=$3) ORDER BY updated_at DESC,id DESC LIMIT 100',
          [p.companyId,p.role==='cliente',p.userId],
        );
        return rows.rows;
      });
    },
    createThread(principal,payload={}) {
      return withTenant(pool,principal,async (db,p)=>{
        const subject=value(payload.subject,160,'assunto');
        const message=value(payload.message,1500,'mensagem');
        const requestId=checkId(payload.clientRequestId);
        const rows=await db.query(
          'INSERT INTO sst.support_thread(company_id,subject,created_by,client_request_id) '+
          'VALUES($1,$2,$3,$4) ON CONFLICT(company_id,client_request_id) DO NOTHING '+
          'RETURNING id,subject,status,created_by,created_at,updated_at',
          [p.companyId,subject,p.userId,requestId],
        );
        if(rows.rowCount){
          const item=rows.rows[0];
          await db.query(
            'INSERT INTO sst.support_message(company_id,thread_id,message,client_request_id,created_by) '+
            'VALUES($1,$2,$3,$4,$5)',[p.companyId,item.id,message,randomUUID(),p.userId],
          );
          return item;
        }
        const previous=await db.query(
          'SELECT id,subject,status,created_by,created_at,updated_at FROM sst.support_thread '+
          'WHERE company_id=$1 AND client_request_id=$2',[p.companyId,requestId],
        );
        if(!previous.rowCount||previous.rows[0].created_by!==p.userId||previous.rows[0].subject!==subject){
          throw new ApiError(409,'REQUEST_CONFLICT','Identificador de solicitacao ja utilizado');
        }
        return previous.rows[0];
      });
    },
    thread(principal,id) {
      return withTenant(pool,principal,async (db,p)=>{
        const item=await threadAccess(db,p,id);
        const messages=await db.query(
          'SELECT id,kind,message,created_by,created_at FROM sst.support_message '+
          'WHERE company_id=$1 AND thread_id=$2 ORDER BY created_at,id',[p.companyId,id],
        );
        return {item,messages:messages.rows};
      });
    },
    reply(principal,id,payload={}) {
      return withTenant(pool,principal,async (db,p)=>{
        const thread=await threadAccess(db,p,id,true);
        const message=value(payload.message,1500,'mensagem');
        const key=checkId(payload.clientRequestId);
        const prior=await db.query(
          'SELECT id,thread_id,created_by,message FROM sst.support_message WHERE company_id=$1 AND client_request_id=$2',[p.companyId,key],
        );
        if(prior.rowCount){
          if(prior.rows[0].thread_id!==id||prior.rows[0].created_by!==p.userId||prior.rows[0].message!==message)throw new ApiError(409,'REQUEST_CONFLICT','Mensagem ja utilizada');
          return {id:prior.rows[0].id,replayed:true};
        }
        if(thread.status!=='aberta')throw new ApiError(409,'INVALID_STATE','Solicitacao encerrada');
        const result=await db.query(
          "INSERT INTO sst.support_message(company_id,thread_id,message,kind,client_request_id,created_by) "+
          "VALUES($1,$2,$3,'mensagem',$4,$5) RETURNING id",
          [p.companyId,id,message,key,p.userId],
        );
        await db.query('UPDATE sst.support_thread SET updated_at=now() WHERE company_id=$1 AND id=$2',[p.companyId,id]);
        return {id:result.rows[0].id,replayed:false};
      });
    },
    changeStatus(principal,id,action,payload={}) {
      return withTenant(pool,principal,async (db,p)=>{
        if(action!=='close'&&action!=='reopen')throw new ApiError(400,'INVALID_INPUT','Acao invalida');
        if(action==='close')requireRole(p,MANAGERS.concat('tecnico'));
        const thread=await threadAccess(db,p,id,true);
        const newStatus=action==='close'?'encerrada':'aberta';
        if(thread.status===newStatus)return {id,status:newStatus,replayed:true};
        const note=value(payload.message??'',1500,'mensagem',true)||
          (action==='close'?'Solicitacao encerrada pela equipe':'Solicitacao reaberta');
        await db.query(
          'INSERT INTO sst.support_message(company_id,thread_id,message,kind,client_request_id,created_by) '+
          'VALUES($1,$2,$3,$4,$5,$6)',
          [p.companyId,id,note,action==='close'?'encerramento':'reabertura',randomUUID(),p.userId],
        );
        await db.query('UPDATE sst.support_thread SET status=$3,updated_at=now() WHERE company_id=$1 AND id=$2',
          [p.companyId,id,newStatus]);
        return {id,status:newStatus,replayed:false};
      });
    },
    ping(principal) {
      return withTenant(pool,principal,async (db,p)=>{
        requireRole(p,STAFF);
        await db.query(
          'INSERT INTO sst.web_user_activity(company_id,user_id,last_seen) VALUES($1,$2,now()) '+
          'ON CONFLICT(company_id,user_id) DO UPDATE SET last_seen=now() '+
          "WHERE sst.web_user_activity.last_seen < now()-interval '45 seconds'",
          [p.companyId,p.userId],
        );
        return {ok:true};
      });
    },
    team(principal) {
      return withTenant(pool,principal,async (db,p)=>{
        requireRole(p,MANAGERS);
        const list=await db.query(
          'SELECT u.id,u.display_name,r.role,a.last_seen, '+
          "(a.last_seen IS NOT NULL AND a.last_seen>now()-interval '3 minutes') AS web_recent "+
          'FROM sst.user_company_role r JOIN sst.app_user u ON u.id=r.user_id '+
          'LEFT JOIN sst.web_user_activity a ON a.user_id=r.user_id AND a.company_id=r.company_id '+
          "WHERE r.company_id=$1 AND r.active AND u.active AND r.role IN ('tecnico','gestor','adm') "+
          'ORDER BY a.last_seen DESC NULLS LAST,u.display_name LIMIT 100',[p.companyId],
        );
        return list.rows;
      });
    },
    overview(principal) {
      return withTenant(pool,principal,async (db,p)=>{
        requireRole(p,MANAGERS);
        const result=await db.query(
          'SELECT '+
          "(SELECT count(*) FROM sst.non_conformity WHERE company_id=$1 AND status<>'validada')::integer AS nc_pendentes,"+
          "(SELECT count(*) FROM sst.inspection WHERE company_id=$1)::integer AS vistorias,"+
          "(SELECT count(*) FROM sst.task WHERE company_id=$1 AND status NOT IN ('concluida','cancelada'))::integer AS tarefas_abertas,"+
          "(SELECT count(*) FROM sst.support_thread WHERE company_id=$1 AND status='aberta')::integer AS apoio_aberto",
          [p.companyId],
        );
        return result.rows[0];
      });
    },
  };
}
