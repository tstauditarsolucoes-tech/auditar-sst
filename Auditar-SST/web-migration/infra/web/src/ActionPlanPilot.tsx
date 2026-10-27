import {useEffect,useState} from 'react';

type Role='adm'|'gestor'|'tecnico'|'cliente';
type Session={role:Role;companyId:string;csrfToken:string;user:{id:string}};
type Nc={id:string;short_title:string;description:string};
type Person={user_id:string;display_name:string};
type Plan={
 id:string;non_conformity_id:string;title:string;description:string;assigned_to:string;
 assigned_name?:string|null;status:'aberta'|'em_andamento'|'concluida'|'cancelada';
 due_at:string|null;revision:number;nc_title?:string|null;
};
type Event={id:string;kind:string;message:string;created_at:string};
type Detail={plan:Plan;events:Event[]};
const statusLabel:Record<Plan['status'],string>={
 aberta:'Aberto',em_andamento:'Em andamento',concluida:'Concluído',cancelada:'Cancelado',
};
async function request<T>(path:string,method:'GET'|'POST'|'PATCH'='GET',body?:object,csrf?:string):Promise<T>{
 const response=await fetch('/api/v1/'+path,{
  method,credentials:'same-origin',cache:'no-store',
  headers:{...(body?{'content-type':'application/json'}:{}),...(csrf?{'x-csrf-token':csrf}:{})},
  body:body?JSON.stringify(body):undefined,
 });
 const value:unknown=await response.json().catch(()=>null);
 if(!response.ok){
  const code=value&&typeof value==='object'&&'code' in value?
   String((value as {code:string}).code):'HTTP_'+response.status;
  const help:Record<string,string>={
   UNAUTHENTICATED:'Sessão de homologação encerrada.',
   FORBIDDEN:'Seu perfil não tem permissão.',
   NOT_FOUND:'Plano ou NC não disponível nesta empresa.',
   INVALID_ASSIGNEE:'Responsável não pertence à empresa ativa.',
   STALE_REVISION:'Outro usuário atualizou este plano. Reabra e confira.',
   IDEMPOTENCY_CONFLICT:'Reenvio com código usado em outra operação.',
   INVALID_STATE:'Esta mudança de situação não é permitida.',
  };
  throw new Error(help[code]||'Operação indisponível: '+code);
 }
 return value as T;
}
function localDate(iso:string|null){if(!iso)return '';const dt=new Date(iso);
 return new Date(dt.getTime()-dt.getTimezoneOffset()*60000).toISOString().slice(0,16);}
