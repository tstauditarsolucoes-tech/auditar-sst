import {useEffect,useState} from 'react';

type Session={role:'adm'|'gestor'|'tecnico'|'cliente';csrfToken:string;user:{id:string}};
type Nc={id:string;short_title:string;description:string;probability:number;severity:number;status:string;updated_at:string};
type Timeline={id:string;kind:string;message:string;created_at:string;nc_id:string;short_title:string};
type Dashboard={counts:{status:string;total:number}[];pending:Nc[];timeline:Timeline[]};
type Thread={id:string;subject:string;status:'aberta'|'encerrada';created_by:string;updated_at:string};
type SupportMessage={id:string;message:string;kind:string;created_by:string;created_at:string};
type ThreadDetail={item:Thread;messages:SupportMessage[]};
const label:Record<string,string>={
  aberta:'Aberta',correcao_informada:'Aguardando validação',validada:'Validada',rejeitada:'Correção rejeitada',
};
async function api<T>(url:string,method:'GET'|'POST'='GET',payload?:object,csrf?:string):Promise<T>{
  const response=await fetch('/api/v1/'+url,{
    method,credentials:'same-origin',cache:'no-store',
    headers:{...(payload?{'Content-Type':'application/json'}:{}),...(csrf?{'X-CSRF-Token':csrf}:{})},
    body:payload?JSON.stringify(payload):undefined,
  });
  const body:unknown=await response.json().catch(()=>null);
  if(!response.ok){
    const code=body&&typeof body==='object'&&'code' in body?String((body as {code:string}).code):String(response.status);
    throw new Error('A operação não foi concluída: '+code);
  }
  return body as T;
}
export function ClientPortalPilot({session}:{session:Session}){
  const [dashboard,setDashboard]=useState<Dashboard|null>(null);
  const [threads,setThreads]=useState<Thread[]>([]);
  const [selected,setSelected]=useState<ThreadDetail|null>(null);
  const [subject,setSubject]=useState('');
  const [initial,setInitial]=useState('');
  const [requestKey,setRequestKey]=useState(()=>crypto.randomUUID());
  const [replyText,setReplyText]=useState('');
  const [replyKey,setReplyKey]=useState(()=>crypto.randomUUID());
  const [comment,setComment]=useState('');
  const [activeNc,setActiveNc]=useState<string|null>(null);
  const [ncHistory,setNcHistory]=useState<{id:string;kind:string;message:string;created_at:string}[]>([]);
  const [notice,setNotice]=useState('');
  const [busy,setBusy]=useState(false);
  const staff=session.role!=='cliente';
  async function refresh(){
    const [data,list]=await Promise.all([
      api<Dashboard>('portal/dashboard'),
      api<{items:Thread[]}>('portal/threads'),
    ]);
    setDashboard(data);setThreads(list.items);
  }
  useEffect(()=>{
    let live=true;
    Promise.all([api<Dashboard>('portal/dashboard'),api<{items:Thread[]}>('portal/threads')])
      .then(([data,list])=>{if(live){setDashboard(data);setThreads(list.items);}})
      .catch(()=>{if(live)setNotice('Portal ainda indisponível nesta homologação.');});
    return()=>{live=false;};
  },[]);
  async function run(action:()=>Promise<void>){
    setBusy(true);setNotice('');
    try{await action();}
    catch(e){setNotice(e instanceof Error?e.message:'Falha no teste');}
    finally{setBusy(false);}
  }
  async function create(){
    const result=await api<{item:Thread}>('portal/threads','POST',{
      subject,message:initial,clientRequestId:requestKey,
    },session.csrfToken);
    setSubject('');setInitial('');setRequestKey(crypto.randomUUID());
    await refresh();await open(result.item.id);
    setNotice('Solicitação registrada no atendimento de homologação.');
  }
  async function open(id:string){
    const result=await api<ThreadDetail>('portal/threads/'+id);
    setSelected(result);setReplyText('');setReplyKey(crypto.randomUUID());
  }
  async function reply(){
    if(!selected)return;
    await api('portal/threads/'+selected.item.id+'/messages','POST',{
      message:replyText,clientRequestId:replyKey,
    },session.csrfToken);
    setReplyText('');setReplyKey(crypto.randomUUID());
    await open(selected.item.id);await refresh();
    setNotice('Mensagem adicionada ao histórico.');
  }
  async function status(action:'close'|'reopen'){
    if(!selected)return;
    await api('portal/threads/'+selected.item.id+'/'+action,'POST',{message:comment},session.csrfToken);
    setComment('');await open(selected.item.id);await refresh();
    setNotice('Andamento do atendimento registrado.');
  }
  async function correction(nc:Nc,accepted?:boolean){
    if(accepted===false&&!comment.trim())throw new Error('Informe o motivo da rejeição.');
    if(accepted===undefined){
      await api('nonconformities/'+nc.id+'/correction','POST',{message:comment},session.csrfToken);
    }else{
      await api('nonconformities/'+nc.id+'/decision','POST',{accepted,reason:comment},session.csrfToken);
    }
    setComment('');setActiveNc(null);setNcHistory([]);await refresh();
    setNotice('Tratativa registrada na empresa de homologação.');
  }
  async function history(id:string){
    if(activeNc===id){setActiveNc(null);setNcHistory([]);return;}
    const result=await api<{items:{id:string;kind:string;message:string;created_at:string}[]}>('nonconformities/'+id+'/events');
    setActiveNc(id);setNcHistory(result.items);
  }
  const pending=dashboard?.pending||[];
  return <section className="portal-pilot" aria-label="Painel do Cliente de homologação">
    <div className="panel-top">
      <div>
        <p className="eyebrow green">PAINEL DO CLIENTE • HOMOLOGAÇÃO</p>
        <h3>Pendências e comunicação com o técnico</h3>
        <p className="muted">Somente registros fictícios da nova base isolada. Sem integração com a Central Online atual.</p>
      </div>
      <button type="button" className="secondary-button" disabled={busy} onClick={()=>void run(refresh)}>Atualizar painel</button>
    </div>
    {notice&&<p className="auth-message" role="status">{notice}</p>}
    <div className="portal-stats">
      {(['aberta','rejeitada','correcao_informada','validada'] as const).map(status=>
        <div className="portal-stat" key={status}><strong>{dashboard?.counts.find(i=>i.status===status)?.total||0}</strong>
          <span>{label[status]}</span></div>)}
    </div>
    <h4>Não conformidades em destaque ({pending.length} exibidas)</h4>
    {pending.length===0&&<p className="empty">Nenhuma pendência fictícia nesta empresa.</p>}
    <div className="nc-list">{pending.map(nc=><article className="nc-card" key={nc.id}>
      <div className="portal-nc-head"><strong>{nc.short_title||nc.description}</strong>
        <span className="status">{label[nc.status]||nc.status}</span></div>
      {nc.short_title&&<p className="muted">{nc.description}</p>}
      <p className="muted">Prioridade por risco: {nc.probability*nc.severity} (probabilidade {nc.probability} × severidade {nc.severity})</p>
      <button type="button" className="secondary-button" disabled={busy}
        onClick={()=>void run(()=>history(nc.id))}>
        {activeNc===nc.id?'Fechar histórico':'Histórico e tratativa'}
      </button>
      {activeNc===nc.id&&<div className="inspection-detail">
        <ol className="auth-timeline">{ncHistory.map(event=><li key={event.id}>
          <strong>{event.kind.replaceAll('_',' ')}</strong>
          {event.message&&<p>{event.message}</p>}
          <small>{new Date(event.created_at).toLocaleString('pt-BR')}</small>
        </li>)}</ol>
        <label>Comentário da tratativa
          <textarea rows={2} maxLength={1200} value={comment} onChange={e=>setComment(e.target.value)}/>
        </label>
        {['aberta','rejeitada'].includes(nc.status)&&<button type="button" className="primary-button" disabled={busy}
          onClick={()=>void run(()=>correction(nc))}>Registrar correção</button>}
        {nc.status==='correcao_informada'&&staff&&<div className="auth-actions">
          <button type="button" className="primary-button" disabled={busy}
            onClick={()=>void run(()=>correction(nc,true))}>Validar correção</button>
          <button type="button" className="secondary-button" disabled={busy||!comment.trim()}
            onClick={()=>void run(()=>correction(nc,false))}>Rejeitar com motivo</button>
        </div>}
        {nc.status==='correcao_informada'&&!staff&&<p className="muted">Aguardando validação técnica.</p>}
        <p className="muted">Fotos e evidências ainda não estão disponíveis neste piloto. Nenhuma foto é alterada no Drive.</p>
      </div>}
    </article>)}</div>
    <div className="auth-divider"/>
    <h4>Solicitar apoio / conversar com a Auditar</h4>
    <form className="auth-form" onSubmit={e=>{e.preventDefault();void run(create);}}>
      <label>Assunto<input required maxLength={160} value={subject} onChange={e=>setSubject(e.target.value)}
        placeholder="Ex.: Dúvida sobre uma pendência"/></label>
      <label>Mensagem<textarea required maxLength={1500} rows={2} value={initial}
        onChange={e=>setInitial(e.target.value)}/></label>
      <button type="submit" className="primary-button" disabled={busy}>Abrir solicitação de teste</button>
    </form>
    <div className="inspection-list">{threads.map(thread=><article className="inspection-item" key={thread.id}>
      <div><strong>{thread.subject}</strong><small>{thread.status} · {new Date(thread.updated_at).toLocaleString('pt-BR')}</small></div>
      <button type="button" className="secondary-button" disabled={busy}
        onClick={()=>void run(()=>selected?.item.id===thread.id?Promise.resolve(setSelected(null)):open(thread.id))}>
        {selected?.item.id===thread.id?'Fechar':'Conversar'}
      </button>
    </article>)}</div>
    {threads.length===0&&<p className="empty">Nenhuma solicitação de apoio nesta conta de teste.</p>}
    {selected&&<div className="inspection-detail">
      <h4>{selected.item.subject} · {selected.item.status}</h4>
      <ol className="auth-timeline">{selected.messages.map(message=><li key={message.id}>
        <strong>{message.created_by===session.user.id?'Você':staff?'Outro participante':'Equipe Auditar'} · {message.kind.replaceAll('_',' ')}</strong>
        <p>{message.message}</p>
        <small>{new Date(message.created_at).toLocaleString('pt-BR')}</small>
      </li>)}</ol>
      {selected.item.status==='aberta'&&<form className="auth-form" onSubmit={e=>{e.preventDefault();void run(reply);}}>
        <label>Responder<textarea required maxLength={1500} rows={2} value={replyText}
          onChange={e=>setReplyText(e.target.value)}/></label>
        <button type="submit" className="primary-button" disabled={busy}>Enviar resposta</button>
      </form>}
      <label>Observação do andamento
        <textarea maxLength={1500} rows={2} value={comment} onChange={e=>setComment(e.target.value)}/>
      </label>
      {selected.item.status==='aberta'&&staff&&<button type="button" className="secondary-button" disabled={busy}
        onClick={()=>void run(()=>status('close'))}>Encerrar solicitação</button>}
      {selected.item.status==='encerrada'&&<button type="button" className="secondary-button" disabled={busy}
        onClick={()=>void run(()=>status('reopen'))}>Reabrir solicitação</button>}
    </div>}
    <div className="auth-divider"/>
    <h4>Últimas tratativas de NCs</h4>
    <ol className="auth-timeline">{(dashboard?.timeline||[]).map(event=><li key={event.id}>
      <strong>{event.short_title||'NC registrada'}: {event.kind.replaceAll('_',' ')}</strong>
      {event.message&&<p>{event.message}</p>}
      <small>{new Date(event.created_at).toLocaleString('pt-BR')}</small>
    </li>)}</ol>
  </section>;
}
