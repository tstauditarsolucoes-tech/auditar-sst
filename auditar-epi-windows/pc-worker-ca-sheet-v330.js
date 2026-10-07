(()=>{
'use strict';
const CACHE='auditarEpiGestaoCacheV1';
const $=(s,r=document)=>r.querySelector(s),$$=(s,r=document)=>[...r.querySelectorAll(s)];
const esc=(v='')=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let currentWorkerId='';

function read(){
  try{
    const r=JSON.parse(localStorage.getItem(CACHE)||'{}');
    r.app=r.app&&typeof r.app==='object'?r.app:{};
    for(const k of ['companies','workers','epis','deliveries'])r.app[k]=Array.isArray(r.app[k])?r.app[k]:[];
    return r;
  }catch(_){return {app:{companies:[],workers:[],epis:[],deliveries:[]}}}
}
function fmt(v,withTime=false){if(!v)return '—';try{return new Intl.DateTimeFormat('pt-BR',withTime?{dateStyle:'short',timeStyle:'short'}:{dateStyle:'short'}).format(new Date(v))}catch(_){return String(v)}}
function workerData(id){
  const r=read(),w=r.app.workers.find(x=>x.id===id);if(!w)return null;
  const c=r.app.companies.find(x=>x.id===w.companyId)||{};
  const em=new Map(r.app.epis.map(e=>[e.id,e]));
  const deliveries=r.app.deliveries.filter(d=>d.workerId===id&&d.cancelled!==true).sort((a,b)=>String(b.createdAt||'').localeCompare(String(a.createdAt||'')));
  const qty=new Map(),last=new Map();
  deliveries.forEach(d=>(d.items||[]).forEach(i=>{qty.set(i.epiId,(qty.get(i.epiId)||0)+Number(i.qty||0));const cur=last.get(i.epiId);if(!cur||String(d.createdAt||'')>String(cur.createdAt||''))last.set(i.epiId,d)}));
  (w.epiReturns||[]).forEach(x=>qty.set(x.epiId,(qty.get(x.epiId)||0)-Number(x.qty||0)));
  const rows=[...qty.entries()].map(([epiId,q])=>{
    const e=em.get(epiId)||{},d=last.get(epiId),cycle=Number(e.cycle||0);
    let due='';if(d?.createdAt&&cycle){const dt=new Date(d.createdAt);if(!Number.isNaN(dt.getTime()))due=new Date(dt.getTime()+cycle*86400000).toISOString()}
    return {e,qty:Math.max(0,q),last:d?.createdAt||'',due};
  }).filter(x=>x.qty>0).sort((a,b)=>String(a.e.name||'').localeCompare(String(b.e.name||'')));
  return {r,w,c,rows};
}
function styles(){
  if($('#pc330WorkerCaStyle'))return;
  const s=document.createElement('style');s.id='pc330WorkerCaStyle';s.textContent=`
    .pc330-worker-ca-summary{margin-top:18px}.pc330-worker-ca-summary h2{font-size:14px;color:#173d39;margin:0 0 9px}
    .pc330-worker-ca-table{width:100%;border-collapse:collapse;font-size:10px}.pc330-worker-ca-table th,.pc330-worker-ca-table td{border:1px solid #d7e3e0;padding:8px;text-align:left;vertical-align:top}.pc330-worker-ca-table th{background:#f1f7f6;color:#4d6863;font-size:9px;text-transform:uppercase}
    .pc330-ca-print-paper{display:none;background:#fff;color:#222}
    @media print{
      body.pc330-ca-printing *{visibility:hidden!important}
      body.pc330-ca-printing .pc330-ca-print-paper,body.pc330-ca-printing .pc330-ca-print-paper *{visibility:visible!important}
      body.pc330-ca-printing .pc330-ca-print-paper{display:block!important;position:absolute!important;left:0!important;top:0!important;width:100%!important;padding:10mm!important;box-sizing:border-box!important}
      body.pc330-ca-printing .pc330-ca-print-paper h1{font-size:18px;text-align:center;margin:0 0 5px}
      body.pc330-ca-printing .pc330-ca-print-paper h2{font-size:12px;text-align:center;margin:0 0 14px;font-weight:500}
      body.pc330-ca-printing .pc330-ca-print-paper table{width:100%;border-collapse:collapse;font-size:8.5px}
      body.pc330-ca-printing .pc330-ca-print-paper th,body.pc330-ca-printing .pc330-ca-print-paper td{border:1px solid #aaa;padding:5px;vertical-align:top}
      body.pc330-ca-printing .pc330-ca-print-paper th{background:#eee!important;-webkit-print-color-adjust:exact;print-color-adjust:exact}
    }
  `;document.head.appendChild(s);
}
function ensureButton(){
  const actions=$('#workerSheetPc .worker-sheet-toolbar .actions');if(!actions||$('#workerCaSheetPrint'))return;
  const b=document.createElement('button');b.id='workerCaSheetPrint';b.className='secondary';b.type='button';b.textContent='📄 Ficha de CA';b.addEventListener('click',printCaSheet);actions.appendChild(b);
}
function renderSummary(){
  if(!currentWorkerId)return;const d=workerData(currentWorkerId),paper=$('#workerSheetPaper');if(!d||!paper)return;
  $('#pc330WorkerCaSummary')?.remove();
  const sec=document.createElement('div');sec.id='pc330WorkerCaSummary';sec.className='worker-sheet-section pc330-worker-ca-summary';
  sec.innerHTML='<h2>EPIs em posse • CA e validade</h2>'+(d.rows.length?`<table class="pc330-worker-ca-table"><thead><tr><th>EPI</th><th>CA</th><th>Validade do CA</th><th>Qtd. em posse</th><th>Próxima troca</th></tr></thead><tbody>${d.rows.map(x=>`<tr><td><b>${esc(x.e.name||'EPI')}</b></td><td>${esc(x.e.ca||'—')}</td><td>${esc(x.e.caValidity||'—')}</td><td>${x.qty}</td><td>${x.due?fmt(x.due):'—'}</td></tr>`).join('')}</tbody></table>`:'<div class="worker-sheet-empty">Nenhum EPI em posse.</div>');
  const metrics=paper.querySelector('.worker-sheet-metrics');if(metrics)metrics.insertAdjacentElement('afterend',sec);else paper.prepend(sec);
}
function printCaSheet(){
  const d=workerData(currentWorkerId);if(!d)return;
  let paper=$('#pc330CaPrintPaper');if(!paper){paper=document.createElement('article');paper.id='pc330CaPrintPaper';paper.className='pc330-ca-print-paper';document.body.appendChild(paper)}
  const rows=d.rows.length?d.rows.map(x=>`<tr><td>${esc(x.e.name||'EPI')}</td><td>${esc(x.e.ca||'—')}</td><td>${esc(x.e.caValidity||'—')}</td><td>${esc(x.e.caValidationStatus||'—')}</td><td>${esc(x.e.caManufacturer||x.e.model||'—')}</td><td>${esc(x.e.size||'—')}</td><td>${x.qty}</td><td>${x.last?fmt(x.last):'—'}</td><td>${x.due?fmt(x.due):'—'}</td><td>${x.e.caCheckedAt?fmt(x.e.caCheckedAt,true):'—'}</td></tr>`).join(''):'<tr><td colspan="10">Nenhum EPI em posse.</td></tr>';
  paper.innerHTML=`<h1>FICHA DE CA DOS EPIs</h1><h2>Gestão EPI • Auditar</h2><p><b>Empresa:</b> ${esc(d.c.name||'—')}${d.c.cnpj?'<br><b>CNPJ:</b> '+esc(d.c.cnpj):''}<br><b>Trabalhador:</b> ${esc(d.w.name||'—')}<br><b>Matrícula:</b> ${esc(d.w.reg||'—')} &nbsp; <b>Cargo:</b> ${esc(d.w.role||'—')} &nbsp; <b>Setor:</b> ${esc(d.w.sector||'—')}</p><table><thead><tr><th>EPI</th><th>CA</th><th>Validade CA</th><th>Situação</th><th>Fabricante / Modelo</th><th>Tamanho</th><th>Qtd. em posse</th><th>Última entrega</th><th>Próxima troca</th><th>CA consultado em</th></tr></thead><tbody>${rows}</tbody></table><p style="font-size:8.5px;margin-top:12px">A validade e a situação são apresentadas conforme os dados de CA registrados/consultados pelo sistema. Esta ficha apoia a rastreabilidade dos EPIs vinculados ao trabalhador.</p><p style="font-size:8px;margin-top:7px">Emitido em ${fmt(new Date().toISOString(),true)}.</p>`;
  document.body.classList.add('pc330-ca-printing');setTimeout(()=>window.print(),60);
}
function cleanup(){document.body.classList.remove('pc330-ca-printing')}
function boot(){
  styles();ensureButton();
  [100,400].forEach(ms=>setTimeout(ensureButton,ms));
  document.addEventListener('click',e=>{const b=e.target.closest?.('[data-worker-sheet]');if(b){currentWorkerId=b.dataset.workerSheet;setTimeout(()=>{ensureButton();renderSummary()},35)}},true);
  window.addEventListener('afterprint',cleanup);
  window.addEventListener('storage',e=>{if(e.key===CACHE&&currentWorkerId&&$('#workerSheetPc')?.classList.contains('active'))setTimeout(renderSummary,30)});
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();