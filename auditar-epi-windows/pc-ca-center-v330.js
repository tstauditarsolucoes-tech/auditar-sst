(()=>{
'use strict';
const CACHE='auditarEpiGestaoCacheV1';
const $=(s,r=document)=>r.querySelector(s),$$=(s,r=document)=>[...r.querySelectorAll(s)];
const esc=(v='')=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const norm=(v='')=>String(v??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim();
const digits=v=>String(v??'').replace(/\D/g,'');
const clean=v=>String(v??'').trim();
let busy=false;

function read(){
  try{
    const r=JSON.parse(localStorage.getItem(CACHE)||'{}');
    r.app=r.app&&typeof r.app==='object'?r.app:{};
    for(const k of ['companies','workers','epis','deliveries'])r.app[k]=Array.isArray(r.app[k])?r.app[k]:[];
    r.stock=r.stock&&typeof r.stock==='object'?r.stock:{};
    r.stock.movements=Array.isArray(r.stock.movements)?r.stock.movements:[];
    r.stock.minimums=r.stock.minimums&&typeof r.stock.minimums==='object'?r.stock.minimums:{};
    return r;
  }catch(_){return {app:{companies:[],workers:[],epis:[],deliveries:[]},stock:{movements:[],minimums:{}}}}
}
function write(r){r.updatedAt=new Date().toISOString();localStorage.setItem(CACHE,JSON.stringify(r));}
function toast(m){const e=$('#toast');if(!e)return alert(m);e.textContent=m;e.classList.add('show');setTimeout(()=>e.classList.remove('show'),2800)}
function canOperate(){return ['admin','campo'].includes(String(window.GestaoEpiAuth?.user?.()?.role||document.body.dataset.epiRole||''))}
function api(action,extra={}){if(!window.GestaoEpiAuth?.api)throw new Error('Faça login para consultar os CAs.');return window.GestaoEpiAuth.api(action,extra)}
function parseDate(v){
  const s=clean(v);if(!s)return null;
  let m=s.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
  if(m){const d=new Date(Number(m[3]),Number(m[2])-1,Number(m[1]),12);return Number.isNaN(d.getTime())?null:d}
  m=s.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if(m){const d=new Date(Number(m[1]),Number(m[2])-1,Number(m[3]),12);return Number.isNaN(d.getTime())?null:d}
  const d=new Date(s);return Number.isNaN(d.getTime())?null:d;
}
function fmtDate(v){const d=parseDate(v);if(!d)return clean(v)||'—';return new Intl.DateTimeFormat('pt-BR').format(d)}
function daysTo(v){const d=parseDate(v);if(!d)return null;const n=new Date();n.setHours(12,0,0,0);d.setHours(12,0,0,0);return Math.ceil((d-n)/86400000)}
function info(e){
  const ca=digits(e.ca),validity=clean(e.caValidity),status=clean(e.caValidationStatus||e.caStatus),checked=clean(e.caCheckedAt),days=daysTo(validity),st=norm(status);
  let key='ok',label='Regular',cls='ok';
  if(!ca){key='missing';label='Sem CA';cls='warn'}
  else if(/venc|expir|cancel|suspens|inativ|invalid|inval/.test(st)||(days!=null&&days<0)){key='expired';label='Vencido/irregular';cls='bad'}
  else if(!validity){key='no-validity';label='Sem validade';cls='warn'}
  else if(days<=30){key='30';label='Vence em '+Math.max(0,days)+' dia(s)';cls='bad'}
  else if(days<=60){key='60';label='Vence em '+days+' dia(s)';cls='warn'}
  else if(days<=90){key='90';label='Vence em '+days+' dia(s)';cls='warn'}
  else if(!checked){key='unchecked';label='Sem consulta recente';cls='warn'}
  return {ca,validity,status,checked,days,key,label,cls};
}
function matches(e,f){
  const x=info(e);
  if(f==='all')return true;
  if(f==='expired')return x.key==='expired';
  if(f==='30')return x.days!=null&&x.days>=0&&x.days<=30;
  if(f==='60')return x.days!=null&&x.days>=0&&x.days<=60;
  if(f==='90')return x.days!=null&&x.days>=0&&x.days<=90;
  if(f==='no-validity')return !!x.ca&&!x.validity;
  if(f==='unchecked')return !!x.ca&&!x.checked;
  if(f==='missing')return !x.ca;
  return true;
}
function stats(rows){
  const o={total:rows.length,expired:0,d30:0,noValidity:0,unchecked:0};
  rows.forEach(e=>{const x=info(e);if(x.key==='expired')o.expired++;if(x.days!=null&&x.days>=0&&x.days<=30)o.d30++;if(x.ca&&!x.validity)o.noValidity++;if(x.ca&&!x.checked)o.unchecked++;});
  return o;
}
function installStyles(){
  if($('#pc330CaStyle'))return;
  const s=document.createElement('style');s.id='pc330CaStyle';s.textContent=`
    #caSmartPc .pc330-ca-kpis{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:8px;margin-bottom:12px}
    #caSmartPc .pc330-ca-kpi{background:#fff;border:1px solid #dbe8e5;border-radius:12px;padding:11px;min-width:0}
    #caSmartPc .pc330-ca-kpi strong{display:block;color:#173d39;font-size:20px}#caSmartPc .pc330-ca-kpi span{font-size:9px;color:#6c817d}
    #caSmartPc .pc330-ca-actions{display:flex;gap:7px;align-items:center;flex-wrap:wrap}
    #caSmartPc .pc330-ca-badge{display:inline-flex;border-radius:999px;padding:4px 7px;font-size:8px;font-weight:900}
    #caSmartPc .pc330-ca-badge.ok{background:#ecfdf3;color:#166534}#caSmartPc .pc330-ca-badge.warn{background:#fff8e6;color:#8a6418}#caSmartPc .pc330-ca-badge.bad{background:#fff0ee;color:#b42318}
    #caSmartPc .pc330-ca-sub{display:block;margin-top:3px;color:#70847f;font-size:8.5px;line-height:1.35}
    @media(max-width:1100px){#caSmartPc .pc330-ca-kpis{grid-template-columns:repeat(3,minmax(0,1fr))}}
  `;document.head.appendChild(s);
}
function prepare(){
  const view=$('#caSmartPc');if(!view)return false;
  const title=view.querySelector('.v25h h2'),sub=view.querySelector('.v25h p');
  if(title)title.textContent='🛡️ Central de CA';
  if(sub)sub.textContent='Validade, situação e última consulta dos Certificados de Aprovação.';
  const nav=$('.sidebar .nav[data-view="caSmartPc"] span');if(nav)nav.textContent='Central de CA';
  const filter=$('#v25CaFilter');
  if(filter&&!filter.dataset.pc330){
    filter.dataset.pc330='1';
    filter.innerHTML='<option value="all">Todos</option><option value="expired">Vencidos/irregulares</option><option value="30">Vencem em 30 dias</option><option value="60">Vencem em 60 dias</option><option value="90">Vencem em 90 dias</option><option value="no-validity">Sem validade</option><option value="unchecked">Sem consulta</option><option value="missing">Sem CA</option>';
  }
  const head=view.querySelector('.v25h');
  if(head&&!$('#pc330CaUpdateAll')){
    const right=head.lastElementChild;
    const wrap=document.createElement('span');wrap.className='pc330-ca-actions';
    wrap.innerHTML='<button id="pc330CaUpdateAll" class="v25btn p" type="button">↻ Atualizar CAs</button>';
    if(right&&right!==head.firstElementChild)right.insertAdjacentElement('beforebegin',wrap);else head.appendChild(wrap);
    $('#pc330CaUpdateAll').addEventListener('click',updateAll);
  }
  const oldK=$('#v25CaK');
  if(oldK){oldK.className='pc330-ca-kpis';}
  return true;
}
function render(){
  if(!prepare())return;
  const root=read(),all=root.app.epis.filter(e=>e.active!==false),q=norm($('#v25CaSearch')?.value||''),f=$('#v25CaFilter')?.value||'all',st=stats(all);
  $('#v25CaK').innerHTML=`<div class="pc330-ca-kpi"><strong>${st.total}</strong><span>EPIs ativos</span></div><div class="pc330-ca-kpi"><strong>${st.expired}</strong><span>vencidos/irregulares</span></div><div class="pc330-ca-kpi"><strong>${st.d30}</strong><span>vencem em 30 dias</span></div><div class="pc330-ca-kpi"><strong>${st.noValidity}</strong><span>sem validade</span></div><div class="pc330-ca-kpi"><strong>${st.unchecked}</strong><span>sem consulta</span></div>`;
  const rank=x=>x.key==='expired'?0:x.key==='30'?1:x.key==='60'?2:x.key==='90'?3:x.key==='no-validity'?4:x.key==='unchecked'?5:x.key==='missing'?6:7;
  const rows=all.filter(e=>matches(e,f)&&(!q||[e.name,e.ca,e.model,e.caManufacturer,e.caValidationStatus].some(v=>norm(v).includes(q)))).sort((a,b)=>rank(info(a))-rank(info(b))||String(a.name||'').localeCompare(String(b.name||'')));
  $('#v25CaTable').innerHTML=rows.length?`<table class="v25t"><thead><tr><th>EPI</th><th>CA</th><th>Validade</th><th>Situação</th><th>Última consulta</th><th>Fabricante / modelo</th><th>Ações</th></tr></thead><tbody>${rows.map(e=>{const x=info(e);return `<tr><td><b>${esc(e.name||'EPI')}</b><span class="pc330-ca-sub">${esc(e.size?'Tam. '+e.size:'')}</span></td><td>${esc(x.ca||'—')}</td><td>${esc(x.validity?fmtDate(x.validity):'—')}</td><td><span class="pc330-ca-badge ${x.cls}">${esc(x.label)}</span>${x.status?`<span class="pc330-ca-sub">${esc(x.status)}</span>`:''}</td><td>${x.checked?esc(fmtDate(x.checked)):'—'}</td><td>${esc(e.caManufacturer||e.model||'—')}</td><td><div class="pc330-ca-actions"><button class="v25btn p" data-pc330-ca="${esc(e.id)}" type="button">↻ Atualizar</button><button class="v25btn" data-pc330-source="${esc(e.id)}" type="button">Fonte oficial</button></div></td></tr>`}).join('')}</tbody></table>`:'<div class="empty">Nenhum EPI encontrado neste filtro.</div>';
}
function applyCheck(e,c){
  e.caCheckedAt=new Date().toISOString();
  e.caCheckedBy=String(window.GestaoEpiAuth?.user?.()?.name||window.GestaoEpiAuth?.user?.()?.username||'');
  e.caValidationStatus=String(c?.status|| (c?.found===false?'Não confirmado':''));
  e.caValidity=String(c?.validity||'');
  e.caEquipment=String(c?.equipment||'');
  e.caManufacturer=String(c?.manufacturer||'');
  e.caSourceUrl=String(c?.sourceUrl||e.caSourceUrl||'');
  e.caSourceType=String(c?.sourceType||e.caSourceType||'');
  e.updatedAt=new Date().toISOString();
}
async function query(items){
  const res=await api('tenant_ai_assistant',{payload:{mode:'ca_validate',items:items.map(e=>({ca:digits(e.ca),name:e.name||'',manufacturer:e.model||e.manufacturer||''}))}});
  if(!res?.ok)throw new Error(res?.message||'Falha na consulta dos CAs.');
  return Array.isArray(res?.result?.checks)?res.result.checks:[];
}
async function updateOne(id){
  if(busy)return;if(!canOperate())return toast('Seu perfil é somente consulta.');
  const root=read(),e=root.app.epis.find(x=>x.id===id);if(!e?.ca)return toast('Este EPI não possui CA informado.');
  busy=true;try{
    const checks=await query([e]),c=checks.find(x=>digits(x.ca)===digits(e.ca));
    if(!c)throw new Error('A consulta não retornou dados para este CA.');
    applyCheck(e,c);write(root);toast('CA atualizado.');render();
  }catch(err){toast(err?.message||'Não foi possível atualizar o CA.')}finally{busy=false}
}
async function updateAll(){
  if(busy)return;if(!canOperate())return toast('Seu perfil é somente consulta.');
  const root=read(),rows=root.app.epis.filter(e=>e.active!==false&&digits(e.ca));if(!rows.length)return toast('Nenhum EPI com CA para consultar.');
  busy=true;const btn=$('#pc330CaUpdateAll');if(btn)btn.disabled=true;let done=0;
  try{
    for(let i=0;i<rows.length;i+=20){
      const batch=rows.slice(i,i+20),checks=await query(batch),map=new Map(checks.map(c=>[digits(c.ca),c]));
      batch.forEach(e=>{const c=map.get(digits(e.ca));if(c){applyCheck(e,c);done++;}});
      write(root);render();
    }
    toast(done+' CA(s) atualizado(s).');
  }catch(err){toast(err?.message||'Falha ao atualizar os CAs.')}finally{busy=false;if(btn)btn.disabled=false;render()}
}
function openSource(id){
  const e=read().app.epis.find(x=>x.id===id);if(!e)return;
  const u=String(e.caSourceUrl||'').trim()||('https://caepi.mte.gov.br/internet/ConsultaCAInternet.aspx?txtNumeroCA='+encodeURIComponent(digits(e.ca)));
  window.open(u,'_blank');
}
function boot(){
  installStyles();
  [0,120,500].forEach(ms=>setTimeout(()=>{prepare();if($('#caSmartPc')?.classList.contains('active'))render()},ms));
  $('#v25CaSearch')?.addEventListener('input',()=>setTimeout(render,0));
  $('#v25CaFilter')?.addEventListener('change',()=>setTimeout(render,0));
  document.addEventListener('click',e=>{
    const nav=e.target.closest?.('.nav[data-view="caSmartPc"]');if(nav)setTimeout(render,30);
    const b=e.target.closest?.('[data-pc330-ca]');if(b){e.preventDefault();updateOne(b.dataset.pc330Ca);return}
    const src=e.target.closest?.('[data-pc330-source]');if(src){e.preventDefault();openSource(src.dataset.pc330Source)}
  },true);
  window.addEventListener('storage',e=>{if(e.key===CACHE&&$('#caSmartPc')?.classList.contains('active'))setTimeout(render,30)});
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();