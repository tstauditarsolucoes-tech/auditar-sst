import {useEffect,useState} from 'react';
type Role='adm'|'gestor'|'tecnico'|'cliente';
type Session={role:Role;companyId:string;csrfToken:string;user:{id:string}};
type Kind='treinamento'|'dds'|'integracao';
type Status='planejado'|'realizado'|'cancelado';
type Activity={
  id:string;kind:Kind;title:string;sector:string;nr_reference:string;instructor:string;
  planned_at:string|null;duration_minutes:number|null;participants_count:number|null;
  status:Status;revision:number;created_by:string;updated_at:string;
};
type History={id:string;kind:string;message:string;created_at:string};
type Detail={training:Activity;events:History[]};
const kindNames:Record<Kind,string>={treinamento:'Treinamento',dds:'DDS',integracao:'Integração'};
const statusNames:Record<Status,string>={planejado:'Planejado',realizado:'Realizado (informado)',cancelado:'Cancelado'};
async function request<T>(url:string,method:'GET'|'POST'|'PATCH'='GET',body?:object,csrf?:string):Promise<T>{
  const res=await fetch('/api/v1/'+url,{
    method,credentials:'same-origin',cache:'no-store',
    headers:{...(body?{'Content-Type':'application/json'}:{}),...(csrf?{'X-CSRF-Token':csrf}:{})},
    body:body?JSON.stringify(body):undefined,
  });
  const value:unknown=await res.json().catch(()=>null);
  if(!res.ok){
    const code=value&&typeof value==='object'&&'code' in value?String((value as {code:string}).code):String(res.status);
    const errors:Record<string,string>={
      FORBIDDEN:'Sem permissão para esta atividade.',
      STALE_REVISION:'O registro mudou. Reabra antes de salvar.',
      INVALID_STATE:'Este registro já foi encerrado.',
      IDEMPOTENCY_CONFLICT:'A chave de envio já foi usada.',
      INCOMPLETE_ACTIVITY:'Informe duração e quantidade de participantes antes de marcar como realizado.',
      UNAUTHENTICATED:'Sessão expirada ou indisponível.',
    };
    throw new Error(errors[code]||'Operação indisponível: '+code);
  }
  return value as T;
}
function isoTime(value:string):string|null{return value?new Date(value).toISOString():null;}
function localTime(value:string|null):string{
  if(!value)return '';
  const d=new Date(value);
  return new Date(d.getTime()-d.getTimezoneOffset()*60000).toISOString().slice(0,16);
}
function maybeInt(value:string):number|null{return value===''?null:Number(value);}
type FormState={
  kind:Kind;title:string;sector:string;nrReference:string;instructor:string;plannedAt:string;
  durationMinutes:string;participantsCount:string;
};
const empty=():FormState=>({
  kind:'treinamento',title:'',sector:'',nrReference:'',instructor:'',plannedAt:'',
  durationMinutes:'',participantsCount:'',
});
function fromActivity(a:Activity):FormState{return {
  kind:a.kind,title:a.title,sector:a.sector,nrReference:a.nr_reference,
  instructor:a.instructor,plannedAt:localTime(a.planned_at),
  durationMinutes:a.duration_minutes?.toString()||'',
  participantsCount:a.participants_count?.toString()??'',
};}
function payload(form:FormState){return {
  kind:form.kind,title:form.title,sector:form.sector,nrReference:form.nrReference,
  instructor:form.instructor,plannedAt:isoTime(form.plannedAt),
  durationMinutes:maybeInt(form.durationMinutes),participantsCount:maybeInt(form.participantsCount),
};}
export function TrainingPilot({session}:{session:Session}){
  const [items,setItems]=useState<Activity[]>([]);
  const [selected,setSelected]=useState<Detail|null>(null);
  const [form,setForm]=useState<FormState>(empty);
  const [edit,setEdit]=useState<FormState>(empty);
  const [filter,setFilter]=useState<'todos'|Kind>('todos');
  const [note,setNote]=useState('');
  const [newKey,setNewKey]=useState(()=>crypto.randomUUID());
  const [statusKey,setStatusKey]=useState(()=>crypto.randomUUID());
  const [busy,setBusy]=useState(false);
  const [notice,setNotice]=useState('');
  const canManage=selected&&(session.role==='adm'||session.role==='gestor'||
    selected.training.created_by===session.user.id);
  async function refresh(){
    const list=await request<{items:Activity[]}>('training-sessions');
    setItems(list.items);
  }
  useEffect(()=>{
    let active=true;
    request<{items:Activity[]}>('training-sessions')
      .then(d=>{if(active)setItems(d.items);})
      .catch(()=>{if(active)setNotice('Treinamentos ainda indisponíveis na homologação.');});
    return()=>{active=false;};
  },[session.companyId]);
  async function run(fn:()=>Promise<void>){
    setBusy(true);setNotice('');
    try{await fn();}
    catch(error){setNotice(error instanceof Error?error.message:'Falha de homologação');}
    finally{setBusy(false);}
  }
  async function open(id:string){
    const detail=await request<Detail>('training-sessions/'+id);
    setSelected(detail);setEdit(fromActivity(detail.training));
    setNote('');setStatusKey(crypto.randomUUID());
  }
  async function create(){
    const result=await request<{item:Activity}>('training-sessions','POST',{
      ...payload(form),clientRequestId:newKey,
    },session.csrfToken);
    setForm(empty());setNewKey(crypto.randomUUID());
    await refresh();await open(result.item.id);
    setNotice('Atividade fictícia salva na base de homologação.');
  }
  async function saveEdit(){
    if(!selected)return;
    await request('training-sessions/'+selected.training.id,'PATCH',{
      ...payload(edit),expectedRevision:selected.training.revision,
    },session.csrfToken);
    await refresh();await open(selected.training.id);
    setNotice('Registro atualizado com histórico.');
  }
  async function changeStatus(status:'realizado'|'cancelado'){
    if(!selected)return;
    await request('training-sessions/'+selected.training.id+'/status','POST',{
      status,message:note,expectedRevision:selected.training.revision,
      clientRequestId:statusKey,
    },session.csrfToken);
    await refresh();await open(selected.training.id);
    setNotice('Situação registrada no histórico de homologação.');
  }
  const shown=items.filter(item=>filter==='todos'||item.kind===filter);
  function updateForm(key:keyof FormState,value:string,editing=false){
    const change=(s:FormState)=>({...s,[key]:value});
    if(editing)setEdit(change);else setForm(change);
  }
  function fields(f:FormState,editing=false){
    return <div className="auth-form">
      {!editing&&<label>Tipo
        <select value={f.kind} onChange={e=>updateForm('kind',e.target.value)}>
          {(['treinamento','dds','integracao'] as const).map(k=><option key={k} value={k}>{kindNames[k]}</option>)}
        </select>
      </label>}
      <label>Tema / título
        <input required maxLength={200} value={f.title}
          onChange={e=>updateForm('title',e.target.value,editing)}
          placeholder="Ex.: Uso correto de protetor auricular"/>
      </label>
      <div className="inspection-two">
        <label>Setor
          <input maxLength={180} value={f.sector} onChange={e=>updateForm('sector',e.target.value,editing)}/>
        </label>
        <label>NR de referência (quando aplicável)
          <input maxLength={100} value={f.nrReference}
            onChange={e=>updateForm('nrReference',e.target.value,editing)} placeholder="Ex.: NR-06"/>
        </label>
      </div>
      <label>Instrutor / responsável pela orientação
        <input maxLength={180} value={f.instructor} onChange={e=>updateForm('instructor',e.target.value,editing)}/>
      </label>
      <div className="inspection-two">
        <label>Data e hora
          <input type="datetime-local" value={f.plannedAt}
            onChange={e=>updateForm('plannedAt',e.target.value,editing)}/>
        </label>
        <label>Duração (minutos)
          <input type="number" min="1" max="1440" value={f.durationMinutes}
            onChange={e=>updateForm('durationMinutes',e.target.value,editing)} placeholder="Ex.: 15"/>
        </label>
      </div>
      <label>Quantidade informada de participantes
        <input type="number" min="0" max="10000" value={f.participantsCount}
          onChange={e=>updateForm('participantsCount',e.target.value,editing)}/>
      </label>
    </div>;
  }
  return <section className="panel" aria-label="Treinamentos e DDS de homologação">
    <div className="panel-top">
      <div><p className="eyebrow green">TREINAMENTOS E DDS · HOMOLOGAÇÃO</p>
        <h2>Registro de atividades educativas</h2>
        <p className="muted">Planejamento, orientação realizada e histórico por empresa.</p>
      </div><span className="tag">{items.length} registro(s)</span>
    </div>
    <p className="privacy-warning">Não substitui certificado, lista de presença, carga horária legal ou comprovante. Use somente dados fictícios; não importe pessoas ou fotos reais.</p>
    {notice&&<p className="auth-message" role="status">{notice}</p>}
    <form className="auth-form" onSubmit={e=>{e.preventDefault();void run(create);}}>
      <h3>Nova atividade</h3>{fields(form)}
      <button type="submit" className="primary-button" disabled={busy||!form.title.trim()}>Salvar planejamento</button>
    </form>
    <div className="auth-divider"/>
    <div className="panel-top"><h3>Histórico da empresa</h3>
      <button className="secondary-button" type="button" disabled={busy} onClick={()=>void run(refresh)}>Atualizar</button>
    </div>
    <label>Filtrar tipo
      <select value={filter} onChange={e=>setFilter(e.target.value as typeof filter)}>
        <option value="todos">Todos</option>
        {(['treinamento','dds','integracao'] as const).map(k=><option key={k} value={k}>{kindNames[k]}</option>)}
      </select>
    </label>
    {!shown.length&&<p className="empty">Nenhuma atividade fictícia para este filtro.</p>}
    <div className="inspection-list">{shown.map(item=><article className="inspection-item" key={item.id}>
      <div><strong>{item.title}</strong>
        <small>{kindNames[item.kind]} · {statusNames[item.status]} · {item.sector||'Sem setor'}</small>
        <small>{item.planned_at?new Date(item.planned_at).toLocaleString('pt-BR'):'Data a definir'}</small>
      </div>
      <button type="button" className="secondary-button" disabled={busy}
        onClick={()=>void run(()=>open(item.id))}>Abrir</button>
    </article>)}</div>
    {selected&&<div className="inspection-detail">
      <h3>{selected.training.title}</h3>
      <p className="muted">{kindNames[selected.training.kind]} · {statusNames[selected.training.status]} · revisão {selected.training.revision}</p>
      {canManage&&selected.training.status==='planejado'&&
      <form className="auth-form" onSubmit={e=>{e.preventDefault();void run(saveEdit);}}>
        <h4>Editar planejamento</h4>{fields(edit,true)}
        <button type="submit" className="secondary-button" disabled={busy||!edit.title.trim()}>Salvar alterações</button>
      </form>}
      {canManage&&selected.training.status==='planejado'&&<div className="auth-form">
        <label>Observação / motivo do cancelamento
          <textarea rows={2} maxLength={1200} value={note} onChange={e=>setNote(e.target.value)}/>
        </label>
        <div className="auth-actions">
          <button className="primary-button" type="button" disabled={busy}
            onClick={()=>void run(()=>changeStatus('realizado'))}>Marcar realizado</button>
          <button className="secondary-button" type="button" disabled={busy||!note.trim()}
            onClick={()=>void run(()=>changeStatus('cancelado'))}>Cancelar com motivo</button>
        </div>
        <p className="muted">Para marcar realizado, informe antes a duração e a quantidade de participantes. Essa indicação não certifica presença nem conformidade normativa.</p>
      </div>}
      <h4>Histórico</h4>
      <ol className="auth-timeline">{selected.events.map(event=><li key={event.id}>
        <strong>{event.kind.replaceAll('_',' ')}</strong>
        {event.message&&<p>{event.message}</p>}
        <small>{new Date(event.created_at).toLocaleString('pt-BR')}</small>
      </li>)}</ol>
      <button className="secondary-button" type="button" disabled={busy} onClick={()=>setSelected(null)}>Fechar</button>
    </div>}
  </section>;
}
