/** Isolated member portal. Never accepts client-supplied identity/company/role. */
import {createHash} from 'node:crypto';
import {ApiError,withTenant,assertPrincipal} from './ncService.mjs';
import {hashPassword} from './authService.mjs';
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
export function portalId(v){if(typeof v!=='string'||!UUID.test(v))throw new ApiError(400,'INVALID_INPUT','Identificador invalido');return v.toLowerCase();}
export function portalText(v,max=2000){if(typeof v!=='string'||!v.trim()||v.trim().length>max)throw new ApiError(400,'INVALID_INPUT','Preencha o texto dentro do limite');return v.trim();}
function manager(p){assertPrincipal(p);if(!['adm','gestor'].includes(p.role))throw new ApiError(403,'FORBIDDEN','Operacao exclusiva da gestao');}
function staff(p){assertPrincipal(p);if(!['adm','gestor','tecnico'].includes(p.role))throw new ApiError(403,'FORBIDDEN','Operacao exclusiva da equipe');}
function member(p){if(p?.portal!=='cipa'||!UUID.test(p.companyId||'')||!UUID.test(p.accountId||''))throw new ApiError(401,'UNAUTHENTICATED','Acesso individual necessario');
  if(p.mustChangePassword!==false)throw new ApiError(403,'PASSWORD_CHANGE_REQUIRED','Troque a senha temporaria antes de continuar');}
