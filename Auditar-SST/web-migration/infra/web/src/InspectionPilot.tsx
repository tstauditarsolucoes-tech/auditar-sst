import { useEffect, useState } from 'react';
import {EvidencePilot} from './EvidencePilot';

type PilotSession={
  companyId:string;
  role:'adm'|'gestor'|'tecnico'|'cliente';
  csrfToken:string;
};
type Inspection={
  id:string;inspection_type:'vistoria'|'ronda_expressa'|'checklist';
  status:'rascunho'|'concluida'|'arquivada';
  title:string;description:string;sector:string;location:string;
  revision:number;created_at:string;completed_at:string|null;
};
type Finding={
  id:string;short_title:string;description:string;probability:number;
  severity:number;recurring:boolean;status:string;
};
type InspectionEvent={id:string;kind:string;message:string;created_at:string};
type Detail={inspection:Inspection;findings:Finding[];events:InspectionEvent[]};
const kinds:Record<Inspection['inspection_type'],string>={
  vistoria:'Vistoria',ronda_expressa:'Ronda Expressa',checklist:'Checklist',
};
const states:Record<Inspection['status'],string>={
  rascunho:'Rascunho',concluida:'Concluída',arquivada:'Arquivada',
};
const newRequestId=()=>crypto.randomUUID();

async function api<T>(path:string,method:'GET'|'POST'|'PATCH'='GET',
  body?:object,csrf?:string):Promise<T> {
  const response=await fetch('/api/v1/'+path,{
    method,
    headers:{
      ...(body?{'Content-Type':'application/json'}:{}),
      ...(csrf?{'X-CSRF-Token':csrf}:{}),
    },
    credentials:'same-origin',
    cache:'no-store',
    body:body?JSON.stringify(body):undefined,
  });
  const payload:unknown=await response.json().catch(()=>null);
  if(!response.ok){
    const code=payload&&typeof payload==='object'&&'code' in payload?
      String((payload as {code:string}).code):'HTTP_'+response.status;
    const names:Record<string,string>={
      UNAUTHENTICATED:'Sua sessão de teste expirou. Entre novamente.',
      FORBIDDEN:'Seu perfil não pode realizar esta ação.',
      STALE_REVISION:'Este rascunho mudou em outra sessão. Reabra antes de editar.',
      IDEMPOTENCY_CONFLICT:'Essa chave de envio já existe com informações diferentes.',
      INVALID_STATE:'A vistoria já foi concluída ou não aceita novos achados.',
      NOT_FOUND:'Vistoria indisponível para sua empresa ou perfil.',
      CSRF_DENIED:'Proteção de sessão inválida. Entre novamente.',
    };
    throw new Error(names[code]||'Não foi possível executar: '+code);
  }
  return payload as T;
}

