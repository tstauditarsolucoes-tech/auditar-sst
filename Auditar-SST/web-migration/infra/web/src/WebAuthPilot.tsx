import { useEffect, useState } from 'react';

type WebSession = {
  ok: true;
  user: {id: string; name: string};
  companyId: string;
  role: 'adm' | 'gestor' | 'tecnico' | 'cliente';
  csrfToken: string;
};
type Company = { company_id: string; name: string; role: WebSession['role'] };
type Nc = {
  id: string;
  description: string;
  probability: number;
  severity: number;
  recurring: boolean;
  status: 'aberta' | 'correcao_informada' | 'rejeitada' | 'validada';
};
type NcEvent = {id: string;kind: string;message: string;created_at: string};

const statusText: Record<Nc['status'], string> = {
  aberta: 'Aberta',
  correcao_informada: 'Aguardando validação',
  rejeitada: 'Correção rejeitada',
  validada: 'Validada',
};

async function request<T>(path: string, method: 'GET' | 'POST' = 'GET', body?: object, csrf?: string): Promise<T> {
  const headers: Record<string,string> = {};
  if (body) headers['Content-Type'] = 'application/json';
  if (csrf) headers['X-CSRF-Token'] = csrf;
  const response = await fetch('/api/v1/' + path, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
    credentials: 'same-origin',
    cache: 'no-store',
  });
  const data: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const code = data && typeof data === 'object' && 'code' in data ?
      String((data as {code: string}).code) : 'HTTP_' + response.status;
    throw new Error(code === 'UNAUTHENTICATED' ? 'A sessão não está disponível ou expirou.' :
      code === 'LOGIN_FAILED' ? 'E-mail ou senha não conferem.' :
      code === 'CSRF_DENIED' ? 'Proteção da sessão inválida. Atualize o acesso.' :
      code === 'ORIGIN_DENIED' ? 'Endereço não autorizado para este teste.' :
      code === 'FORBIDDEN' ? 'A sua conta não tem permissão para esta ação.' :
      'Operação indisponível: ' + code);
  }
  return data as T;
}