function hash(data){return createHash('sha256').update(JSON.stringify(data)).digest('hex');}
function date(v){if(typeof v!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(v)||!Number.isFinite(Date.parse(v))||new Date(v).toISOString().slice(0,10)!==v)throw new ApiError(400,'INVALID_INPUT','Prazo invalido');return v;}
export function nextPortalStatus(current,next,isStaff){
  const allowed=isStaff?{aguardando_validacao:['concluida','andamento'],concluida:['andamento']}:
    {aberta:['andamento','aguardando_validacao'],andamento:['aguardando_validacao'],aguardando_validacao:['andamento']};
  if(!allowed[current]?.includes(next))throw new ApiError(409,'INVALID_STATE','Transicao nao permitida; atualize a tela');
  return next;
}
export async function withCipaMember(pool,p,fn){
  member(p);if(!pool)throw new ApiError(503,'DATABASE_UNAVAILABLE','Banco indisponivel');
  const db=await pool.connect();
  try{await db.query('BEGIN');await db.query('SET LOCAL ROLE sst_cipa_runtime');
    await db.query("SELECT set_config('app.company_id',$1,true),set_config('app.cipa_account_id',$2,true)",[p.companyId,p.accountId]);
    const r=await fn(db,p);await db.query('COMMIT');return r;
  }catch(e){await db.query('ROLLBACK').catch(()=>{});throw e;}finally{db.release();}
}
async function mandate(db,p,id,writing=false){
  const row=(await db.query('SELECT id,name,status,starts_on,ends_on FROM sst.cipa_mandate WHERE company_id=$1 AND id=$2',[p.companyId,portalId(id)])).rows[0];
  if(!row)throw new ApiError(404,'NOT_FOUND','Mandato nao encontrado');
  if(writing&&row.status==='encerrado')throw new ApiError(409,'CLOSED_MANDATE','Mandato encerrado: consulta somente');
  return row;
}
async function entry(db,p,data,requestId){
  const payload=[p.accountId||p.userId,data];const fingerprint=hash(payload);
  const q=await db.query('INSERT INTO sst.cipa_portal_entry(company_id,mandate_id,action_id,meeting_id,author_account_id,author_staff_id,kind,message,client_request_id,request_fingerprint) '+
    'VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10) ON CONFLICT(company_id,client_request_id) DO NOTHING RETURNING id,kind,message,created_at',
    [p.companyId,data.mandateId,data.actionId||null,data.meetingId||null,p.accountId||null,p.userId||null,data.kind,data.message,portalId(requestId),fingerprint]);
  if(q.rowCount)return q.rows[0];
  const old=(await db.query('SELECT id,kind,message,created_at,request_fingerprint FROM sst.cipa_portal_entry WHERE company_id=$1 AND client_request_id=$2',[p.companyId,requestId])).rows[0];
  if(!old||old.request_fingerprint!==fingerprint)throw new ApiError(409,'IDEMPOTENCY_CONFLICT','Chave de envio ja utilizada');
  const {request_fingerprint:_,...safe}=old;return safe;
}
async function workspace(db,p,id,isStaff){
  const m=await mandate(db,p,id);
  const actions=await db.query('SELECT id,mandate_id,assigned_to,title,description,due_on,priority,status,revision,updated_at FROM sst.cipa_portal_action WHERE company_id=$1 AND mandate_id=$2 ORDER BY due_on,id LIMIT 200',[p.companyId,m.id]);
  const meetings=await db.query('SELECT id,title,scheduled_at,summary,status FROM sst.cipa_meeting WHERE company_id=$1 AND mandate_id=$2 ORDER BY scheduled_at DESC,id LIMIT 100',[p.companyId,m.id]);
  const entries=await db.query('SELECT id,kind,message,action_id,meeting_id,author_account_id,created_at FROM sst.cipa_portal_entry WHERE company_id=$1 AND mandate_id=$2 ORDER BY created_at DESC,id LIMIT 300',[p.companyId,m.id]);
  const photos=(await db.query('SELECT id,entry_id,author_account_id,mime_type,created_at FROM sst.cipa_portal_photo WHERE company_id=$1 AND mandate_id=$2 ORDER BY created_at DESC,id DESC LIMIT 100',[p.companyId,m.id])).rows;
  const counts=(await db.query("SELECT count(*) FILTER (WHERE status<>'concluida')::integer AS pending, count(*) FILTER (WHERE status='aguardando_validacao')::integer AS reviewing FROM sst.cipa_portal_action WHERE company_id=$1 AND mandate_id=$2",[p.companyId,m.id])).rows[0];
  const scheduled=(await db.query("SELECT count(*)::integer AS count FROM sst.cipa_meeting WHERE company_id=$1 AND mandate_id=$2 AND status='planejada'",[p.companyId,m.id])).rows[0].count;
  // Per-member monthly progress is event-sourced and not clipped by the general history limit.
  const checklist=isStaff?[]:(await db.query(
    "SELECT DISTINCT ON (split_part(message,'|',1),split_part(message,'|',2)) message,created_at " +
    "FROM sst.cipa_portal_entry WHERE company_id=$1 AND mandate_id=$2 AND author_account_id=$3 AND kind='checklist' " +
    "ORDER BY split_part(message,'|',1) DESC,split_part(message,'|',2),created_at DESC,id DESC LIMIT 48",
    [p.companyId,m.id,p.accountId])).rows;
  const result={mandate:m,actions:actions.rows,meetings:meetings.rows,entries:entries.rows,photos,checklist,counts:{...counts,scheduled},limits:{actions:200,meetings:100,entries:300}};
  if(isStaff){
    result.accounts=(await db.query('SELECT a.id,a.display_name,a.email,a.active,a.must_change_password,g.member_id,g.active AS grant_active FROM sst.cipa_portal_grant g JOIN sst.cipa_portal_account a ON a.company_id=g.company_id AND a.id=g.account_id WHERE g.company_id=$1 AND g.mandate_id=$2 ORDER BY a.display_name,a.id',[p.companyId,m.id])).rows;
    result.members=(await db.query('SELECT id,display_name FROM sst.cipa_member WHERE company_id=$1 AND mandate_id=$2 ORDER BY display_name,id',[p.companyId,m.id])).rows;
  }
  return result;
}
export function createCipaPortalService(pool){return {
  monthlySummary(p,id,period){
    staff(p);portalId(id);
    if(typeof period!=='string'||!/^\d{4}-(0[1-9]|1[0-2])$/.test(period))throw new ApiError(400,'INVALID_INPUT','Competencia mensal invalida');
    return withTenant(pool,p,async db=>{
      const m=await mandate(db,p,id);
      const actions=(await db.query("SELECT count(*)::integer AS total, " +
        "count(*) FILTER (WHERE status<>'concluida')::integer AS pending, " +
        "count(*) FILTER (WHERE status='aguardando_validacao')::integer AS reviewing, " +
        "count(*) FILTER (WHERE status='concluida')::integer AS done, " +
        "count(*) FILTER (WHERE status<>'concluida' AND due_on<(now() AT TIME ZONE 'America/Fortaleza')::date)::integer AS overdue " +
        "FROM sst.cipa_portal_action WHERE company_id=$1 AND mandate_id=$2",[p.companyId,m.id])).rows[0];
      const meetings=(await db.query("SELECT status,count(*)::integer AS total FROM sst.cipa_meeting " +
        "WHERE company_id=$1 AND mandate_id=$2 AND to_char(scheduled_at AT TIME ZONE 'America/Fortaleza','YYYY-MM')=$3 " +
        "GROUP BY status",[p.companyId,m.id,period])).rows;
      const participation=(await db.query("SELECT kind,count(*)::integer AS total FROM sst.cipa_portal_entry " +
        "WHERE company_id=$1 AND mandate_id=$2 AND to_char(created_at AT TIME ZONE 'America/Fortaleza','YYYY-MM')=$3 " +
        "GROUP BY kind",[p.companyId,m.id,period])).rows;
      // Last declared state per task, per member, per month, without using the 300-entry display limit.
      const checklists=(await db.query(
        "WITH latest AS (SELECT DISTINCT ON (author_account_id,split_part(message,'|',2)) " +
        "author_account_id,split_part(message,'|',3) AS state FROM sst.cipa_portal_entry " +
        "WHERE company_id=$1 AND mandate_id=$2 AND kind='checklist' AND split_part(message,'|',1)=$3 " +
        "ORDER BY author_account_id,split_part(message,'|',2),created_at DESC,id DESC) " +
        "SELECT g.account_id,a.display_name,count(latest.state) FILTER (WHERE latest.state='feito')::integer AS completed " +
        "FROM sst.cipa_portal_grant g JOIN sst.cipa_portal_account a ON a.company_id=g.company_id AND a.id=g.account_id " +
        "LEFT JOIN latest ON latest.author_account_id=g.account_id " +
        "WHERE g.company_id=$1 AND g.mandate_id=$2 AND g.active GROUP BY g.account_id,a.display_name " +
        "ORDER BY a.display_name,g.account_id LIMIT 200",
        [p.companyId,m.id,period])).rows;
      const members=(await db.query('SELECT count(*)::integer AS total FROM sst.cipa_portal_grant WHERE company_id=$1 AND mandate_id=$2 AND active',[p.companyId,m.id])).rows[0].total;
      return {mandate:{id:m.id,name:m.name,status:m.status},period,actions,meetings,participation,checklists,activeMembers:members,
        note:'Acoes refletem situacao atual do mandato; reunioes e eventos referem-se a competencia informada. Ciencia de convocacao nao comprova presenca nem assinatura.'};
    });
  },
  mandates(p){return withCipaMember(pool,p,async db=>(await db.query('SELECT id,name,status,starts_on,ends_on FROM sst.cipa_mandate WHERE company_id=$1 ORDER BY starts_on DESC,id LIMIT 100',[p.companyId])).rows);},
  get(p,id){return withCipaMember(pool,p,db=>workspace(db,p,id,false));},
  adminGet(p,id){staff(p);return withTenant(pool,p,db=>workspace(db,p,id,true));},
  accounts(p){manager(p);return withTenant(pool,p,async db=>(await db.query('SELECT id,display_name,email,active FROM sst.cipa_portal_account WHERE company_id=$1 ORDER BY display_name,id LIMIT 200',[p.companyId])).rows);},
  async createAccount(p,id,b={}){
    manager(p);portalId(id);const displayName=portalText(b.displayName,180),email=portalText(b.email,254).toLowerCase();
    if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email))throw new ApiError(400,'INVALID_INPUT','Email invalido');
    const memberId=portalId(b.memberId);const requestId=portalId(b.clientRequestId);const verifier=await hashPassword(b.password);
    return withTenant(pool,p,async db=>{
      await mandate(db,p,id,true);
      const m=await db.query('SELECT 1 FROM sst.cipa_member WHERE company_id=$1 AND mandate_id=$2 AND id=$3',[p.companyId,id,memberId]);
      if(!m.rowCount)throw new ApiError(404,'NOT_FOUND','Membro nao encontrado neste mandato');
      const q=await db.query('INSERT INTO sst.cipa_portal_account(company_id,display_name,email,password_verifier,created_by) VALUES($1,$2,$3,$4,$5) ON CONFLICT(company_id,email) DO NOTHING RETURNING id,display_name,email,active,must_change_password',[p.companyId,displayName,email,verifier,p.userId]);
      if(!q.rowCount)throw new ApiError(409,'ACCOUNT_EXISTS','Conta ja existente. Vincule a conta, sem substituir sua senha');
      const a=q.rows[0];
      const grant=await db.query('INSERT INTO sst.cipa_portal_grant(company_id,mandate_id,account_id,member_id) VALUES($1,$2,$3,$4) ON CONFLICT DO NOTHING RETURNING account_id',[p.companyId,id,a.id,memberId]);
      if(!grant.rowCount)throw new ApiError(409,'LINK_CONFLICT','Membro ja possui uma conta vinculada');
      await entry(db,p,{mandateId:id,kind:'acesso',message:'Acesso individual criado para '+displayName},requestId);
      return a;
    });
  },
  link(p,id,b={}){manager(p);return withTenant(pool,p,async db=>{
    await mandate(db,p,id,true);const accountId=portalId(b.accountId),memberId=portalId(b.memberId);
    const a=(await db.query('SELECT id,display_name FROM sst.cipa_portal_account WHERE company_id=$1 AND id=$2 AND active FOR UPDATE',[p.companyId,accountId])).rows[0];
    if(!a)throw new ApiError(404,'NOT_FOUND','Conta ativa nao encontrada');
    const m=await db.query('SELECT 1 FROM sst.cipa_member WHERE company_id=$1 AND mandate_id=$2 AND id=$3',[p.companyId,id,memberId]);
    if(!m.rowCount)throw new ApiError(404,'NOT_FOUND','Membro nao encontrado neste mandato');
    const prior=(await db.query('SELECT member_id FROM sst.cipa_portal_grant WHERE company_id=$1 AND mandate_id=$2 AND account_id=$3',[p.companyId,id,accountId])).rows[0];
    if(prior&&prior.member_id!==memberId)throw new ApiError(409,'LINK_CONFLICT','Conta ja vinculada a outro membro deste mandato');
    await db.query('INSERT INTO sst.cipa_portal_grant(company_id,mandate_id,account_id,member_id) VALUES($1,$2,$3,$4) ON CONFLICT DO NOTHING',[p.companyId,id,accountId,memberId]);
    const linked=await db.query('UPDATE sst.cipa_portal_grant SET active=true WHERE company_id=$1 AND mandate_id=$2 AND account_id=$3 AND member_id=$4 RETURNING account_id',[p.companyId,id,accountId,memberId]);
    if(!linked.rowCount)throw new ApiError(409,'LINK_CONFLICT','Membro ja possui outra conta vinculada');
    return entry(db,p,{mandateId:id,kind:'acesso',message:'Vinculo liberado para '+a.display_name},b.clientRequestId);
  });},
  revoke(p,id,b={}){manager(p);return withTenant(pool,p,async db=>{
    await mandate(db,p,id);const accountId=portalId(b.accountId);
    // Revoke this mandate only; other mandates remain explicitly assigned.
    const q=await db.query('UPDATE sst.cipa_portal_grant SET active=false WHERE company_id=$1 AND mandate_id=$2 AND account_id=$3 RETURNING account_id',[p.companyId,id,accountId]);
    if(!q.rowCount)throw new ApiError(404,'NOT_FOUND','Vinculo nao encontrado');
    await db.query('UPDATE sst.cipa_portal_session SET revoked_at=now() WHERE company_id=$1 AND account_id=$2 AND revoked_at IS NULL',[p.companyId,accountId]);
    return entry(db,p,{mandateId:id,kind:'acesso',message:'Vinculo revogado: '+accountId},b.clientRequestId);
  });},
  async reset(p,id,b={}){manager(p);const accountId=portalId(b.accountId),verifier=await hashPassword(b.password);
    return withTenant(pool,p,async db=>{
      await mandate(db,p,id);const a=(await db.query('SELECT a.id FROM sst.cipa_portal_account a JOIN sst.cipa_portal_grant g ON g.company_id=a.company_id AND g.account_id=a.id WHERE a.company_id=$1 AND g.mandate_id=$2 AND a.id=$3 AND a.active AND g.active FOR UPDATE OF a',[p.companyId,id,accountId])).rows[0];
      if(!a)throw new ApiError(404,'NOT_FOUND','Vinculo ativo nao encontrado');
      const eventData={mandateId:id,kind:'acesso',message:'Senha temporaria redefinida; sessoes revogadas: '+accountId};
      const previous=await db.query('SELECT 1 FROM sst.cipa_portal_entry WHERE company_id=$1 AND client_request_id=$2',[p.companyId,portalId(b.clientRequestId)]);
      if(previous.rowCount)return entry(db,p,eventData,b.clientRequestId);
      await db.query('UPDATE sst.cipa_portal_account SET password_verifier=$3,must_change_password=true,credential_changed_at=clock_timestamp() WHERE company_id=$1 AND id=$2',[p.companyId,accountId,verifier]);
      await db.query('UPDATE sst.cipa_portal_session SET revoked_at=now() WHERE company_id=$1 AND account_id=$2 AND revoked_at IS NULL',[p.companyId,accountId]);
      return entry(db,p,eventData,b.clientRequestId);
    });
  },
  createAction(p,id,b={}){staff(p);const data={assignedTo:portalId(b.assignedTo),title:portalText(b.title,200),description:typeof b.description==='string'&&!b.description.trim()?'':portalText(b.description),dueOn:date(b.dueOn),priority:b.priority};
    if(!['baixa','media','alta','critica'].includes(data.priority))throw new ApiError(400,'INVALID_INPUT','Prioridade invalida');
    const key=portalId(b.clientRequestId),fingerprint=hash([p.userId,id,data]);
    return withTenant(pool,p,async db=>{
      await mandate(db,p,id,true);
      const grant=await db.query('SELECT 1 FROM sst.cipa_portal_grant g JOIN sst.cipa_portal_account a ON a.company_id=g.company_id AND a.id=g.account_id WHERE g.company_id=$1 AND g.mandate_id=$2 AND g.account_id=$3 AND g.active AND a.active',[p.companyId,id,data.assignedTo]);
      if(!grant.rowCount)throw new ApiError(404,'NOT_FOUND','Destinatario sem vinculo ativo');
      const q=await db.query('INSERT INTO sst.cipa_portal_action(company_id,mandate_id,assigned_to,title,description,due_on,priority,created_by,client_request_id,request_fingerprint) VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10) ON CONFLICT(company_id,client_request_id) DO NOTHING RETURNING id,title,status,revision',[p.companyId,id,data.assignedTo,data.title,data.description,data.dueOn,data.priority,p.userId,key,fingerprint]);
      if(q.rowCount)return q.rows[0];
      const old=(await db.query('SELECT id,title,status,revision,request_fingerprint FROM sst.cipa_portal_action WHERE company_id=$1 AND client_request_id=$2',[p.companyId,key])).rows[0];
      if(!old||old.request_fingerprint!==fingerprint)throw new ApiError(409,'IDEMPOTENCY_CONFLICT','Chave de envio ja utilizada');
      const {request_fingerprint:_,...safe}=old;return safe;
    });
  },
  status(p,id,b={},isStaff=false){
    if(isStaff)staff(p);else member(p);
    const key=portalId(b.clientRequestId),message=portalText(b.message,1900),actionId=portalId(id);
    if(!Number.isInteger(b.expectedRevision)||b.expectedRevision<1)throw new ApiError(400,'INVALID_INPUT','Versao obrigatoria');
    return (isStaff?withTenant:withCipaMember)(pool,p,async db=>{
      const a=(await db.query('SELECT id,mandate_id,status,revision FROM sst.cipa_portal_action WHERE company_id=$1 AND id=$2 FOR UPDATE',[p.companyId,actionId])).rows[0];
      if(!a)throw new ApiError(404,'NOT_FOUND','Acao nao encontrada');
      await mandate(db,p,a.mandate_id,true);
      // Idempotency must precede the revision check for safe retries after a lost response.
      const data={mandateId:a.mandate_id,actionId,kind:isStaff?'decisao':'atualizacao',message:'['+b.status+'] '+message,expectedRevision:b.expectedRevision};
      const previous=await db.query('SELECT 1 FROM sst.cipa_portal_entry WHERE company_id=$1 AND client_request_id=$2',[p.companyId,key]);
      if(previous.rowCount){await entry(db,p,data,key);return a;}
      if(a.revision!==b.expectedRevision)throw new ApiError(409,'STALE_REVISION','Acao alterada por outra pessoa. Atualize antes de salvar');
      const next=nextPortalStatus(a.status,b.status,isStaff);
      const event=await entry(db,p,data,key);
      const q=await db.query('UPDATE sst.cipa_portal_action SET status=$3,revision=revision+1,updated_at=now() WHERE company_id=$1 AND id=$2 RETURNING id,status,revision',[p.companyId,actionId,next]);
      return {...q.rows[0],eventId:event.id};
    });
  },
  post(p,id,b={},isStaff=false){
    if(isStaff)staff(p);else member(p);
    const allowed=isStaff?['aviso','orientacao']:['sugestao','apoio','ciencia_reuniao','checklist','observacao'];
    if(!allowed.includes(b.kind))throw new ApiError(400,'INVALID_INPUT','Tipo nao permitido');
    const data={mandateId:portalId(id),kind:b.kind,message:b.kind==='checklist'?'':portalText(b.message)};
    if(b.kind==='checklist'){
      if(typeof b.period!=='string'||!/^\d{4}-(0[1-9]|1[0-2])$/.test(b.period)||
         !['verificar_ambiente','acompanhar_acoes','consultar_reuniao','sugerir_melhoria'].includes(b.itemKey)||
         typeof b.checked!=='boolean')throw new ApiError(400,'INVALID_INPUT','Roteiro mensal invalido');
      // No free text or attachments in checklist state; immutable individual event.
      data.message=[b.period,b.itemKey,b.checked?'feito':'pendente'].join('|');
    }
    if(b.kind==='observacao'){
      const location=portalText(b.location,140),description=portalText(b.message,1600);
      data.message='Local: '+location+'\nSituacao observada: '+description;
    }
    if(['apoio','orientacao'].includes(b.kind))data.actionId=portalId(b.actionId);
    if(b.kind==='ciencia_reuniao')data.meetingId=portalId(b.meetingId);
    return (isStaff?withTenant:withCipaMember)(pool,p,async db=>{
      await mandate(db,p,id,true);
      if(data.actionId){const q=await db.query('SELECT 1 FROM sst.cipa_portal_action WHERE company_id=$1 AND mandate_id=$2 AND id=$3',[p.companyId,id,data.actionId]);if(!q.rowCount)throw new ApiError(404,'NOT_FOUND','Acao nao encontrada');}
      if(data.meetingId){const q=await db.query("SELECT 1 FROM sst.cipa_meeting WHERE company_id=$1 AND mandate_id=$2 AND id=$3 AND status<>'cancelada'",[p.companyId,id,data.meetingId]);if(!q.rowCount)throw new ApiError(404,'NOT_FOUND','Reuniao nao encontrada ou cancelada');data.message='Ciencia de convocacao registrada. Nao comprova presenca ou assinatura.';}
      return entry(db,p,data,b.clientRequestId);
    });
  },
};}
