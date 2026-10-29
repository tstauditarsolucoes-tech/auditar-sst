import {useEffect,useState} from 'react';

type Member={id:string;display_name:string;role:string;last_seen:string|null;web_recent:boolean};
type Overview={nc_pendentes:number;vistorias:number;tarefas_abertas:number;apoio_aberto:number};
async function get<T>(path:string):Promise<T>{
  const response=await fetch('/api/v1/'+path,{cache:'no-store',credentials:'same-origin'});
  if(!response.ok)throw new Error('Central ADM indisponível ('+response.status+')');
  return response.json() as Promise<T>;
}
export function AdminOverviewPilot(){
  const [summary,setSummary]=useState<Overview|null>(null);
  const [team,setTeam]=useState<Member[]>([]);
  const [notice,setNotice]=useState('');
  const [busy,setBusy]=useState(false);
  async function refresh(){
    const [overview,staff]=await Promise.all([
      get<Overview>('admin/overview'),get<{items:Member[]}>('admin/team'),
    ]);
    setSummary(overview);setTeam(staff.items);setNotice('');
  }
  useEffect(()=>{
    let live=true;
    Promise.all([get<Overview>('admin/overview'),get<{items:Member[]}>('admin/team')])
      .then(([overview,staff])=>{if(live){setSummary(overview);setTeam(staff.items);}})
      .catch(()=>{if(live)setNotice('Central ADM de homologação não disponível.');});
    return()=>{live=false;};
  },[]);
  return <section className="admin-pilot" aria-label="Central administrativa web em homologação">
    <div className="panel-top">
      <div>
        <p className="eyebrow green">CENTRAL ADM · HOMOLOGAÇÃO</p>
        <h3>Visão gerencial da empresa ativa</h3>
        <p className="muted">Indicadores apenas da empresa selecionada, com registros fictícios da nova base.</p>
      </div>
      <button type="button" className="secondary-button" disabled={busy} onClick={()=>{
        setBusy(true);void refresh().catch(e=>setNotice(String(e))).finally(()=>setBusy(false));
      }}>Atualizar</button>
    </div>
    {notice&&<p className="auth-message" role="status">{notice}</p>}
    <div className="portal-stats">
      {([
        ['NCs pendentes',summary?.nc_pendentes],
        ['Vistorias',summary?.vistorias],
        ['Tarefas abertas',summary?.tarefas_abertas],
        ['Solicitações de apoio',summary?.apoio_aberto],
      ] as const).map(([caption,qty])=><div key={caption} className="portal-stat">
        <strong>{qty??'–'}</strong><span>{caption}</span>
      </div>)}
    </div>
    <h4>Atividade da equipe na nova versão web</h4>
    <p className="muted">“Atividade recente” significa acesso à interface web nos últimos 3 minutos; não representa presença no aplicativo Flutter do Android ou Windows.</p>
    {team.length===0&&<p className="empty">Nenhuma conta técnica ativa identificada nesta empresa de homologação.</p>}
    <div className="inspection-list">{team.map(person=><article className="inspection-item" key={person.id}>
      <div><strong>{person.display_name}</strong><small>Perfil: {person.role}</small>
        <small>Última atividade web: {person.last_seen?
          new Date(person.last_seen).toLocaleString('pt-BR'):'Nenhuma atividade registrada'}</small></div>
      <span className="status">{person.web_recent?'Atividade recente':'Sem atividade recente'}</span>
    </article>)}</div>
    <p className="muted">Criação de contas e acesso global entre empresas ainda não fazem parte deste piloto: ficam bloqueados até definição de permissões e migração autenticada.</p>
  </section>;
}
