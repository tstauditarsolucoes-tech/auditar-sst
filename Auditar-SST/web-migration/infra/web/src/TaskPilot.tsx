import {useEffect,useState} from 'react';

type Role='adm'|'gestor'|'tecnico'|'cliente';
type Session={role:Role;companyId:string;csrfToken:string};
type TaskStatus='aberta'|'em_andamento'|'concluida'|'cancelada';
type Priority='baixa'|'media'|'alta'|'critica';
type Task={
  id:string;title:string;description:string;priority:Priority;status:TaskStatus;
  assigned_to:string;assigned_by:string;assigned_name:string|null;
  due_at:string|null;revision:number;created_at:string;completed_at:string|null;
};
type Assignee={user_id:string;role:Role;display_name:string};
type Event={id:string;kind:string;message:string;created_at:string};
type Detail={task:Task;events:Event[]};
const names:Record<TaskStatus,string>={
  aberta:'Aberta',em_andamento:'Em andamento',concluida:'Concluída',cancelada:'Cancelada',
};
const newRequestId=()=>crypto.randomUUID();
function utc(local:string):string|null{return local?new Date(local).toISOString():null;}
function localDate(iso:string|null){
  if(!iso)return '';
  const date=new Date(iso);
  const local=new Date(date.getTime()-date.getTimezoneOffset()*60000);
  return local.toISOString().slice(0,16);
}
async function api<T>(path:string,method:'GET'|'POST'|'PATCH'='GET',body?:object,csrf?:string){
  const res=await fetch('/api/v1/'+path,{
    method,
    headers:{...(body?{'content-type':'application/json'}:{}),...(csrf?{'x-csrf-token':csrf}:{})},
    credentials:'same-origin',cache:'no-store',body:body?JSON.stringify(body):undefined,
  });
  const data:unknown=await res.json().catch(()=>null);
  if(!res.ok){
    const code=data&&typeof data==='object'&&'code' in data?
      String((data as {code:string}).code):'HTTP_'+res.status;
    const messages:Record<string,string>={
      UNAUTHENTICATED:'Sessão de homologação expirada.',
      FORBIDDEN:'Sua conta não tem permissão para essa tarefa.',
      NOT_FOUND:'Tarefa não encontrada nesta empresa.',
      INVALID_ASSIGNEE:'Escolha um técnico ativo da empresa.',
      INVALID_STATE:'Essa mudança de status não é permitida.',
      IDEMPOTENCY_CONFLICT:'O envio foi reutilizado com outros dados.',
      STALE_REVISION:'Esta tarefa foi alterada; reabra antes de editar.',
    };
    throw new Error(messages[code]||'Operação indisponível: '+code);
  }
  return data as T;
}
export function TaskPilot({session,userId}:{session:Session;userId:string}){
  const [tasks,setTasks]=useState<Task[]>([]);
  const [assignees,setAssignees]=useState<Assignee[]>([]);
  const [detail,setDetail]=useState<Detail|null>(null);
  const [busy,setBusy]=useState(false);
  const [notice,setNotice]=useState('');
  const [title,setTitle]=useState('');
  const [description,setDescription]=useState('');
  const [priority,setPriority]=useState<Priority>('media');
  const [dueAt,setDueAt]=useState('');
  const [assignedTo,setAssignedTo]=useState(userId);
  const [requestKey,setRequestKey]=useState(newRequestId);
  const [comment,setComment]=useState('');
  const [editTitle,setEditTitle]=useState('');
  const [editDescription,setEditDescription]=useState('');
  const [editPriority,setEditPriority]=useState<Priority>('media');
  const [editDueAt,setEditDueAt]=useState('');
  const [editAssignee,setEditAssignee]=useState(userId);
  const manager=['adm','gestor'].includes(session.role);
  useEffect(()=>{
    let live=true;
    Promise.all([
      api<{items:Task[]}>('tasks'),
      manager?api<{items:Assignee[]}>('tasks/assignees'):Promise.resolve({items:[]}),
    ]).then(([list,staff])=>{
      if(!live)return;
      setTasks(list.items);setAssignees(staff.items);
    }).catch(()=>{if(live)setNotice('Agenda ainda indisponível neste ambiente de homologação.');});
    return()=>{live=false;};
  },[manager]);
  async function run(action:()=>Promise<void>){
    setBusy(true);setNotice('');
    try{await action();}
    catch(error){setNotice(error instanceof Error?error.message:'Falha no teste');}
    finally{setBusy(false);}
  }
  async function refresh(){
    const list=await api<{items:Task[]}>('tasks');
    setTasks(list.items);
  }
  async function open(id:string){
    const value=await api<Detail>('tasks/'+id);
    setDetail(value);
    setEditTitle(value.task.title);
    setEditDescription(value.task.description);
    setEditPriority(value.task.priority);
    setEditDueAt(localDate(value.task.due_at));
    setEditAssignee(value.task.assigned_to);
    setComment('');
  }
  async function create(){
    await api('tasks','POST',{
      title,description,priority,dueAt:utc(dueAt),
      assignedTo:manager?assignedTo:userId,clientRequestId:requestKey,
    },session.csrfToken);
    setRequestKey(newRequestId());setTitle('');setDescription('');setDueAt('');setPriority('media');
    await refresh();
    setNotice('Tarefa fictícia registrada na agenda da empresa.');
  }
  async function edit(){
    if(!detail)return;
    await api('tasks/'+detail.task.id,'PATCH',{
      title:editTitle,description:editDescription,priority:editPriority,
      dueAt:utc(editDueAt),assignedTo:editAssignee,
      expectedRevision:detail.task.revision,
    },session.csrfToken);
    await open(detail.task.id);
    await refresh();
    setNotice('Alterações da tarefa registradas no histórico.');
  }
  async function status(next:TaskStatus){
    if(!detail)return;
    await api('tasks/'+detail.task.id+'/status','POST',{
      status:next,message:comment,
    },session.csrfToken);
    await open(detail.task.id);
    await refresh();
    setNotice('Andamento registrado com sucesso.');
  }
  const canStatus=detail&&(manager||detail.task.assigned_to===userId);
  const active=detail&&['aberta','em_andamento'].includes(detail.task.status);
  return <section className="task-pilot" aria-label="Agenda SST de homologação">
    <div className="panel-top">
      <div>
        <p className="eyebrow green">AGENDA SST • HOMOLOGAÇÃO PRIVADA</p>
        <h3>Tarefas e acompanhamento da equipe</h3>
        <p className="muted">Apenas tarefas fictícias da empresa ativa. Sem alterar a agenda dos aplicativos instalados.</p>
      </div>
      <button type="button" className="secondary-button" disabled={busy}
        onClick={()=>void run(refresh)}>Atualizar agenda</button>
    </div>
    {notice&&<p role="status" className="auth-message">{notice}</p>}
    <form className="auth-form" onSubmit={event=>{event.preventDefault();void run(create);}}>
      <h4>Nova tarefa fictícia</h4>
      <label>Título<input required maxLength={200} value={title}
        onChange={event=>setTitle(event.target.value)} placeholder="Ex.: Verificar extintor do setor"/></label>
      <label>Descrição<textarea maxLength={4000} rows={2} value={description}
        onChange={event=>setDescription(event.target.value)}/></label>
      <div className="inspection-two">
        <label>Prioridade
          <select value={priority} onChange={event=>setPriority(event.target.value as Priority)}>
            {(['baixa','media','alta','critica'] as const).map(p=><option key={p} value={p}>{p}</option>)}
          </select>
        </label>
        <label>Prazo previsto
          <input type="datetime-local" value={dueAt} onChange={event=>setDueAt(event.target.value)}/>
        </label>
      </div>
      {manager&&<label>Responsável
        <select value={assignedTo} onChange={event=>setAssignedTo(event.target.value)}>
          {assignees.map(person=><option key={person.user_id} value={person.user_id}>
            {person.display_name} · {person.role}
          </option>)}
        </select>
      </label>}
      {!manager&&<p className="muted">O técnico pode criar tarefa para si; o gestor atribui tarefas para a equipe.</p>}
      <button type="submit" className="primary-button"
        disabled={busy||(manager&&!assignees.some(a=>a.user_id===assignedTo))}>Registrar tarefa</button>
    </form>
    <h4>Minhas tarefas / equipe</h4>
    {tasks.length===0&&<p className="empty">Nenhuma tarefa fictícia cadastrada nesta empresa.</p>}
    <div className="inspection-list">{tasks.map(task=><article key={task.id} className="inspection-item">
      <div>
        <strong>{task.title}</strong>
        <small>{names[task.status]} · Prioridade {task.priority} · {task.assigned_name||'Responsável'}</small>
        {task.due_at&&<small>Prazo: {new Date(task.due_at).toLocaleString('pt-BR')}</small>}
      </div>
      <button type="button" className="secondary-button" disabled={busy}
        onClick={()=>void run(()=>detail?.task.id===task.id?Promise.resolve(setDetail(null)):open(task.id))}>
        {detail?.task.id===task.id?'Fechar':'Abrir'}
      </button>
    </article>)}</div>
    {detail&&<div className="inspection-detail">
      <h4>{detail.task.title}</h4>
      <p className="muted">{names[detail.task.status]} · Revisão {detail.task.revision}</p>
      <p>{detail.task.description}</p>
      {manager&&active&&<form className="auth-form" onSubmit={event=>{event.preventDefault();void run(edit);}}>
        <h4>Editar designação e prazo</h4>
        <label>Título<input required maxLength={200} value={editTitle}
          onChange={event=>setEditTitle(event.target.value)}/></label>
        <label>Descrição<textarea maxLength={4000} rows={2} value={editDescription}
          onChange={event=>setEditDescription(event.target.value)}/></label>
        <div className="inspection-two">
          <label>Prioridade<select value={editPriority} onChange={event=>setEditPriority(event.target.value as Priority)}>
            {(['baixa','media','alta','critica'] as const).map(p=><option key={p} value={p}>{p}</option>)}
          </select></label>
          <label>Prazo<input type="datetime-local" value={editDueAt} onChange={event=>setEditDueAt(event.target.value)}/></label>
        </div>
        <label>Responsável<select value={editAssignee} onChange={event=>setEditAssignee(event.target.value)}>
          {assignees.map(person=><option key={person.user_id} value={person.user_id}>{person.display_name}</option>)}
        </select></label>
        <button type="submit" className="secondary-button" disabled={busy}>Salvar ajustes</button>
      </form>}
      {canStatus&&active&&<div className="auth-form">
        <h4>Atualizar andamento</h4>
        <label>Comentário / motivo de cancelamento
          <textarea rows={2} maxLength={1200} value={comment} onChange={event=>setComment(event.target.value)}/>
        </label>
        <div className="auth-actions">
          {detail.task.status==='aberta'&&<button type="button" className="secondary-button" disabled={busy}
            onClick={()=>void run(()=>status('em_andamento'))}>Iniciar</button>}
          <button type="button" className="primary-button" disabled={busy}
            onClick={()=>void run(()=>status('concluida'))}>Concluir</button>
          <button type="button" className="secondary-button" disabled={busy||!comment.trim()}
            onClick={()=>void run(()=>status('cancelada'))}>Cancelar com motivo</button>
        </div>
      </div>}
      <h4>Histórico da tarefa</h4>
      <ol className="auth-timeline">{detail.events.map(event=><li key={event.id}>
        <strong>{event.kind.replaceAll('_',' ')}</strong>
        {event.message&&<p>{event.message}</p>}
        <small>{new Date(event.created_at).toLocaleString('pt-BR')}</small>
      </li>)}</ol>
    </div>}
  </section>;
}
