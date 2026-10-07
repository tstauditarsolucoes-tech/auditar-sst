(()=>{
'use strict';
const APP='auditarEpiV1',STOCK='auditarEpiStockV1';
const $=(s,r=document)=>r.querySelector(s),$$=(s,r=document)=>[...r.querySelectorAll(s)];
const esc=(v='')=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function read(k,f={}){try{return {...f,...JSON.parse(localStorage.getItem(k)||'{}')}}catch{return f}}
function fmt(v){if(!v)return '—';try{return new Intl.DateTimeFormat('pt-BR',{dateStyle:'short',timeStyle:'short'}).format(new Date(v))}catch{return String(v)}}
function field(note,key){const m=String(note||'').match(new RegExp('(?:^|\\|)\\s*'+key+'\\s*:\\s*([^|]+)','i'));return m?m[1].trim():''}
function data(){const a=read(APP,{companies:[],workers:[],epis:[],deliveries:[]}),s=read(STOCK,{movements:[]});for(const k of ['companies','workers','epis','deliveries'])a[k]=Array.isArray(a[k])?a[k]:[];s.movements=Array.isArray(s.movements)?s.movements:[];return {a,s}}
function evidenceText(d){const x=[];if(d.signature)x.push('assinatura');if(d.biometricVerified||d.biometricEvidenceId||d.confirmationMethod==='face-biometric')x.push('biometria');if(d.biometricEvidenceHash)x.push('hash de evidência');return x.join(' + ')||'sem evidência identificada'}
function timeline(workerId){
 const {a,s}=data(),epis=new Map(a.epis.map(e=>[e.id,e])),events=[];a.epiAuthorizations=Array.isArray(a.epiAuthorizations)?a.epiAuthorizations:[];
 a.epiAuthorizations.filter(x=>x.workerId===workerId).forEach(x=>{const items=(x.items||[]).map(i=>{const e=epis.get(i.approvedSubstituteEpiId||i.epiId)||{};return (e.name||'EPI')+' • autorizado '+Number(i.qty||0)+' • entregue '+Number((x.fulfilled||{})[i.epiId]||0)}).join(' | ');events.push({at:x.createdAt,type:'Liberação TST',icon:'🧾',title:x.code||'Liberação de EPI',detail:items||'Sem itens',meta:(x.authorizedBy?.name?'Liberado por '+x.authorizedBy.name+' • ':'')+'Status: '+String(x.status||'pending')+(x.expiresAt?' • validade '+fmt(x.expiresAt):'')})});
 a.deliveries.filter(d=>d.workerId===workerId&&d.cancelled!==true).forEach(d=>{
   const items=(d.items||[]).map(i=>{const e=epis.get(i.epiId)||{};return (e.name||'EPI')+(e.ca?' • CA '+e.ca:'')+' • qtd. '+Number(i.qty||0)}).join(' | ');
   const trace=d.authorizationCode?'Liberação '+d.authorizationCode:(d.deliveryMode==='direct-warehouse'?'Entrega direta pelo almoxarifado':'');events.push({at:d.createdAt,type:'Entrega',icon:'📦',title:(d.reason||'Entrega de EPI'),detail:items||'Sem itens identificados',meta:'Evidência: '+evidenceText(d)+(trace?' • '+trace:'')+(d.deliveredBy?.name?' • entregue por '+d.deliveredBy.name:''),receipt:d.id});
 });
 (s.movements||[]).forEach(m=>{
   const wid=m.workerId||field(m.note,'workerId');if(wid!==workerId)return;
   const note=String(m.note||''),e=epis.get(m.epiId)||{};
   if(note.startsWith('DEVOLUÇÃO EPI'))events.push({at:m.createdAt,type:'Devolução',icon:'↩️',title:e.name||'EPI',detail:'Quantidade devolvida: '+(field(note,'qtd')||Math.abs(Number(m.delta||0))),meta:note});
   else if(/troca|substitui/i.test(note))events.push({at:m.createdAt,type:'Troca',icon:'🔄',title:e.name||'EPI',detail:note,meta:''});
 });
 return events.sort((x,y)=>String(y.at||'').localeCompare(String(x.at||'')));
}
function style(){if($('#wh360Style'))return;const s=document.createElement('style');s.id='wh360Style';s.textContent=`
.wh360{margin-top:12px;border-top:1px solid #dce8e5;padding-top:12px}.wh360 h3{margin:0 0 8px;color:#173d39}.wh360-list{display:grid;gap:8px;max-height:300px;overflow:auto}.wh360-row{display:grid;grid-template-columns:34px 1fr;gap:9px;border:1px solid #e0e9e7;border-radius:12px;padding:9px;background:#fff}.wh360-icon{width:32px;height:32px;border-radius:10px;background:#edf7f5;display:grid;place-items:center}.wh360-row b{display:block;color:#173d39}.wh360-row small{display:block;color:#6d817d;margin-top:2px;line-height:1.35}.wh360-meta{font-size:10px;color:#80908d;margin-top:4px}.wh360-empty{padding:12px;border:1px dashed #cbdad8;border-radius:12px;color:#6d817d}`;document.head.appendChild(s)}
function inject(workerId){
 const box=$('#ux300Modal .ux300-sheet');
 if(!box||!workerId)return;
 $('#wh360Box')?.remove();const ev=timeline(workerId),sec=document.createElement('div');sec.id='wh360Box';sec.className='wh360';
 sec.innerHTML='<h3>Histórico 360°</h3><div class="wh360-list">'+(ev.length?ev.slice(0,30).map(x=>`<div class="wh360-row"><div class="wh360-icon">${x.icon}</div><div><b>${esc(x.type)} • ${esc(x.title)}</b><small>${esc(x.detail)}</small><div class="wh360-meta">${esc(fmt(x.at))}${x.meta?' • '+esc(x.meta):''}</div></div></div>`).join(''):'<div class="wh360-empty">Nenhuma movimentação registrada para este trabalhador.</div>')+'</div>';
 box.appendChild(sec);
}
function workerIdFromButton(btn){return btn?.dataset?.uxWorker||btn?.getAttribute?.('data-ux-worker')||''}
function boot(){style();document.addEventListener('click',e=>{const b=e.target.closest?.('[data-ux-worker]');if(b){const id=workerIdFromButton(b);setTimeout(()=>inject(id),80)}},true)}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();