export function InspectionPilot({session}:{session:PilotSession}){
  const [inspections,setInspections]=useState<Inspection[]>([]);
  const [detail,setDetail]=useState<Detail|null>(null);
  const [busy,setBusy]=useState(false);
  const [notice,setNotice]=useState('');
  const [kind,setKind]=useState<Inspection['inspection_type']>('vistoria');
  const [title,setTitle]=useState('');
  const [description,setDescription]=useState('');
  const [sector,setSector]=useState('');
  const [location,setLocation]=useState('');
  const [createKey,setCreateKey]=useState(newRequestId);
  const [editTitle,setEditTitle]=useState('');
  const [editDescription,setEditDescription]=useState('');
  const [editSector,setEditSector]=useState('');
  const [editLocation,setEditLocation]=useState('');
  const [findingName,setFindingName]=useState('');
  const [findingDescription,setFindingDescription]=useState('');
  const [findingProbability,setFindingProbability]=useState(3);
  const [findingSeverity,setFindingSeverity]=useState(3);
  const [findingRecurring,setFindingRecurring]=useState(false);
  const [findingKey,setFindingKey]=useState(newRequestId);
  const [confirmComplete,setConfirmComplete]=useState(false);
  const canWrite=session.role!=='cliente';

  useEffect(()=>{
    let alive=true;
    api<{items:Inspection[]}>('inspections')
      .then(value=>{if(alive)setInspections(value.items);})
      .catch(()=>{if(alive)setNotice('As vistorias ainda não foram habilitadas nesta homologação.');});
    return ()=>{alive=false;};
  },[]);

  async function run(action:()=>Promise<void>){
    setBusy(true);setNotice('');
    try{await action();}
    catch(error){setNotice(error instanceof Error?error.message:'Falha no teste');}
    finally{setBusy(false);}
  }
  async function refresh(){
    const response=await api<{items:Inspection[]}>('inspections');
    setInspections(response.items);
  }
  async function open(id:string){
    const response=await api<Detail>('inspections/'+id);
    setDetail(response);
    setEditTitle(response.inspection.title);
    setEditDescription(response.inspection.description);
    setEditSector(response.inspection.sector);
    setEditLocation(response.inspection.location);
    setConfirmComplete(false);
  }
  async function create(){
    const response=await api<{item:Inspection}>('inspections','POST',{
      inspectionType:kind,title,description,sector,location,clientRequestId:createKey,
    },session.csrfToken);
    setTitle('');setDescription('');setSector('');setLocation('');
    setCreateKey(newRequestId());
    await refresh();
    await open(response.item.id);
    setNotice('Rascunho de teste salvo no banco de homologação.');
  }
  async function save(){
    if(!detail)return;
    await api('inspections/'+detail.inspection.id,'PATCH',{
      title:editTitle,description:editDescription,sector:editSector,location:editLocation,
      expectedRevision:detail.inspection.revision,
    },session.csrfToken);
    await open(detail.inspection.id);
    await refresh();
    setNotice('Rascunho atualizado e histórico preservado.');
  }
  async function addFinding(){
    if(!detail)return;
    await api('inspections/'+detail.inspection.id+'/findings','POST',{
      shortTitle:findingName,description:findingDescription,
      probability:findingProbability,severity:findingSeverity,recurring:findingRecurring,
      clientRequestId:findingKey,
    },session.csrfToken);
    setFindingKey(newRequestId());
    setFindingName('');setFindingDescription('');
    setFindingProbability(3);setFindingSeverity(3);setFindingRecurring(false);
    await open(detail.inspection.id);
    await refresh();
    setNotice('Achado de teste vinculado à vistoria.');
  }
  async function complete(){
    if(!detail||!confirmComplete)return;
    await api('inspections/'+detail.inspection.id+'/complete','POST',{},session.csrfToken);
    await open(detail.inspection.id);
    await refresh();
    setNotice('Vistoria fictícia concluída; rascunho bloqueado para edição.');
  }

  return <section className="inspection-pilot" aria-label="Vistorias de homologação">
    <div className="panel-top">
      <div>
        <p className="eyebrow green">VISTORIAS • HOMOLOGAÇÃO PRIVADA</p>
        <h3>Vistorias e Ronda Expressa no servidor</h3>
        <p className="muted">Teste de rascunhos, achados e conclusão. Fotos fictícias em volume privado opcional; sem IA, sincronização Flutter ou dados existentes nesta etapa.</p>
      </div>
      <button type="button" className="secondary-button" disabled={busy}
        onClick={()=>void run(refresh)}>Atualizar lista</button>
    </div>
    {notice&&<p role="status" className="auth-message">{notice}</p>}
    {canWrite&&<form className="auth-form" onSubmit={event=>{event.preventDefault();void run(create);}}>
      <h4>Nova vistoria fictícia</h4>
      <label>Tipo
        <select value={kind} onChange={event=>setKind(event.target.value as Inspection['inspection_type'])}>
          {Object.entries(kinds).map(([value,label])=><option key={value} value={value}>{label}</option>)}
        </select>
      </label>
      <label>Título
        <input value={title} onChange={event=>setTitle(event.target.value)}
          maxLength={200} required placeholder="Ex.: Ronda fictícia do setor de produção"/>
      </label>
      <div className="inspection-two">
        <label>Setor
          <input value={sector} onChange={event=>setSector(event.target.value)} maxLength={180}/>
        </label>
        <label>Local ou máquina
          <input value={location} onChange={event=>setLocation(event.target.value)} maxLength={180}/>
        </label>
      </div>
      <label>Observações
        <textarea value={description} onChange={event=>setDescription(event.target.value)}
          maxLength={4000} rows={2}/>
      </label>
      <button className="primary-button" type="submit" disabled={busy}>Salvar rascunho</button>
    </form>}
    <h4>Vistorias da empresa selecionada</h4>
    {inspections.length===0&&<p className="empty">Nenhuma vistoria disponível nesta empresa de teste.</p>}
    <div className="inspection-list">
      {inspections.map(item=><article className="inspection-item" key={item.id}>
        <div>
          <strong>{item.title}</strong>
          <small>{kinds[item.inspection_type]} · {item.sector||'Setor não informado'} · {states[item.status]}</small>
        </div>
        <button type="button" className="secondary-button" disabled={busy}
          onClick={()=>void run(()=>detail?.inspection.id===item.id?
            Promise.resolve(setDetail(null)):open(item.id))}>
          {detail?.inspection.id===item.id?'Fechar':'Abrir'}
        </button>
      </article>)}
    </div>
    {detail&&<div className="inspection-detail">
      <div className="panel-top">
        <div>
          <h4>{detail.inspection.title}</h4>
          <p className="muted">{states[detail.inspection.status]} · Revisão {detail.inspection.revision} · {detail.inspection.location||'Local não informado'}</p>
        </div>
      </div>
      {canWrite&&detail.inspection.status==='rascunho'&&<>
        <form className="auth-form" onSubmit={event=>{event.preventDefault();void run(save);}}>
          <h4>Editar rascunho</h4>
          <label>Título<input value={editTitle} onChange={event=>setEditTitle(event.target.value)} maxLength={200} required/></label>
          <div className="inspection-two">
            <label>Setor<input value={editSector} onChange={event=>setEditSector(event.target.value)} maxLength={180}/></label>
            <label>Local<input value={editLocation} onChange={event=>setEditLocation(event.target.value)} maxLength={180}/></label>
          </div>
          <label>Descrição<textarea value={editDescription} onChange={event=>setEditDescription(event.target.value)} maxLength={4000} rows={2}/></label>
          <button type="submit" className="secondary-button" disabled={busy}>Salvar alterações</button>
        </form>
        <form className="auth-form" onSubmit={event=>{event.preventDefault();void run(addFinding);}}>
          <h4>Adicionar não conformidade fictícia</h4>
          <label>Nome da NC
            <input maxLength={140} value={findingName} onChange={event=>setFindingName(event.target.value)}
              placeholder="Ex.: Extintor vencido"/>
          </label>
          <label>Descrição do achado
            <textarea rows={3} maxLength={4000} required
              value={findingDescription} onChange={event=>setFindingDescription(event.target.value)}/>
          </label>
          <div className="inspection-two">
            <label>Probabilidade
              <select value={findingProbability} onChange={event=>setFindingProbability(Number(event.target.value))}>
                {[1,2,3,4,5].map(n=><option key={n} value={n}>{n}</option>)}
              </select>
            </label>
            <label>Severidade
              <select value={findingSeverity} onChange={event=>setFindingSeverity(Number(event.target.value))}>
                {[1,2,3,4,5].map(n=><option key={n} value={n}>{n}</option>)}
              </select>
            </label>
          </div>
          <label className="inspection-check"><input type="checkbox" checked={findingRecurring}
            onChange={event=>setFindingRecurring(event.target.checked)}/> Não conformidade recorrente</label>
          <button className="primary-button" type="submit" disabled={busy}>Adicionar achado</button>
        </form>
        <div className="inspection-complete">
          <label className="inspection-check"><input type="checkbox" checked={confirmComplete}
            onChange={event=>setConfirmComplete(event.target.checked)}/>
            Confirmo que esta vistoria é fictícia e que não será mais editável após concluir.
          </label>
          <button type="button" className="primary-button" disabled={busy||!confirmComplete}
            onClick={()=>void run(complete)}>Concluir vistoria sem IA</button>
        </div>
      </>}
      <h4>Achados vinculados</h4>
      {detail.findings.length===0&&<p className="muted">Nenhum achado; uma vistoria conforme também pode ser concluída.</p>}
      <div className="inspection-list">{detail.findings.map(item=><article key={item.id} className="inspection-item">
        <div>
          <strong>{item.short_title||item.description}</strong>
          <small>Risco: {item.probability} × {item.severity} · {item.status.replaceAll('_',' ')}
            {item.recurring?' · Recorrente':''}</small>
          <p>{item.description}</p>
        </div>
      </article>)}</div>
      {canWrite&&<EvidencePilot session={session} targetType="inspection" targetId={detail.inspection.id}/>}
      <h4>Histórico da vistoria</h4>
      <ol className="auth-timeline">{detail.events.map(event=><li key={event.id}>
        <strong>{event.kind.replaceAll('_',' ')}</strong>
        {event.message&&<p>{event.message}</p>}
        <small>{new Date(event.created_at).toLocaleString('pt-BR')}</small>
      </li>)}</ol>
    </div>}
  </section>;
}