export function WebAuthPilot() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [session, setSession] = useState<WebSession | null>(null);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [ncs, setNcs] = useState<Nc[]>([]);
  const [histories, setHistories] = useState<Record<string,NcEvent[]>>({});
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [description, setDescription] = useState('');
  const [probability, setProbability] = useState(3);
  const [severity, setSeverity] = useState(3);
  const [note, setNote] = useState('');
  const [actionId, setActionId] = useState<string | null>(null);

  async function refresh() {
    const [usersCompanies, ncData] = await Promise.all([
      request<{items: Company[]}>('auth/companies'),
      request<{items: Nc[]}>('nonconformities'),
    ]);
    setCompanies(usersCompanies.items);
    setNcs(ncData.items);
  }

  useEffect(() => {
    let mounted = true;
    request<WebSession>('auth/session')
      .then(async (value) => {
        if (!mounted) return;
        setSession(value);
        const [list, rows] = await Promise.all([
          request<{items: Company[]}>('auth/companies'),
          request<{items: Nc[]}>('nonconformities'),
        ]);
        if (mounted) {setCompanies(list.items);setNcs(rows.items);}
      })
      .catch(() => { /* padrão sem login novo: nenhuma sessão real */ });
    return () => {mounted = false;};
  }, []);

  async function run(action: () => Promise<void>) {
    setBusy(true);
    setMessage('');
    try { await action(); }
    catch (error) { setMessage(error instanceof Error ? error.message : 'Falha no teste'); }
    finally { setBusy(false); }
  }
  async function login() {
    const value = await request<WebSession>('auth/login','POST',{email,password});
    setSession(value);
    setPassword('');
    await refresh();
    setMessage('Sessão de homologação iniciada.');
  }
  async function logout() {
    await request<{ok: boolean}>('auth/logout','POST',{},session?.csrfToken);
    setSession(null);setCompanies([]);setNcs([]);setHistories({});setPassword('');
    setMessage('Sessão encerrada.');
  }
  async function changeCompany(companyId: string) {
    const changed = await request<{companyId: string;role: WebSession['role']}>(
      'auth/company','POST',{companyId},session?.csrfToken,
    );
    setSession((current) => current ? {...current,companyId:changed.companyId,role:changed.role} : null);
    setHistories({});
    await refresh();
    setMessage('Empresa de homologação alterada.');
  }
  async function createNc() {
    await request<{item:Nc}>('nonconformities','POST',{
      description,probability,severity,
    },session?.csrfToken);
    setDescription('');
    await refresh();
    setMessage('NC criada no banco de homologação.');
  }
  async function actOnNc(id: string, mode: 'informar' | 'validar' | 'rejeitar') {
    const route = mode === 'informar' ? 'correction' : 'decision';
    const payload = mode === 'informar' ? {message:note} :
      {accepted:mode === 'validar',reason:note};
    await request('nonconformities/' + id + '/' + route,'POST',payload,session?.csrfToken);
    setNote('');setActionId(null);
    await refresh();
    setMessage('Tratativa de NC registrada.');
  }
  async function toggleHistory(id: string) {
    if (histories[id]) {
      setHistories((current)=>{const copy={...current};delete copy[id];return copy;});
      return;
    }
    const values=await request<{items:NcEvent[]}>('nonconformities/' + id + '/events');
    setHistories((current)=>({...current,[id]:values.items}));
  }
  const canValidate = session && ['tecnico','gestor','adm'].includes(session.role);

  return (
    <section className="panel auth-pilot">
      <div className="panel-top">
        <div>
          <p className="eyebrow green">MÓDULO NOVO EM HOMOLOGAÇÃO</p>
          <h2>Teste de login e NCs conectadas</h2>
          <p className="muted">Esta área é separada dos exemplos. Ela só funciona quando o Júlio habilitar o novo servidor isolado com HTTPS e as contas autorizadas.</p>
        </div>
        <span className="tag">Acesso protegido</span>
      </div>
      <p className="privacy-warning">Não insira senhas do aplicativo atual nem dados, fotos ou informações reais de clientes. O login novo ainda não está ativo no Docker padrão.</p>
      {message && <p role="status" className="auth-message">{message}</p>}

      {!session ? (
        <form className="auth-form" onSubmit={(event) => {event.preventDefault();void run(login);}}>
          <label>E-mail de homologação
            <input type="email" autoComplete="username" value={email}
              onChange={(event)=>setEmail(event.target.value)} maxLength={254} required />
          </label>
          <label>Senha da conta nova de homologação
            <input type="password" autoComplete="current-password" value={password}
              onChange={(event)=>setPassword(event.target.value)} minLength={12} maxLength={256} required />
          </label>
          <button className="primary-button" type="submit" disabled={busy}>Entrar para testar</button>
          <p className="muted">Se aparecer “sessão não disponível”, a autenticação ainda não foi ativada pelo administrador da homologação.</p>
        </form>
      ) : (
        <>
          <div className="auth-session">
            <div><strong>{session.user.name}</strong><small>Perfil: {session.role} · Sessão de homologação</small></div>
            <button className="secondary-button" disabled={busy} onClick={()=>void run(logout)}>Sair</button>
          </div>
          <label className="auth-company">Empresa ativa
            <select value={session.companyId} disabled={busy}
              onChange={(event)=>void run(()=>changeCompany(event.target.value))}>
              {companies.map((c)=><option key={c.company_id} value={c.company_id}>{c.name} ({c.role})</option>)}
            </select>
          </label>
          <div className="auth-divider" />
          {session.role !== 'cliente' && (
            <form className="auth-form" onSubmit={(event)=>{event.preventDefault();void run(createNc);}}>
              <h3>Criar NC de teste</h3>
              <label>Descrição
                <textarea value={description} maxLength={4000} rows={3} required
                  onChange={(event)=>setDescription(event.target.value)} placeholder="Somente situação fictícia" />
              </label>
              <div className="auth-numbers">
                <label>Probabilidade
                  <select value={probability} onChange={(e)=>setProbability(Number(e.target.value))}>
                    {[1,2,3,4,5].map((n)=><option key={n} value={n}>{n}</option>)}
                  </select>
                </label>
                <label>Severidade
                  <select value={severity} onChange={(e)=>setSeverity(Number(e.target.value))}>
                    {[1,2,3,4,5].map((n)=><option key={n} value={n}>{n}</option>)}
                  </select>
                </label>
              </div>
              <button className="primary-button" type="submit" disabled={busy}>Criar NC fictícia</button>
            </form>
          )}
          <div className="auth-divider" />
          <div className="panel-top">
            <h3>NCs da empresa ativa</h3>
            <button className="secondary-button" disabled={busy} onClick={()=>void run(refresh)}>Atualizar</button>
          </div>
          {ncs.length === 0 && <p className="empty">Nenhuma não conformidade cadastrada nesta empresa de homologação.</p>}
          <div className="nc-list">
            {ncs.map((nc)=>(
              <article key={nc.id} className="nc-card">
                <p className="nc-code">{nc.id}</p>
                <h3>{nc.description}</h3>
                <p className="muted">Probabilidade {nc.probability} × Severidade {nc.severity}</p>
                <span className="status">{statusText[nc.status]}</span>
                <div className="auth-actions">
                  <button className="secondary-button" disabled={busy}
                    onClick={()=>void run(()=>toggleHistory(nc.id))}>
                    {histories[nc.id] ? 'Ocultar histórico' : 'Ver histórico'}
                  </button>
                </div>
                {histories[nc.id] && <ol className="auth-timeline">
                  {histories[nc.id].map((event)=><li key={event.id}>
                    <strong>{event.kind.replaceAll('_',' ')}</strong>
                    {event.message && <p>{event.message}</p>}
                    <small>{new Date(event.created_at).toLocaleString('pt-BR')}</small>
                  </li>)}
                </ol>}
                {nc.status !== 'validada' && (
                  <div className="auth-actions">
                    <button type="button" className="secondary-button" disabled={busy}
                      onClick={()=>{setActionId(actionId===nc.id?null:nc.id);setNote('');}}>Registrar tratativa</button>
                    {actionId===nc.id && (
                      <div className="auth-form">
                        <label>Comentário ou motivo
                          <textarea rows={2} maxLength={1200} value={note} onChange={(event)=>setNote(event.target.value)}/>
                        </label>
                        {(nc.status==='aberta'||nc.status==='rejeitada') ? (
                          <button className="primary-button" disabled={busy} onClick={()=>void run(()=>actOnNc(nc.id,'informar'))}>
                            Informar correção
                          </button>
                        ) : canValidate ? (
                          <div className="auth-actions">
                            <button className="primary-button" disabled={busy}
                              onClick={()=>void run(()=>actOnNc(nc.id,'validar'))}>Validar</button>
                            <button className="secondary-button" disabled={busy||!note.trim()}
                              onClick={()=>void run(()=>actOnNc(nc.id,'rejeitar'))}>Rejeitar com motivo</button>
                          </div>
                        ) : <p className="muted">Aguardando análise técnica.</p>}
                      </div>
                    )}
                  </div>
                )}
              </article>
            ))}
          </div>
        </>
      )}
    </section>
  );
}
