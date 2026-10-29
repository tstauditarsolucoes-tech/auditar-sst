import {useEffect,useState} from 'react';
type Role='adm'|'gestor'|'tecnico'|'cliente';
type Session={role:Role;companyId:string;csrfToken:string;user:{id:string}};
type Mandate={id:string;name:string;starts_on:string;ends_on:string;election_on:string|null;status:'preparacao'|'ativo'|'encerrado';revision:number};
type Member={id:string;display_name:string;representation:string;seat:string};
type Meeting={id:string;title:string;scheduled_at:string;summary:string;status:'planejada'|'realizada'|'cancelada';revision:number;created_by:string};
type Entry={id:string;kind:string;message:string;created_at:string};
type Detail={mandate:Mandate;members:Member[];meetings:Meeting[];events:Entry[]};
const statusNames={preparacao:'Preparação',ativo:'Em andamento',encerrado:'Encerrado'};
const representNames={empregados:'Representante dos empregados',empregador:'Representante do empregador',designado:'Designado'};
const seatNames={titular:'Titular',suplente:'Suplente',designado:'Designado'};
async function request<T>(path:string,method:'GET'|'POST'='GET',body?:object,csrf?:string):Promise<T>{
 const response=await fetch('/api/v1/'+path,{
  method,credentials:'same-origin',cache:'no-store',
  headers:{...(body?{'Content-Type':'application/json'}:{}),...(csrf?{'X-CSRF-Token':csrf}:{})},
  body:body?JSON.stringify(body):undefined,
 });
 const data:unknown=await response.json().catch(()=>null);
 if(!response.ok){
  const code=data&&typeof data==='object'&&'code' in data?String((data as {code:string}).code):String(response.status);
  const messages:Record<string,string>={
   FORBIDDEN:'Sem permissão para esta ação.',NOT_FOUND:'Registro indisponível nesta empresa.',
   INVALID_STATE:'Mandato ou reunião já encerrados.',INVALID_INPUT:'Confira as informações obrigatórias.',
   STALE_REVISION:'O registro foi alterado. Reabra e confira.',IDEMPOTENCY_CONFLICT:'Código de reenvio já utilizado.',
   UNAUTHENTICATED:'Sessão indisponível ou expirada.',
  };
  throw new Error(messages[code]||'Falha ao registrar: '+code);
 }
 return data as T;
}
function localDateTime(v:string){const d=new Date(v);
 return new Date(d.getTime()-d.getTimezoneOffset()*60000).toISOString().slice(0,16);}
