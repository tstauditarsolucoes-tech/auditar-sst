import { useEffect, useMemo, useState } from 'react';
import { displayNcTitle, matrixScore, normalizeFriendlyName, priorityFromMatrix } from './domain/nc';
import type { Priority } from './domain/nc';

type Entry = {
  id: string;
  description: string;
  sector: string;
  status: 'Aberta' | 'Aguardando validação' | 'Validada';
  probability: number;
  severity: number;
  recurring: boolean;
};
type Section = 'inicio' | 'ncs';
type Filter = 'Todas' | Entry['status'];

const EXAMPLES: readonly Entry[] = [
  { id: 'DEMO-NC-001', description: 'Extintor vencido. Providenciar substituição e inspecionar sinalização.', sector: 'Expedição', status: 'Aberta', probability: 4, severity: 4, recurring: false },
  { id: 'DEMO-NC-002', description: 'Proteção removida na transmissão da máquina. Isolar o equipamento e reinstalar a proteção.', sector: 'Produção', status: 'Aguardando validação', probability: 5, severity: 5, recurring: true },
  { id: 'DEMO-NC-003', description: 'Ausência de identificação do extintor. Regularizar placa.', sector: 'Oficina', status: 'Validada', probability: 2, severity: 2, recurring: false },
  { id: 'DEMO-NC-004', description: 'Obstrução no acesso ao extintor. Desobstruir e manter livre.', sector: 'Almoxarifado', status: 'Aberta', probability: 3, severity: 3, recurring: true },
];

function priorityClass(p: Priority): string {
  return p === 'Crítica' ? 'critical' : p === 'Alta' ? 'high' : p === 'Média' ? 'medium' : 'low';
}

