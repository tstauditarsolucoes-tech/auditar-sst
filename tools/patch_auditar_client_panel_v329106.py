#!/usr/bin/env python3
"""Existing management panel: server-side client-only public projection."""
from pathlib import Path
import sys
root=Path(sys.argv[1])/'painel_web_google_apps_script'
code=root/'Code.gs'; html=root/'Index.html'
s=code.read_text(encoding='utf-8')
start=s.index('function publicPanelPayload_(payload) {')
end=s.index('\nfunction panelCompanyLogoDataUri_', start)
projection=r'''// A public link is a read-only bearer token, not an Auditar user session.
// Never publish the original synchronized payload, even if a tab is hidden.
function clientPortalScopes_(payload) {
  const requested = payload && payload.clientPortal &&
    payload.clientPortal.version === 2 &&
    payload.clientPortal.modules && typeof payload.clientPortal.modules === 'object'
    ? payload.clientPortal.modules : {};
  const defaults = {
    overview: true, actions: true, inspections: true,
    training: false, safety: false, improvements: false,
    agenda: false, extinguishers: false
  };
  const allowed = {};
  Object.keys(defaults).forEach(function(key) {
    allowed[key] = key === 'overview' ? true :
      (Object.prototype.hasOwnProperty.call(requested, key)
        ? requested[key] === true : defaults[key]);
  });
  return allowed;
}

function publicPanelPayload_(payload) {
  const source = payload && typeof payload === 'object' ? payload : {};
  const scopes = clientPortalScopes_(source);
  function pick(row, names) {
    const clean = {};
    const value = row && typeof row === 'object' && !Array.isArray(row) ? row : {};
    names.forEach(function(name) {
      if (Object.prototype.hasOwnProperty.call(value, name)) clean[name] = value[name];
    });
    return clean;
  }
  function rows(data, names, max) {
    return (Array.isArray(data) ? data : []).slice(0, max || 80)
      .map(function(row) { return pick(row, names); });
  }
  const result = {
    schemaVersion: 12,
    updatedAt: String(source.updatedAt || ''),
    clientPortal: {version: 2, readOnly: true, modules: scopes},
    company: pick(source.company, ['id','name','city','uf']),
    summary: pick(source.summary,
      ['inspections','conformity','ncPending','ncInProgress','ncAwaiting','ncOverdue','overdue']),
    periodComparison: {
      currentStart: String((source.periodComparison || {}).currentStart || ''),
      currentEnd: String((source.periodComparison || {}).currentEnd || ''),
      previousStart: String((source.periodComparison || {}).previousStart || ''),
      previousEnd: String((source.periodComparison || {}).previousEnd || ''),
      currentSummary: pick((source.periodComparison || {}).currentSummary,
        ['inspections','conformity','ncPending','ncInProgress','ncAwaiting','ncOverdue','overdue']),
      previousSummary: pick((source.periodComparison || {}).previousSummary,
        ['inspections','conformity','ncPending','ncInProgress','ncAwaiting','ncOverdue','overdue']),
      currentMetrics: pick((source.periodComparison || {}).currentMetrics,
        ['openNc','overdueActions','expiredTrainings','sstScore']),
      previousMetrics: pick((source.periodComparison || {}).previousMetrics,
        ['openNc','overdueActions','expiredTrainings','sstScore'])
    },
    sstScore: pick(source.sstScore, ['value','previousValue','isCurrentMonth','method']),
    monthlyTrend: rows(source.monthlyTrend, ['label','conformity','inspections'], 24),
    sectors: rows(source.sectors,
      ['name','inspections','conformes','parciais','nao_conformes','overdue_ncs','openNcs','conformity'],80),
    // All module-specific data is opt-in and filtered on the SERVER, not CSS.
    openNonConformities: scopes.actions ? rows(source.openNonConformities,
      ['code','status','classification','sector','area','nextDueDate'],80) : [],
    pendingActions: scopes.actions ? rows(source.pendingActions,
      ['ncCode','status','priority','correctiveAction','problem','responsible','sector','area','dueDate'],80) : [],
    recentInspections: scopes.inspections ? rows(source.recentInspections,
      ['reportNumber','date','sector','area','checklistType','status'],80) : [],
    trainingSummary: scopes.training ? pick(source.trainingSummary,
      ['total','current','dueSoon','expired','pending']) : {},
    workforceSummary: scopes.training ? pick(source.workforceSummary,
      ['activeWorkers','missingRequiredTrainings']) : {},
    trainingRecords: scopes.training ? rows(source.trainingRecords,
      ['worker','role','sector','code','title','expiryDate','trainingDate','status'],100) : [],
    workforceDetails: scopes.training ? rows(source.workforceDetails,
      ['worker','role','sector','trainingStatus','trainingDetails'],100) : [],
    missingRequiredTrainings: scopes.training ? rows(source.missingRequiredTrainings,
      ['worker','role','code','title'],100) : [],
    safetyObservationSummary: scopes.safety ? pick(source.safetyObservationSummary,
      ['total','open','resolved','conditions','acts','criticalOrOverdue']) : {},
    safetyObservations: scopes.safety ? rows(source.safetyObservations,
      ['kind','title','description','sector','location','risk','priority','status',
       'overdue','dueDate','responsible'],80) : [],
    improvementSummary: scopes.improvements ? pick(source.improvementSummary,
      ['total','suggested','planned','inProgress','realized','withBeforeAfter']) : {},
    improvements: scopes.improvements ? rows(source.improvements,
      ['title','suggestion','beforeSituation','sector','location','priority','status',
       'overdue','responsible','dueDate','completedDate','hasBeforeAfter','hasBeforePhoto','hasAfterPhoto'],80) : [],
    agendaSummary: scopes.agenda ? pick(source.agendaSummary,
      ['today','next7Days','overdue','completed']) : {},
    agenda: scopes.agenda ? rows(source.agenda,
      ['date','title','description','notes','subtype','sector','location','responsible','status'],80) : [],
    extinguisherSummary: scopes.extinguishers ? pick(source.extinguisherSummary,
      ['total','current','dueSoon','expired','irregular','missingLocations','maintenance']) : {},
    extinguishers: scopes.extinguishers ? rows(source.extinguishers,
      ['code','type','capacity','sector','location','expiryDate','status','lastReplacementDate',
       'lastReplacementReason','responsibility','responsibleName','actionStatus'],100) : [],
    companySectors: scopes.extinguishers ? rows(source.companySectors,['id','name'],100) : []
  };
  // Never return accessToken, syncKey, notifications/emails, medical, CPF,
  // personal documents, raw JSON, attachment URLs, internal device records.
  return result;
}
'''
s=s[:start]+projection+s[end:]
# Existing management publication and device sync remain untouched, aside from
# a version marker on the management-only response to avoid false confirmation.
marker="return jsonResponse_({ok: true, message: 'Painel atualizado.'});"
if s.count(marker)!=1:raise RuntimeError('panel response marker')
s=s.replace(marker,"return jsonResponse_({ok: true, message: 'Painel atualizado.', clientPortalVersion: 2});",1)
# Confirm token is bound to the company row, not just a matching token string.
marker="  return {\n    active: data[3] === true || String(data[3]).toLowerCase() === 'true',\n    payload: payload,\n  };"
if s.count(marker)!=1:raise RuntimeError('panel record marker')
s=s.replace(marker,"  return {\n    active: data[3] === true || String(data[3]).toLowerCase() === 'true',\n    companyId: String(data[1] || ''),\n    payload: payload,\n  };",1)
marker="  if (!record.active) return unavailablePage_('Este acesso está desativado.');"
if s.count(marker)!=1:raise RuntimeError('panel grant marker')
s=s.replace(marker,marker+"""
  const storedId = String(record.companyId || '');
  const payloadId = String(((record.payload || {}).company || {}).id || '');
  if (!storedId || !payloadId || storedId !== payloadId) {
    return unavailablePage_('Vínculo da empresa inválido.');
  }""",1)