export function CipaPilot({session}:{session:Session}){
 const manager=session.role==='adm'||session.role==='gestor';
 const [mandates,setMandates]=useState<Mandate[]>([]);
 const [selected,setSelected]=useState<Detail|null>(null);
 const [name,setName]=useState('');
 const [start,setStart]=useState('');
 const [end,setEnd]=useState('');
 const [election,setElection]=useState('');
 const [mandateKey,setMandateKey]=useState(()=>crypto.randomUUID());
 const [memberName,setMemberName]=useState('');
 const [representation,setRepresentation]=useState<'empregados'|'empregador'|'designado'>('empregados');
 const [seat,setSeat]=useState<'titular'|'suplente'|'designado'>('titular');
 const [memberKey,setMemberKey]=useState(()=>crypto.randomUUID());
 const [meetingTitle,setMeetingTitle]=useState('');
 const [meetingDate,setMeetingDate]=useState('');
 const [meetingAgenda,setMeetingAgenda]=useState('');
 const [meetingKey,setMeetingKey]=useState(()=>crypto.randomUUID());
 const [decisionId,setDecisionId]=useState<string|null>(null);
 const [summary,setSummary]=useState('');
 const [discussed,setDiscussed]=useState(''),[decisions,setDecisions]=useState(''),[responsible,setResponsible]=useState(''),[followUp,setFollowUp]=useState('');
 const [closeNote,setCloseNote]=useState('');
 const [busy,setBusy]=useState(false);
 const [notice,setNotice]=useState('');
 async function refresh(){
  const data=await request<{items:Mandate[]}>('cipa/mandates');
  setMandates(data.items);
 }
 async function open(id:string){setSelected(await request<Detail>('cipa/mandates/'+id));}
 useEffect(()=>{
  let mounted=true;
  request<{items:Mandate[]}>('cipa/mandates')
   .then(r=>{if(mounted)setMandates(r.items);})
   .catch(()=>{if(mounted)setNotice('CIPA ainda não está disponível nesta homologação.');});
  return ()=>{mounted=false;};
 },[session.companyId]);
 async function run(callback:()=>Promise<void>){
  setBusy(true);setNotice('');
  try{await callback();}
  catch(e){setNotice(e instanceof Error?e.message:'Erro inesperado de homologação.');}
  finally{setBusy(false);}
 }
 async function create(){
  const result=await request<{item:Mandate}>('cipa/mandates','POST',{
   name,startsOn:start,endsOn:end,electionOn:election||null,clientRequestId:mandateKey,
  },session.csrfToken);
  setName('');setStart('');setEnd('');setElection('');setMandateKey(crypto.randomUUID());
  await refresh();await open(result.item.id);
  setNotice('Mandato fictício criado apenas para homologação.');
 }
 async function addMember(){
  if(!selected)return;
  await request('cipa/mandates/'+selected.mandate.id+'/members','POST',{
   displayName:memberName,representation,seat,clientRequestId:memberKey,
  },session.csrfToken);
  setMemberName('');setMemberKey(crypto.randomUUID());
  await open(selected.mandate.id);setNotice('Representante fictício registrado.');
 }
 async function addMeeting(){
  if(!selected)return;
  await request('cipa/mandates/'+selected.mandate.id+'/meetings','POST',{
   title:meetingTitle,scheduledAt:new Date(meetingDate).toISOString(),agenda:meetingAgenda,clientRequestId:meetingKey,
  },session.csrfToken);
  setMeetingTitle('');setMeetingDate('');setMeetingAgenda('');setMeetingKey(crypto.randomUUID());
  await open(selected.mandate.id);setNotice('Reunião fictícia agendada.');
 }
 async function decideMeeting(id:string,status:'realizada'|'cancelada',revision:number){
  if(!selected)return;
  await request('cipa/meetings/'+id+'/status','POST',{
   status,summary,expectedRevision:revision,
  },session.csrfToken);
  setSummary('');setDiscussed('');setDecisions('');setResponsible('');setFollowUp('');setDecisionId(null);
  await open(selected.mandate.id);setNotice('Andamento da reunião registrado.');
 }
 async function changeMandate(status:'ativo'|'encerrado'){
  if(!selected)return;
  await request('cipa/mandates/'+selected.mandate.id+'/status','POST',{
   status,expectedRevision:selected.mandate.revision,note:closeNote,
  },session.csrfToken);
  setCloseNote('');await refresh();await open(selected.mandate.id);
  setNotice('Status administrativo do mandato atualizado.');
 }
 return <section className="panel">
  <div className="panel-top"><div>
   <p className="eyebrow green">CIPA · HOMOLOGAÇÃO PRIVADA</p>
   <h2>Mandatos, composição e reuniões</h2>
   <p className="muted">Controle administrativo interno por empresa, com histórico das atualizações.</p>
  </div><span className="tag">{mandates.length} mandato(s)</span></div>
  <p className="privacy-warning">Use somente dados fictícios. Este piloto não substitui eleição, atas assinadas, dimensionamento ou documentos exigidos pela NR-5.</p>
  {notice&&<p className="auth-message" role="status">{notice}</p>}
  <form className="auth-form" onSubmit={e=>{e.preventDefault();void run(create);}}>
   <h3>Novo mandato de teste</h3>
   <label>Identificação<input required maxLength={180} value={name} onChange={e=>setName(e.target.value)}
     placeholder="Ex.: CIPA 2027 (fictícia)"/></label>
   <label>Início<input required type="date" value={start} onChange={e=>setStart(e.target.value)}/></label>
   <label>Término<input required type="date" value={end} min={start||undefined} onChange={e=>setEnd(e.target.value)}/></label>
   <label>Data de eleição (opcional)<input type="date" value={election} onChange={e=>setElection(e.target.value)}/></label>
   <button className="primary-button" type="submit" disabled={busy||!name.trim()||!start||!end}>Criar mandato fictício</button>
  </form>
  <div className="auth-divider"/>
  <div className="panel-top"><h3>Mandatos da empresa ativa</h3>
   <button className="secondary-button" disabled={busy} onClick={()=>void run(refresh)}>Atualizar</button></div>
  {!mandates.length&&<p className="empty">Nenhum mandato fictício cadastrado.</p>}
  <div className="nc-list">{mandates.map(m=><article className="nc-card" key={m.id}>
   <h3>{m.name}</h3><p className="muted">{new Date(m.starts_on).toLocaleDateString('pt-BR',{timeZone:'UTC'})} a {new Date(m.ends_on).toLocaleDateString('pt-BR',{timeZone:'UTC'})} · {statusNames[m.status]}</p>
   <button className="secondary-button" disabled={busy} onClick={()=>void run(()=>open(m.id))}>Composição e reuniões</button>
  </article>)}</div>
  {selected&&<div className="auth-form">
   <div className="panel-top"><h3>{selected.mandate.name}</h3>
    <button className="secondary-button" disabled={busy} onClick={()=>setSelected(null)}>Fechar</button></div>
   <p className="muted">{statusNames[selected.mandate.status]} · Revisão {selected.mandate.revision} · Controle administrativo, sem validade eleitoral presumida.</p>
   {manager&&selected.mandate.status!=='encerrado'&&<div className="auth-actions">
    {selected.mandate.status==='preparacao'&&
     <button className="secondary-button" disabled={busy} onClick={()=>void run(()=>changeMandate('ativo'))}>Marcar em andamento</button>}
    {selected.mandate.status==='ativo'&&<>
     <label>Motivo do encerramento<textarea rows={2} maxLength={1200} value={closeNote} onChange={e=>setCloseNote(e.target.value)}/></label>
     <button className="secondary-button" disabled={busy||!closeNote.trim()} onClick={()=>void run(()=>changeMandate('encerrado'))}>Encerrar administrativamente</button>
    </>}
   </div>}
   <h4>Composição registrada</h4>
   {!selected.members.length&&<p className="muted">Nenhum representante de teste.</p>}
   <div className="nc-list">{selected.members.map(m=><div className="nc-card" key={m.id}>
    <strong>{m.display_name}</strong>
    <p className="muted">{representNames[m.representation as keyof typeof representNames]} · {seatNames[m.seat as keyof typeof seatNames]}</p>
   </div>)}</div>
   {selected.mandate.status!=='encerrado'&&<form className="auth-form" onSubmit={e=>{e.preventDefault();void run(addMember);}}>
    <h4>Adicionar representante fictício</h4>
    <label>Identificação<input value={memberName} maxLength={180} required onChange={e=>setMemberName(e.target.value)}/></label>
    <label>Representação<select value={representation} onChange={e=>{
     const v=e.target.value as typeof representation;setRepresentation(v);setSeat(v==='designado'?'designado':'titular');
    }}>
     <option value="empregados">Empregados</option><option value="empregador">Empregador</option>
     <option value="designado">Designado</option>
    </select></label>
    {representation!=='designado'&&<label>Condição<select value={seat} onChange={e=>setSeat(e.target.value as typeof seat)}>
     <option value="titular">Titular</option><option value="suplente">Suplente</option>
    </select></label>}
    <button type="submit" className="secondary-button" disabled={busy||!memberName.trim()}>Adicionar</button>
   </form>}
   <h4>Reuniões</h4>
   {!selected.meetings.length&&<p className="muted">Nenhuma reunião fictícia.</p>}
   <div className="nc-list">{selected.meetings.map(m=><article key={m.id} className="nc-card">
    <strong>{m.title}</strong>
    <p className="muted">{new Date(m.scheduled_at).toLocaleString('pt-BR')} · {m.status}</p>
    {m.summary&&<p>{m.summary}</p>}
    {m.status==='planejada'&&selected.mandate.status!=='encerrado'&&(manager||session.user.id===m.created_by)&&<>
     <button className="secondary-button" disabled={busy} onClick={()=>{
      setDecisionId(decisionId===m.id?null:m.id);setSummary('');setDiscussed('');setDecisions('');setResponsible('');setFollowUp('');
     }}>Registrar resultado</button>
     {decisionId===m.id&&<div className="auth-form">
      <p><strong>Registro guiado:</strong> descreva o que foi discutido e decidido. O texto será uma minuta para revisão, não uma ata assinada.</p>
      <label>Assuntos discutidos<textarea maxLength={950} rows={2} value={discussed} onChange={e=>setDiscussed(e.target.value)} placeholder="Ex.: avaliação das condições observadas no setor" /></label>
      <label>Decisões e encaminhamentos<textarea maxLength={950} rows={2} value={decisions} onChange={e=>setDecisions(e.target.value)} placeholder="Ex.: solicitar avaliação técnica do equipamento" /></label>
      <label>Quem ficou responsável?<input maxLength={250} value={responsible} onChange={e=>setResponsible(e.target.value)} placeholder="Ex.: responsável da manutenção" /></label>
      <label>Prazo ou próxima verificação<input maxLength={150} value={followUp} onChange={e=>setFollowUp(e.target.value)} placeholder="Ex.: próxima reunião / data combinada" /></label>
      <button type="button" className="secondary-button" disabled={busy||!discussed.trim()||!decisions.trim()} onClick={()=>{
        const text=['MINUTA DE REUNIÃO — REVISÃO OBRIGATÓRIA',
          'Pauta prevista: '+(m.summary||'não informada'),
          'Assuntos discutidos: '+discussed.trim(),
          'Decisões e encaminhamentos: '+decisions.trim(),
          'Responsável(is): '+(responsible.trim()||'a definir'),
          'Acompanhamento/prazo: '+(followUp.trim()||'a definir'),
          'Atenção: esta minuta não comprova presença, aprovação ou assinatura.'].join('\\n');
        if(text.length>4000){setNotice('Minuta muito longa. Resuma os campos antes de gerar.');return;}
        setSummary(text);
      }}>Montar minuta para revisão</button>
      <label>Resumo da reunião ou motivo<textarea maxLength={4000} rows={3} required
       value={summary} onChange={e=>setSummary(e.target.value)}/></label>
      <div className="auth-actions">
       <button className="primary-button" disabled={busy||!summary.trim()}
        onClick={()=>void run(()=>decideMeeting(m.id,'realizada',m.revision))}>Registrar realizada</button>
       <button className="secondary-button" disabled={busy||!summary.trim()}
        onClick={()=>void run(()=>decideMeeting(m.id,'cancelada',m.revision))}>Cancelar</button>
      </div>
     </div>}
    </>}
   </article>)}</div>
   {selected.mandate.status!=='encerrado'&&<form className="auth-form" onSubmit={e=>{e.preventDefault();void run(addMeeting);}}>
    <h4>Agendar reunião fictícia</h4>
    <label>Assunto<input required maxLength={200} value={meetingTitle} onChange={e=>setMeetingTitle(e.target.value)}/></label>
    <label>Data e horário<input type="datetime-local" required value={meetingDate}
     onChange={e=>setMeetingDate(e.target.value)}/></label>
    <label>Pauta da reunião (opcional)<textarea rows={4} maxLength={1800} value={meetingAgenda} onChange={e=>setMeetingAgenda(e.target.value)} placeholder="Quais assuntos precisam ser tratados?" /></label>
    <button type="button" className="secondary-button" onClick={()=>setMeetingAgenda('1. Verificação das pendências do mês.\\n2. Situações observadas pelos membros.\\n3. Acompanhamento das ações e responsáveis.\\n4. Próxima reunião e encaminhamentos.')}>Usar pauta sugerida</button>
    <button className="secondary-button" type="submit" disabled={busy||!meetingTitle.trim()||!meetingDate}>Agendar</button>
   </form>}
   <h4>Linha do tempo</h4>
   <ol className="auth-timeline">{selected.events.map(e=><li key={e.id}>
    <strong>{e.kind.replaceAll('_',' ')}</strong>{e.message&&<p>{e.message}</p>}
    <small>{new Date(e.created_at).toLocaleString('pt-BR')}</small>
   </li>)}</ol>
  </div>}
 </section>;
}
