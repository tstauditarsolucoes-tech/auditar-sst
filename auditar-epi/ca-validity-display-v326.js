(()=>{
'use strict';
const APP_KEY='auditarEpiV1';
const $=(s,r=document)=>r.querySelector(s),$$=(s,r=document)=>[...r.querySelectorAll(s)];
function read(){
  try{return {companies:[],workers:[],epis:[],deliveries:[],...JSON.parse(localStorage.getItem(APP_KEY)||'{}')}}
  catch{return {companies:[],workers:[],epis:[],deliveries:[]}}
}
function clean(v=''){return String(v??'').trim()}
function decorateEpis(){
  const list=$('#epiList');if(!list)return;
  const a=read(),map=new Map((a.epis||[]).map(e=>[String(e.id),e]));
  $$('#epiList .list-item').forEach(row=>{
    const id=row.querySelector('[data-del-epi]')?.dataset.delEpi||'';
    const epi=map.get(String(id));if(!epi)return;
    const small=row.querySelector('.list-main small');if(!small)return;
    const old=row.querySelector('.ca-validity-v326');if(old)old.remove();
    const validity=clean(epi.caValidity);
    if(!validity)return;
    const span=document.createElement('span');
    span.className='ca-validity-v326';
    span.textContent=' • Validade CA '+validity;
    small.appendChild(span);
  });
}
function boot(){
  decorateEpis();
  [250,700,1500].forEach(ms=>setTimeout(decorateEpis,ms));
  document.addEventListener('click',e=>{
    if(e.target.closest?.('[data-go="epis"]'))setTimeout(decorateEpis,70);
  },true);
  document.addEventListener('auditar-epi-data-changed',()=>setTimeout(decorateEpis,90));
  document.addEventListener('gestao-epi-auth-ready',()=>setTimeout(decorateEpis,120));
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();