function due(iso:string){return iso?new Date(iso).toISOString():null;}
export function ActionPlanPilot({session}:{session:Session}){
 const manager=session.role==='adm'||session.role==='gestor';
 const [plans,setPlans]=useState<Plan[]>([]);
 const [ncs,setNcs]=useState<Nc[]>([]);
 const [staff,setStaff]=useState<Person[]>([]);
 const [selected,setSelected]=useState<Detail|null>(null);
 const [ncId,setNcId]=useState('');
 const [title,setTitle]=useState('');
 const [description,setDescription]=useState('');
 const [assignedTo,setAssignedTo]=useState(session.user.id);
 const [dueAt,setDueAt]=useState('');
 const [createKey,setCreateKey]=useState(()=>crypto.randomUUID());
 const [message,setMessage]=useState('');
 const [transitionKey,setTransitionKey]=useState(()=>crypto.randomUUID());
 const [editTitle,setEditTitle]=useState('');
 const [editDescription,setEditDescription]=useState('');
 const [editDue,setEditDue]=useState('');
 const [editAssignee,setEditAssignee]=useState(session.user.id);
 const [busy,setBusy]=useState(false);
 const [notice,setNotice]=useState('');
 async function refresh(){
  const data=await request<{items:Plan[]}>('action-plans');
  setPlans(data.items);
 }
 async function open(id:string){
  const result=await request<Detail>('action-plans/'+id);
  setSelected(result);setMessage('');setTransitionKey(crypto.randomUUID());
  setEditTitle(result.plan.title);setEditDescription(result.plan.description);
  setEditDue(localDate(result.plan.due_at));setEditAssignee(result.plan.assigned_to);
 }
 useEffect(()=>{
  let active=true;
  Promise.all([
   request<{items:Plan[]}>('action-plans'),
   request<{items:Nc[]}>('nonconformities'),
   manager?request<{items:Person[]}>('tasks/assignees'):Promise.resolve({items:[]}),
  ]).then(([p,n,users])=>{
   if(!active)return;
   setPlans(p.items);setNcs(n.items);setStaff(users.items);
   setNcId(current=>current||n.items[0]?.id||'');
  }).catch(()=>{if(active)setNotice('Plano de Ação ainda indisponível nesta homologação.');});
  return()=>{active=false;};
 },[session.companyId,manager]);
 async function run(action:()=>Promise<void>){
  setBusy(true);setNotice('');
  try{await action();}
  catch(error){setNotice(error instanceof Error?error.message:'Falha de homologação');}
  finally{setBusy(false);}
 }
 async function create(){
  const result=await request<{item:Plan}>('action-plans','POST',{
   nonConformityId:ncId,title,description,
   assignedTo:manager?assignedTo:session.user.id,
   dueAt:due(dueAt),clientRequestId:createKey,
  },session.csrfToken);
  setTitle('');setDescription('');setDueAt('');setCreateKey(crypto.randomUUID());
  await refresh();await open(result.item.id);
  setNotice('Plano registrado apenas na base de homologação.');
 }
 async function edit(){
  if(!selected)return;
  await request('action-plans/'+selected.plan.id,'PATCH',{
   title:editTitle,description:editDescription,dueAt:due(editDue),
   assignedTo:editAssignee,expectedRevision:selected.plan.revision,
  },session.csrfToken);
  await refresh();await open(selected.plan.id);
  setNotice('Plano atualizado com controle de revisão.');
 }
 async function changeStatus(status:Plan['status']){
  if(!selected)return;
  await request('action-plans/'+selected.plan.id+'/status','POST',{
   status,message,expectedRevision:selected.plan.revision,clientRequestId:transitionKey,
  },session.csrfToken);
  await refresh();await open(selected.plan.id);
  setNotice('Andamento salvo no histórico da homologação.');
 }
 return <section className="panel">
  <div className="panel-top"><div><p className="eyebrow green">MÓDULO WEB EM HOMOLOGAÇÃO</p>
   <h2>Plano de Ação SST</h2>
   <p className="muted">Planos vinculados às NCs, responsáveis, prazos e histórico. Somente base nova de testes.</p>
  </div><span className="tag">{plans.length} plano(s)</span></div>
  <p className="privacy-warning">Use somente empresas e situações fictícias. Nenhum plano antigo foi migrado do aplicativo.</p>
  {notice&&<p className="auth-message" role="status">{notice}</p>}
  {ncs.length>0&&<form className="auth-form" onSubmit={e=>{e.preventDefault();void run(create);}}>
   <h3>Novo plano vinculado a uma NC</h3>
   <label>Não conformidade
    <select value={ncId} required onChange={e=>setNcId(e.target.value)}>
     {ncs.map(n=><option key={n.id} value={n.id}>{n.short_title||n.description.slice(0,85)} · {n.id.slice(0,8)}</option>)}
    </select>
   </label>
   <label>Medida a executar
    <input required maxLength={180} value={title} onChange={e=>setTitle(e.target.value)} placeholder="Ex.: Instalar proteção da máquina" />
   </label>
   <label>Descrição e critério de conclusão
    <textarea required rows={3} maxLength={4000} value={description} onChange={e=>setDescription(e.target.value)}/>
   </label>
   {manager&&<label>Responsável
    <select value={assignedTo} onChange={e=>setAssignedTo(e.target.value)}>
     {staff.map(member=><option key={member.user_id} value={member.user_id}>{member.display_name}</option>)}
    </select>
   </label>}
   <label>Prazo (opcional)
    <input type="datetime-local" value={dueAt} onChange={e=>setDueAt(e.target.value)}/>
   </label>
   <button className="primary-button" type="submit" disabled={busy||!ncId||manager&&!staff.length}>Criar plano fictício</button>
  </form>}
  {!ncs.length&&<p className="empty">Cadastre uma NC fictícia primeiro para vinculá-la a um plano.</p>}
  <div className="auth-divider"/>
  <div className="panel-top"><h3>Planos desta empresa</h3>
   <button className="secondary-button" type="button" disabled={busy} onClick={()=>void run(refresh)}>Atualizar</button>
  </div>
  {!plans.length&&<p className="empty">Ainda não há planos registrados neste ambiente.</p>}
  <div className="nc-list">{plans.map(plan=><article key={plan.id} className="nc-card">
   <p className="nc-code">{plan.id.slice(0,8)} · NC {plan.non_conformity_id.slice(0,8)}</p>
   <h3>{plan.title}</h3><p>{plan.description}</p>
   <p className="muted">{statusLabel[plan.status]} · {plan.assigned_name||'Equipe'} · Prazo: {plan.due_at?new Date(plan.due_at).toLocaleDateString('pt-BR'):'A definir'}</p>
   <button className="secondary-button" disabled={busy} onClick={()=>void run(()=>open(plan.id))}>Detalhes e andamento</button>
  </article>)}</div>
  {selected&&<div className="auth-form">
   <h3>Plano: {selected.plan.title}</h3>
   <p className="muted">Revisão {selected.plan.revision} · {statusLabel[selected.plan.status]}</p>
   {manager&&!['cancelada','concluida'].includes(selected.plan.status)&&<>
    <label>Medida<input maxLength={180} value={editTitle} onChange={e=>setEditTitle(e.target.value)}/></label>
    <label>Descrição<textarea rows={3} maxLength={4000} value={editDescription} onChange={e=>setEditDescription(e.target.value)}/></label>
    <label>Responsável<select value={editAssignee} onChange={e=>setEditAssignee(e.target.value)}>
     {staff.map(member=><option value={member.user_id} key={member.user_id}>{member.display_name}</option>)}
    </select></label>
    <label>Prazo<input type="datetime-local" value={editDue} onChange={e=>setEditDue(e.target.value)}/></label>
    <button className="secondary-button" disabled={busy||!editTitle.trim()||!editDescription.trim()} onClick={()=>void run(edit)}>Salvar alterações</button>
   </>}
   {['aberta','em_andamento'].includes(selected.plan.status)&&<>
    <label>Comentário / motivo de cancelamento
     <textarea maxLength={1200} rows={2} value={message} onChange={e=>setMessage(e.target.value)}/>
    </label>
    <div className="auth-actions">
     {selected.plan.status==='aberta'&&<button className="secondary-button" disabled={busy} onClick={()=>void run(()=>changeStatus('em_andamento'))}>Iniciar execução</button>}
     <button className="primary-button" disabled={busy} onClick={()=>void run(()=>changeStatus('concluida'))}>Marcar como concluído</button>
     {manager&&<button className="secondary-button" disabled={busy||!message.trim()} onClick={()=>void run(()=>changeStatus('cancelada'))}>Cancelar com motivo</button>}
    </div>
   </>}
   <h4>Histórico imutável</h4>
   <ol className="auth-timeline">{selected.events.map(ev=><li key={ev.id}>
    <strong>{ev.kind.replaceAll('_',' ')}</strong>{ev.message&&<p>{ev.message}</p>}
    <small>{new Date(ev.created_at).toLocaleString('pt-BR')}</small>
   </li>)}</ol>
   <button className="secondary-button" disabled={busy} onClick={()=>setSelected(null)}>Fechar detalhes</button>
  </div>}
 </section>;
}
