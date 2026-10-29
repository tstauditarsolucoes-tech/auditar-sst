import {useEffect,useRef,useState,type FormEvent} from 'react';
import {portalRequest,PortalError,statusLabel,entryLabel,shortDate,localTime,type CipaSession,type Mandate,type PortalWorkspace} from './cipaPortalClient';
import './cipaPortal.css';
const base='cipa-portal/';
export function CipaMemberPortal(){
  const [session,setSession]=useState<CipaSession|null>(null),[checking,setChecking]=useState(true);
  const [editingPassword,setEditingPassword]=useState(false);
  const [companyId,setCompanyId]=useState(new URLSearchParams(location.search).get('empresa')||'');
  const [email,setEmail]=useState(''),[password,setPassword]=useState(''),[nextPassword,setNextPassword]=useState(''),[confirm,setConfirm]=useState('');
  const [mandates,setMandates]=useState<Mandate[]>([]),[selected,setSelected]=useState(''),[data,setData]=useState<PortalWorkspace|null>(null);
  const [busy,setBusy]=useState(false),[notice,setNotice]=useState(''),[tab,setTab]=useState<'acoes'|'reunioes'|'mural'|'historico'>('acoes');
  const [actionId,setActionId]=useState(''),[actionKind,setActionKind]=useState('andamento'),[note,setNote]=useState(''),[suggestion,setSuggestion]=useState('');
  const [observedLocation,setObservedLocation]=useState(''),[observation,setObservation]=useState('');
  const pending=useRef<{signature:string;id:string}|null>(null),generation=useRef(0);
  function clear(){generation.current++;setSession(null);setEditingPassword(false);setData(null);setMandates([]);setSelected('');setPassword('');setNextPassword('');setConfirm('');setNote('');setSuggestion('');pending.current=null;}
  function failure(e:unknown){if(e instanceof PortalError&&e.code==='UNAUTHENTICATED')clear();setNotice(e instanceof Error?e.message:'Não foi possível conectar.');}
  async function loadList(s:CipaSession){const n=++generation.current;const r=await portalRequest<{items:Mandate[]}>(base+'mandates');if(n!==generation.current)return;
    setMandates(r.items);setSelected(r.items[0]?.id||'');if(!r.items.length)setNotice('Nenhum mandato liberado para sua conta.');}
  useEffect(()=>{let live=true;portalRequest<CipaSession>(base+'auth/session').then(s=>{if(live)setSession(s);}).catch(e=>{if(live&&!(e instanceof PortalError&&e.code==='UNAUTHENTICATED'))failure(e);}).finally(()=>{if(live)setChecking(false);});return()=>{live=false;generation.current++;};},[]);
  useEffect(()=>{if(session&&!session.mustChangePassword)void loadList(session).catch(failure);},[session?.companyId,session?.mustChangePassword]);
  useEffect(()=>{setData(null);setActionId('');setNote('');if(!selected||!session||session.mustChangePassword)return;const abort=new AbortController();
    portalRequest<PortalWorkspace>(base+'mandates/'+selected,undefined,undefined,abort.signal).then(setData).catch(e=>{if(!abort.signal.aborted)failure(e);});return()=>abort.abort();},[selected,session?.companyId,session?.mustChangePassword]);
  async function refresh(){if(!selected)return;const n=generation.current;const r=await portalRequest<PortalWorkspace>(base+'mandates/'+selected);if(n===generation.current)setData(r);}
  async function run(fn:()=>Promise<void>){if(busy)return;setBusy(true);setNotice('');try{await fn();}catch(e){failure(e);}finally{setBusy(false);}}
  async function login(e:FormEvent){e.preventDefault();await run(async()=>{const s=await portalRequest<CipaSession>(base+'auth/login',{companyId,email,password});setPassword('');setSession(s);});}
  async function changePassword(e:FormEvent){e.preventDefault();if(nextPassword!==confirm){setNotice('A confirmação da nova senha não confere.');return;}
    await run(async()=>{const s=await portalRequest<CipaSession>(base+'auth/password',{currentPassword:password,password:nextPassword},session?.csrfToken);setPassword('');setNextPassword('');setConfirm('');setEditingPassword(false);setSession(s);setNotice('Senha alterada. As outras sessões foram encerradas.');});}
  async function post(path:string,payload:object){const signature=JSON.stringify([path,payload]);if(pending.current?.signature!==signature)pending.current={signature,id:crypto.randomUUID()};
    await portalRequest(base+path,{...payload,clientRequestId:pending.current.id},session?.csrfToken);pending.current=null;setNotice('Registro salvo.');setNote('');setActionId('');
    try{await refresh();}catch{setNotice('Registro salvo, mas a lista não atualizou. Use Atualizar; não é preciso reenviar.');}}
  const [guideOpen,setGuideOpen]=useState(false);
  const calendarParts=new Intl.DateTimeFormat('en-US',{year:'numeric',month:'2-digit',timeZone:'America/Fortaleza'}).formatToParts(new Date());
  const period=(calendarParts.find(x=>x.type==='year')?.value||'')+'-'+(calendarParts.find(x=>x.type==='month')?.value||'');
  const checklistState=new Map((data?.checklist||[]).filter(e=>e.message.startsWith(period+'|')).map(e=>[e.message.split('|')[1],e.message.endsWith('|feito')]));
  const monthlyChecklist=[
    {key:'verificar_ambiente',title:'Verificar se existem situações inseguras no setor',hint:'Observe passagens obstruídas, máquinas sem proteção ou extintores com acesso bloqueado. Não se exponha ao risco.'},
    {key:'acompanhar_acoes',title:'Acompanhar as ações atribuídas',hint:'Confira os prazos e use “Preciso de apoio” se tiver dúvidas.'},
    {key:'consultar_reuniao',title:'Conferir a próxima reunião',hint:'Leia a convocação e anote assuntos para levar à reunião.'},
    {key:'sugerir_melhoria',title:'Compartilhar uma sugestão de prevenção',hint:'Descreva uma melhoria possível. Não é necessário citar normas técnicas.'}
  ];
    const closed=data?.mandate.status==='encerrado';
  const chosen=data?.actions.find(a=>a.id===actionId);
  const notices=data?.entries.filter(e=>e.kind==='aviso')||[];
  return <main className="cipa-portal"><header className="cipa-hero"><div className="cipa-brand">AUDITAR <span>SOLUÇÕES</span></div><p>Participação que vira prevenção</p><h1>Portal do membro da CIPA</h1><p>Suas ações, reuniões e avisos em um só lugar.</p></header>
    <aside className="cipa-environment">Homologação privada • dados do novo servidor. Não sincronizado com o aplicativo atual.</aside>
    <div className="cipa-notice" role="status" aria-live="polite">{notice}</div>
    {checking?<p>Verificando acesso…</p>:!session?<section className="cipa-box cipa-login"><h2>Entrar no seu portal</h2><p>A gestão fornece o endereço da empresa e seu acesso individual. Não há cadastro público.</p><form onSubmit={login}>
      <label>Código da empresa<input required value={companyId} onChange={e=>setCompanyId(e.target.value)} maxLength={36} autoComplete="off" placeholder="Código recebido com o link de acesso" /></label>
      <label>E-mail<input required type="email" value={email} onChange={e=>setEmail(e.target.value)} maxLength={254} autoComplete="username" /></label>
      <label>Senha<input required type="password" value={password} onChange={e=>setPassword(e.target.value)} maxLength={256} autoComplete="current-password" /></label>
      <button disabled={busy}>{busy?'Entrando…':'Entrar com segurança'}</button></form><p>Esqueceu a senha? Peça à gestão da sua empresa para emitir uma senha temporária. Não envie sua senha atual.</p></section>:<>
      <div className="cipa-toolbar"><div><strong>Olá, {session.name}</strong><small>Empresa: {session.companyId}</small></div>{!session.mustChangePassword&&<button className="secondary" disabled={busy} onClick={()=>setEditingPassword(true)}>Alterar minha senha</button>}<button className="secondary" disabled={busy} onClick={()=>void run(async()=>{await portalRequest(base+'auth/logout',{},session.csrfToken);clear();setNotice('Sessão encerrada.');})}>Sair</button></div>
      {session.mustChangePassword||editingPassword?<section className="cipa-box cipa-login"><h2>Defina sua senha pessoal</h2><p>{session.mustChangePassword?'A senha temporária não libera os dados antes desta troca.':'Informe sua senha atual. A alteração encerra as outras sessões da sua conta.'}</p><form onSubmit={changePassword}>
        <label>{session.mustChangePassword?'Senha temporária':'Senha atual'}<input required type="password" value={password} onChange={e=>setPassword(e.target.value)} maxLength={256} autoComplete="current-password" /></label>
        <label>Nova senha (mínimo de 12 caracteres)<input required type="password" minLength={12} maxLength={256} value={nextPassword} onChange={e=>setNextPassword(e.target.value)} autoComplete="new-password" /></label>
        <label>Repita a nova senha<input required type="password" minLength={12} maxLength={256} value={confirm} onChange={e=>setConfirm(e.target.value)} autoComplete="new-password" /></label><button disabled={busy}>Salvar minha senha</button>{!session.mustChangePassword&&<button className="secondary" type="button" disabled={busy} onClick={()=>{setEditingPassword(false);setPassword('');setNextPassword('');setConfirm('');}}>Cancelar</button>}</form></section>:<>
        <div className="cipa-toolbar"><label>Mandato<select value={selected} onChange={e=>{generation.current++;setSelected(e.target.value);}} disabled={busy}><option value="">Selecione</option>{mandates.map(m=><option key={m.id} value={m.id}>{m.name} · {statusLabel[m.status]||m.status}</option>)}</select></label><button className="secondary" disabled={busy||!selected} onClick={()=>void run(refresh)}>Atualizar</button></div>
        {selected&&!data?<p>Carregando mandato…</p>:data&&<>
          {closed&&<p className="cipa-environment">Mandato encerrado: os registros permanecem disponíveis para consulta.</p>}
          <section className="cipa-box" aria-label="Guia rápido para participar da CIPA">
            <h2>Por onde começar?</h2>
            <p>Você não precisa conhecer as normas de segurança para participar. Escolha o que deseja fazer; a equipe técnica orienta e valida as ações.</p>
            <div className="cipa-tabs">
              <button type="button" className="secondary" onClick={()=>setTab('acoes')}>Ver minhas tarefas</button>
              <button type="button" className="secondary" onClick={()=>setTab('reunioes')}>Ver próxima reunião</button>
              <button type="button" className="secondary" onClick={()=>setTab('mural')}>Sugerir melhoria</button>
            </div>
            <p><strong>Como funciona:</strong> 1. Leia sua tarefa. 2. Informe o andamento ou peça ajuda. 3. Envie para validação quando terminar. A conclusão só é confirmada pela equipe responsável.</p>
          </section>
          <section className="cipa-box" aria-label="Checklist de orientação mensal da CIPA">
            <h2>Meu roteiro do mês</h2>
            <p>Competência {period.slice(5,7)}/{period.slice(0,4)} · marque cada etapa que realizou. O registro fica vinculado à sua conta e ao mandato. Não substitui inspeção técnica, ata ou registro formal de atividade.</p>
            <p><strong>{monthlyChecklist.filter(item=>checklistState.get(item.key)===true).length} de {monthlyChecklist.length} etapas acompanhadas</strong></p>
            <ul className="cipa-monthly-list">{monthlyChecklist.map(item=><li key={item.key}>
              <label><input type="checkbox" checked={checklistState.get(item.key)===true} disabled={busy||closed}
                onChange={e=>void run(()=>post('mandates/'+selected+'/entries',{kind:'checklist',period,itemKey:item.key,checked:e.target.checked}))}/>
                <span><strong>{item.title}</strong><small>{item.hint}</small></span>
              </label>
            </li>)}</ul>
            <button type="button" className="secondary" aria-expanded={guideOpen} onClick={()=>setGuideOpen(v=>!v)}>{guideOpen?'Fechar orientações':'Aprender: como participar da CIPA'}</button>
            {guideOpen&&<div><h3>Orientações para começar</h3><p><strong>Observe sem se arriscar:</strong> não toque em instalações, máquinas ou equipamentos para verificar problemas.</p><p><strong>Comunique:</strong> relate o local e o que viu usando palavras simples. Evite nomes e informações pessoais desnecessárias.</p><p><strong>Peça apoio:</strong> a equipe técnica avalia os riscos e orienta as medidas adequadas.</p><p><strong>Reuniões:</strong> leia as convocações e leve sugestões. Confirmar leitura não significa presença ou assinatura da ata.</p></div>}
          </section>
          <div className="cipa-metrics"><div><strong>{data.counts.pending}</strong><span>Minhas ações pendentes</span></div><div><strong>{data.counts.reviewing}</strong><span>Em validação</span></div><div><strong>{data.counts.scheduled}</strong><span>Reuniões agendadas</span></div></div>
          <nav className="cipa-tabs" aria-label="Seções do portal">{(['acoes','reunioes','mural','historico'] as const).map((t,i)=><button key={t} className={tab===t?'selected':'secondary'} aria-pressed={tab===t} onClick={()=>setTab(t)}>{['Minhas ações','Reuniões','Avisos e sugestões','Meu histórico'][i]}</button>)}</nav>
          {tab==='acoes'&&<section><h2>O que precisa da sua participação</h2><p>Você informa o andamento. A equipe Auditar valida a conclusão.</p><div className="cipa-cards">{data.actions.map(a=><article className="cipa-box" key={a.id}><div className="cipa-tags"><span>{statusLabel[a.status]}</span><span>Prioridade {a.priority}</span></div><h3>{a.title}</h3><p className="cipa-pre">{a.description}</p><p>Prazo: <strong>{shortDate(a.due_on)}</strong></p><button className="secondary" disabled={busy||closed||a.status==='concluida'} onClick={()=>{setActionId(a.id);setActionKind(a.status==='aberta'||a.status==='aguardando_validacao'?'andamento':'aguardando_validacao');setNote('');}}>Atualizar / pedir apoio</button></article>)}</div>{!data.actions.length&&<p>Você não tem tarefas atribuídas agora. Consulte as reuniões ou envie uma sugestão de prevenção.</p>}
            {chosen&&!closed&&chosen.status!=='concluida'&&<form className="cipa-box" onSubmit={e=>{e.preventDefault();void run(()=>actionKind==='apoio'?post('mandates/'+selected+'/entries',{kind:'apoio',actionId:chosen.id,message:note}):post('actions/'+chosen.id+'/status',{status:actionKind,message:note,expectedRevision:chosen.revision}));}}><h3>Atualizar: {chosen.title}</h3><label>O que deseja registrar?<select value={actionKind} onChange={e=>setActionKind(e.target.value)}><option value="apoio">Preciso de apoio</option>{chosen.status!=='andamento'&&<option value="andamento">Em andamento</option>}{chosen.status!=='aguardando_validacao'&&<option value="aguardando_validacao">Enviei para validação da conclusão</option>}</select></label><label>Conte com suas palavras o que aconteceu ou qual ajuda precisa<textarea required maxLength={1900} rows={3} value={note} onChange={e=>setNote(e.target.value)} placeholder="Exemplo: Preciso de orientação para verificar a proteção da máquina." /></label><p>Se precisar de orientação, escolha “Preciso de apoio”. Não é necessário conhecer o número da NR.</p><button disabled={busy}>Salvar atualização</button></form>}
          </section>}
          {tab==='reunioes'&&<section><h2>Reuniões do mandato</h2><p>Confirmar ciência significa que você leu a convocação. Não substitui presença ou assinatura.</p>{data.meetings.map(m=><article className="cipa-box" key={m.id}><span className="cipa-tag">{statusLabel[m.status]}</span><h3>{m.title}</h3><p>{localTime(m.scheduled_at)}</p><p className="cipa-pre">{m.summary}</p>{data.entries.some(e=>e.kind==='ciencia_reuniao'&&e.meeting_id===m.id)?<p>Ciência registrada no seu histórico.</p>:<button className="secondary" disabled={busy||closed||m.status==='cancelada'} onClick={()=>void run(()=>post('mandates/'+selected+'/entries',{kind:'ciencia_reuniao',meetingId:m.id,message:'Li a convocação.'}))}>Confirmar que li</button>}</article>)}{!data.meetings.length&&<p>Nenhuma reunião cadastrada.</p>}</section>}
          {tab==='mural'&&<section><h2>Avisos da gestão</h2>{notices.map(e=><article key={e.id} className="cipa-box"><small>{localTime(e.created_at)}</small><p className="cipa-pre">{e.message}</p></article>)}{!notices.length&&<p>Nenhum aviso publicado neste mandato.</p>}
            <form className="cipa-box" onSubmit={e=>{e.preventDefault();void run(async()=>{await post('mandates/'+selected+'/entries',{kind:'observacao',location:observedLocation,message:observation});setObservation('');setObservedLocation('');});}}>
              <h3>Registrar uma situação observada</h3>
              <p>Descreva algo que precisa da atenção da equipe. Não toque em instalações ou máquinas e não se aproxime de riscos para registrar.</p>
              <label>Local observado<input required maxLength={140} value={observedLocation} onChange={e=>setObservedLocation(e.target.value)} disabled={closed} placeholder="Exemplo: corredor da expedição" /></label>
              <label>O que você observou?<textarea required rows={3} maxLength={1600} value={observation} onChange={e=>setObservation(e.target.value)} disabled={closed} placeholder="Exemplo: corredor com caixas impedindo a passagem." /></label>
              <p>O técnico avaliará a situação. Este registro não é automaticamente uma não conformidade. Fotos ainda não estão habilitadas neste piloto.</p>
              <button disabled={busy||closed}>Enviar observação</button>
            </form>
            <form className="cipa-box" onSubmit={e=>{e.preventDefault();void run(async()=>{await post('mandates/'+selected+'/entries',{kind:'sugestao',message:suggestion});setSuggestion('');});}}><h3>Sugerir uma melhoria de prevenção</h3><p>Sugestão identificada, visível à equipe e a você. Este não é um canal de denúncias; não insira dados sensíveis.</p><label>O que você observou e o que poderia melhorar?<textarea required rows={4} maxLength={2000} value={suggestion} onChange={e=>setSuggestion(e.target.value)} disabled={closed} placeholder="Exemplo: A passagem perto do estoque fica obstruída. Sugiro manter o corredor livre." /></label><button disabled={busy||closed}>Enviar sugestão</button></form></section>}
          {tab==='historico'&&<section><h2>Meu histórico e decisões da equipe</h2>{data.entries.filter(e=>e.kind!=='aviso').map(e=><article key={e.id} className="cipa-box"><strong>{entryLabel[e.kind]||e.kind}</strong><small>{localTime(e.created_at)}</small><p className="cipa-pre">{e.message}</p></article>)}{!data.entries.filter(e=>e.kind!=='aviso').length&&<p>Sem registros de participação ainda.</p>}</section>}
          <p className="cipa-footnote">Exibição limitada a {data.limits.actions} ações, {data.limits.meetings} reuniões e {data.limits.entries} registros recentes do mandato. Os registros anteriores não são apagados.</p>
        </>}
      </>}
    </>}
    <footer>Auditar Soluções • Portal individual CIPA • Acesso restrito à sua empresa e aos mandatos liberados.</footer>
  </main>;
}