code.write_text(s,encoding='utf-8',newline='\n')

h=html.read_text(encoding='utf-8')
marker="    document.querySelectorAll('[role=\"tab\"]').forEach(button=>{button.addEventListener('click',()=>{"
if h.count(marker)!=1:raise RuntimeError('client html final tabs marker')
insertion=r'''    // A server-side projection already removes denied datasets. Hide their
    // navigation as well, including overview shortcuts and printed sections.
    const CLIENT_SCOPES=(DATA.clientPortal||{}).modules||{};
    const CLIENT_TABS={
      training:'people',actions:'actions',safety:'safety',
      improvements:'improvements',agenda:'agenda',
      extinguishers:'extinguishers',inspections:'inspections'
    };
    Object.keys(CLIENT_TABS).forEach(key=>{
      if(CLIENT_SCOPES[key]===true)return;
      const target='tab-'+CLIENT_TABS[key];
      const tab=document.getElementById(target);
      if(tab)tab.hidden=true;
      const section=document.getElementById('panel-'+CLIENT_TABS[key]);
      if(section)section.hidden=true;
      document.querySelectorAll('[data-open-tab="'+target+'"]').forEach(button=>{
        const card=button.closest('.executive-module');
        if(card)card.hidden=true;
        else button.hidden=true;
      });
    });
    const scopeNote=document.createElement('div');
    scopeNote.className='panel privacy-panel';
    scopeNote.textContent='Visão de consulta autorizada pela Auditar. Módulos não liberados não fazem parte deste resumo; os dados completos permanecem no aplicativo interno.';
    const overview=document.getElementById('panel-overview');
    if(overview)overview.insertBefore(scopeNote,overview.firstChild);
'''
h=h.replace(marker,insertion+marker,1)
# Explicitly avoid click handlers on non-granted tabs.
h=h.replace("document.querySelectorAll('[role=\"tab\"]').forEach(button=>{button.addEventListener",
            "document.querySelectorAll('[role=\"tab\"]:not([hidden])').forEach(button=>{button.addEventListener",1)
h=h.replace("</style>","  [hidden]{display:none!important}\n  </style>",1)
html.write_text(h,encoding='utf-8',newline='\n')
print('AUDITAR_CLIENT_PANEL_SCOPED_PUBLICATION_OK')