export function App() {
  const [section, setSection] = useState<Section>('inicio');
  const [aliases, setAliases] = useState<Record<string, string>>({});
  const [editingId, setEditingId] = useState<string | null>(null);
  const [nameDraft, setNameDraft] = useState('');
  const [editError, setEditError] = useState('');
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState<Filter>('Todas');
  const [probability, setProbability] = useState(3);
  const [severity, setSeverity] = useState(3);
  const [recurring, setRecurring] = useState(false);
  const [apiStatus, setApiStatus] = useState<'consultando' | 'disponível' | 'indisponível'>('consultando');

  useEffect(() => {
    const controller = new AbortController();
    fetch('/api/v1/health', { signal: controller.signal, credentials: 'omit', cache: 'no-store' })
      .then((r) => { if (!r.ok) throw new Error('API não disponível'); return r.json(); })
      .then(() => setApiStatus('disponível'))
      .catch((e: unknown) => {
        if (!(e instanceof Error && e.name === 'AbortError')) setApiStatus('indisponível');
      });
    return () => controller.abort();
  }, []);

  const filtered = useMemo(() => EXAMPLES.filter((row) => {
    const matchesFilter = filter === 'Todas' || row.status === filter;
    const normalizedQuery = query.trim().toLocaleLowerCase('pt-BR');
    const matchesSearch = !normalizedQuery ||
      [displayNcTitle(row, aliases), row.description, row.id, row.sector]
        .some((value) => value.toLocaleLowerCase('pt-BR').includes(normalizedQuery));
    return matchesFilter && matchesSearch;
  }), [aliases, query, filter]);

  const score = matrixScore(probability, severity, recurring);
  const priority = priorityFromMatrix(probability, severity, recurring);

  function beginEdit(row: Entry) {
    setEditingId(row.id);
    setNameDraft(aliases[row.id] ?? '');
    setEditError('');
  }
  function saveName(id: string) {
    try {
      const value = normalizeFriendlyName(nameDraft);
      setAliases((current) => ({ ...current, [id]: value }));
      setEditingId(null);
      setEditError('');
    } catch (e) {
      setEditError(e instanceof Error ? e.message : 'Não foi possível salvar o nome');
    }
  }

  return (
    <div className="layout">
      <aside className="sidebar" aria-label="Navegação do protótipo">
        <div className="brand"><span className="brand-mark">A</span><span><strong>AUDITAR</strong><small>SST · WEB</small></span></div>
        <p className="sidebar-label">AMBIENTE DE TESTES</p>
        <nav className="navigation" aria-label="Módulos">
          <button className={section === 'inicio' ? 'navitem active' : 'navitem'} onClick={() => setSection('inicio')} aria-current={section === 'inicio' ? 'page' : undefined}>▦ <span>Visão geral</span></button>
          <button className={section === 'ncs' ? 'navitem active' : 'navitem'} onClick={() => setSection('ncs')} aria-current={section === 'ncs' ? 'page' : undefined}>◉ <span>Não conformidades</span></button>
          <div className="coming"><span>Agenda SST</span><small>Em migração</small></div>
          <div className="coming"><span>Relatórios e PDF</span><small>Em migração</small></div>
          <div className="coming"><span>Painel do cliente</span><small>Em migração</small></div>
        </nav>
        <div className="sidebar-foot"><strong>Protótipo isolado</strong><span>Sem contas, fotos ou banco real</span></div>
      </aside>

      <main className="main">
        <header className="page-header">
          <div><p className="eyebrow">AUDITAR SOLUÇÕES · PRIMEIRA ETAPA WEB</p><h1>{section === 'inicio' ? 'Visão geral' : 'Não conformidades'}</h1><p className="subheading">Funcionalidades portadas do aplicativo SST para navegador</p></div>
          <div className="api-pill" title="Consulta apenas o endereço de saúde do Node.js"><span className={`dot ${apiStatus}`} />API: {apiStatus}</div>
        </header>

        <div className="notice" role="status"><strong>DEMONSTRAÇÃO COM DADOS FICTÍCIOS</strong><span>Este ambiente não está conectado à Central Online. As alterações existem somente nesta tela e desaparecem ao atualizar a página.</span></div>

        {section === 'inicio' ? (
          <>
            <section className="metric-grid" aria-label="Resumo fictício">
              <div className="metric"><span>Não conformidades demonstrativas</span><strong>04</strong><small>Exemplos, não registros reais</small></div>
              <div className="metric"><span>Abertas</span><strong>02</strong><small>Somente demonstração</small></div>
              <div className="metric"><span>Aguardando validação</span><strong>01</strong><small>Fluxo real ainda não conectado</small></div>
              <div className="metric"><span>Validadas</span><strong>01</strong><small>Somente demonstração</small></div>
            </section>
            <section className="panel simulator">
              <div className="panel-top"><div><p className="eyebrow green">MÓDULO PORTADO DO DART</p><h2>Simulador de prioridade</h2><p className="muted">Reproduz a matriz do Assistente Offline do Auditar SST.</p></div><span className="tag">100% local</span></div>
              <div className="simulation-grid">
                <label>Probabilidade
                  <select value={probability} onChange={(e) => setProbability(Number(e.target.value))}>
                    {[1,2,3,4,5].map((n) => <option key={n} value={n}>{n}</option>)}
                  </select>
                </label>
                <label>Severidade
                  <select value={severity} onChange={(e) => setSeverity(Number(e.target.value))}>
                    {[1,2,3,4,5].map((n) => <option key={n} value={n}>{n}</option>)}
                  </select>
                </label>
                <label className="check-label"><input type="checkbox" checked={recurring} onChange={(e) => setRecurring(e.target.checked)}/> NC recorrente (+2 pontos)</label>
                <div className="score"><span>Pontuação</span><strong>{score}<small>/25</small></strong><span className={`priority ${priorityClass(priority)}`}>{priority}</span></div>
              </div>
            </section>
            <section className="panel quick-view">
              <div className="panel-top"><div><h2>NCs de demonstração</h2><p className="muted">Confira nomes, códigos e classificação de risco.</p></div><button className="secondary-button" onClick={() => setSection('ncs')}>Ver e editar nomes</button></div>
              <div className="nc-list">{EXAMPLES.slice(0, 3).map((row) => <div className="nc-summary" key={row.id}><div><strong>{displayNcTitle(row, aliases)}</strong><small>{row.id} · {row.sector}</small></div><span className={`priority ${priorityClass(priorityFromMatrix(row.probability, row.severity, row.recurring))}`}>{priorityFromMatrix(row.probability, row.severity, row.recurring)}</span></div>)}</div>
            </section>
          </>
        ) : (
          <section className="panel">
            <div className="panel-top"><div><p className="eyebrow green">MÓDULO PORTADO DO DART</p><h2>Nomes amigáveis das NCs</h2><p className="muted">O nome exibido pode mudar sem alterar o código nem a descrição original.</p></div><span className="tag">{filtered.length} resultado(s)</span></div>
            <div className="filters"><label className="search-field">Buscar NC, código ou setor<input type="search" placeholder="Ex.: extintor, proteção..." value={query} onChange={(e) => setQuery(e.target.value)}/></label><label>Situação<select value={filter} onChange={(e) => setFilter(e.target.value as Filter)}><option>Todas</option><option>Aberta</option><option>Aguardando validação</option><option>Validada</option></select></label></div>
            <div className="nc-list">{filtered.length === 0 ? <p className="empty">Nenhuma NC fictícia corresponde aos filtros.</p> : filtered.map((row) => <article className="nc-card" key={row.id}>
              <div className="nc-heading"><div><p className="nc-code">{row.id} · {row.sector}</p><h3>{displayNcTitle(row, aliases)}</h3></div><span className={`priority ${priorityClass(priorityFromMatrix(row.probability, row.severity, row.recurring))}`}>{priorityFromMatrix(row.probability, row.severity, row.recurring)}</span></div>
              <p className="original"><strong>Descrição original:</strong> {row.description}</p>
              <div className="nc-actions"><span className="status">{row.status}</span><button className="secondary-button" onClick={() => beginEdit(row)}>Editar nome</button></div>
              {editingId === row.id && <div className="editor"><label htmlFor={`name-${row.id}`}>Nome amigável (máx. 80 caracteres)</label><input id={`name-${row.id}`} value={nameDraft} maxLength={80} onChange={(e) => {setNameDraft(e.target.value);setEditError('');}} placeholder="Ex.: Extintor vencido" /><small>Deixe vazio para voltar ao título automático. {nameDraft.length}/80 caracteres.</small>{editError && <p className="error" role="alert">{editError}</p>}<div className="edit-buttons"><button className="primary-button" onClick={() => saveName(row.id)}>Aplicar nesta tela</button><button className="secondary-button" onClick={() => setEditingId(null)}>Cancelar</button></div></div>}
            </article>)}</div>
          </section>
        )}
        <footer className="footer">Migração Auditar SST Web · React/TypeScript · Sem implantação no domínio tst.auditarsolucoes.com.br</footer>
      </main>
    </div>
  );
}
