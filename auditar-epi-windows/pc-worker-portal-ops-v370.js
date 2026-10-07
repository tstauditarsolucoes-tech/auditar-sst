(()=>{
'use strict';
const PC=!!document.querySelector('.sidebar')&&!!document.querySelector('#syncStatus');
const APP='auditarEpiV1',STOCK='auditarEpiStockV1',CACHE='auditarEpiGestaoCacheV1',REV='auditarEpiServerRevision';
const $=(s,r=document)=>r.querySelector(s),$$=(s,r=document)=>[...r.querySelectorAll(s)];
const esc=(v='')=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const norm=(v='')=>String(v??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim();
const now=()=>new Date().toISOString(),uid=p=>p+'_'+Date.now()+'_'+Math.random().toString(36).slice(2,8);

function read(){
 try{
  if(PC){
   const r=JSON.parse(localStorage.getItem(CACHE)||'{}');r.app=r.app||{};for(const k of ['companies','workers','epis','deliveries','auditLog'])r.app[k]=Array.isArray(r.app[k])?r.app[k]:[];r.stock=r.stock||{};r.stock.movements=Array.isArray(r.stock.movements)?r.stock.movements:[];return r;
  }
  const app=JSON.parse(localStorage.getItem(APP)||'{}'),stock=JSON.parse(localStorage.getItem(STOCK)||'{}');for(const k of ['companies','workers','epis','deliveries','auditLog'])app[k]=Array.isArray(app[k])?app[k]:[];stock.movements=Array.isArray(stock.movements)?stock.movements:[];return {version:1,revision:Number(localStorage.getItem(REV)||0),updatedAt:now(),app,stock};
 }catch(_){return {version:1,revision:0,app:{companies:[],workers:[],epis:[],deliveries:[],auditLog:[]},stock:{movements:[],minimums:{}}}}
}
function write(r){
 r.updatedAt=now();
 if(PC)localStorage.setItem(CACHE,JSON.stringify(r));else{localStorage.setItem(APP,JSON.stringify(r.app));localStorage.setItem(STOCK,JSON.stringify(r.stock));document.dispatchEvent(new CustomEvent('auditar-epi-data-changed',{detail:{source:'worker-portal-ops-v370'}}))}
}
function user(){return window.GestaoEpiAuth?.user?.()||{}}
function who(){const u=user();return {username:String(u.username||''),name:String(u.name||u.username||''),role:String(u.role||'')}}
function profiles(r){return (r.app.auditLog||[]).filter(x=>x?.type==='epi_user_profile')}
function profile(r=read()){const u=user();if(!u.username)return'none';if(u.role==='admin')return'both';if(u.role==='consulta')return'none';const p=profiles(r).find(x=>norm(x.username)===norm(u.username));return String(p?.profile||'both')}
function canTst(){return ['tst','both'].includes(profile())||user().role==='admin'}
function settings(r,c){return (r.app.auditLog||[]).find(x=>x?.type==='epi_flow_settings'&&x.companyId===c)||{id:'flowset_'+c,type:'epi_flow_settings',companyId:c,directDeliveryAllowed:true,defaultExpiryDays:5,reserveStock:true}}
function auths(r){return (r.app.auditLog||[]).filter(x=>x?.type==='epi_authorization')}
function requests(r){return (r.app.auditLog||[]).filter(x=>x?.type==='worker_epi_request')}
function upsert(r,row){const a=r.app.auditLog||[],i=a.findIndex(x=>x.id===row.id);if(i>=0)a[i]=row;else a.unshift(row);r.app.auditLog=a}
function workerName(r,id){return r.app.workers.find(x=>x.id===id)?.name||'Trabalhador'}
function epiName(r,id){const e=r.app.epis.find(x=>x.id===id);return e?e.name+(e.ca?' • CA '+e.ca:''):'EPI'}
function balance(r,c,e){return (r.stock.movements||[]).filter(m=>m.companyId===c&&m.epiId===e).reduce((s,m)=>s+Number(m.delta||0),0)}
function remaining(i){return Math.max(0,Number(i.qty||0)-Number(i.deliveredQty||0))}
function statusOf(a){if(a.status==='cancelled'||a.status==='delivered')return a.status;if(a.expiresAt&&Date.now()>Date.parse(a.expiresAt))return'expired';const rem=(a.items||[]).reduce((s,i)=>s+remaining(i),0);if(rem<=0)return'delivered';if((a.items||[]).some(i=>Number(i.deliveredQty||0)>0))return'partial';return'pending'}
function effectiveEpi(i){return i?.substitution?.status==='approved'&&i.substitution.toEpiId?i.substitution.toEpiId:i.epiId}
function reserved(r,c,e){return auths(r).filter(a=>a.companyId===c&&['pending','partial'].includes(statusOf(a))).reduce((s,a)=>s+(a.items||[]).reduce((q,i)=>effectiveEpi(i)===e?q+remaining(i):q,0),0)}
function available(r,c,e){return balance(r,c,e)-reserved(r,c,e)}
function toast(m){const t=$('#toast');if(t){t.textContent=m;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),2600)}else alert(m)}
async function sync(){
 try{const api=window.GestaoEpiAuth?.api;if(!api)return false;const r=read(),res=await api('epi_sync_merge',{deviceId:window.GestaoEpiAuth?.deviceId?.()||'',client:PC?'gestao':'campo',payload:r});if(!res?.ok)throw new Error(res?.message||'Falha na sincronização.');const remote=res.payload||r;if(PC)localStorage.setItem(CACHE,JSON.stringify(remote));else{localStorage.setItem(APP,JSON.stringify(remote.app||{}));localStorage.setItem(STOCK,JSON.stringify(remote.stock||{}));localStorage.setItem(REV,String(res.revision||remote.revision||0))}document.dispatchEvent(new CustomEvent('gestao-epi-sync-applied'));return true}catch(e){toast(e?.message||'Falha ao sincronizar.');return false}
}
function statusLabel(x){return x==='submitted'?'Enviada':x==='reviewing'?'Em análise':x==='approved'?'Aprovada':x==='rejected'?'Não aprovada':x==='fulfilled'?'Concluída':x}
function style(){if($('#portal370Style'))return;const s=document.createElement('style');s.id='portal370Style';s.textContent=`
.portal370-row{border:1px solid #dce8e5;border-radius:12px;padding:10px;display:grid;grid-template-columns:1fr auto;gap:10px;align-items:center}.portal370-row small{display:block;color:#6d817d;margin-top:3px;line-height:1.4}.portal370-actions{display:flex;gap:6px;flex-wrap:wrap;justify-content:flex-end}.portal370-actions button{border:1px solid #cfe0dc;background:#fff;border-radius:9px;padding:7px 9px;font-weight:850;color:#285f58}.portal370-actions .primary{background:#0f766e;color:#fff;border-color:#0f766e}.portal370-actions .danger{background:#fff0ee;color:#b42318}.portal370-badge{display:inline-block;border-radius:999px;padding:5px 8px;font-size:9px;font-weight:900}.portal370-badge.submitted,.portal370-badge.reviewing{background:#edf6ff;color:#24588d}.portal370-badge.approved,.portal370-badge.fulfilled{background:#ecfdf3;color:#166534}.portal370-badge.rejected{background:#fff0ee;color:#b42318}.portal370-settings{display:grid;grid-template-columns:1fr 1fr;gap:8px}.portal370-settings label{display:grid;gap:4px}.portal370-settings input,.portal370-settings select{border:1px solid #cfe0dc;border-radius:9px;padding:8px;background:#fff}.portal370-kpi{margin-top:7px;font-size:10px;font-weight:900;color:#0f766e}@media(max-width:700px){.portal370-row{grid-template-columns:1fr}.portal370-actions{justify-content:flex-start}.portal370-settings{grid-template-columns:1fr}}
`;document.head.appendChild(s)}
function ensureTab(){
 const tabs=$('#flow350Tabs');if(!tabs||tabs.querySelector('[data-flowtab="portalRequests370"]'))return;const b=document.createElement('button');b.dataset.flowtab='portalRequests370';b.textContent='Solicitações';tabs.appendChild(b);
}
function ensureCentral(){
 const target=PC?$('#operationsPc340 .pc340-kpis'):$('#operationsCenterV340 .ops340-kpis');if(!target)return;const r=read(),count=requests(r).filter(x=>['submitted','reviewing'].includes(String(x.status||''))).length;let card=$('#portal370Central');if(!card){card=document.createElement('div');card.id='portal370Central';card.className=PC?'pc340-kpi':'ops340-kpi';card.style.cursor='pointer';target.appendChild(card);card.onclick=openRequests}card.innerHTML='<strong>'+count+'</strong><span>solicitações do trabalhador</span><div class="portal370-kpi">Abrir solicitações</div>';
}
function openFlow(){const n=PC?$('.sidebar .nav[data-view="epiFlowV350"]'):$('[data-go="epiFlowV350"]');n?.click()}
function openRequests(){openFlow();setTimeout(()=>{ensureTab();renderRequests()},100)}
function renderRequests(){
 if(!canTst())return toast('Seu perfil não possui permissão para analisar solicitações.');
 ensureTab();$$('#flow350Tabs [data-flowtab]').forEach(b=>b.classList.toggle('active',b.dataset.flowtab==='portalRequests370'));const box=$('#flow350Content');if(!box)return;
 const r=read(),rows=requests(r).slice().sort((a,b)=>String(b.createdAt||'').localeCompare(String(a.createdAt||''))),companies=r.app.companies.filter(c=>c.active!==false);
 box.innerHTML=`<div class="flow350-card"><h3>Solicitações do trabalhador</h3><p class="flow350-note">Pedidos enviados pelo Portal. Aprovar uma troca cria uma liberação para retirada no almoxarifado.</p><div class="flow350-list">${rows.map(x=>rowHtml(r,x)).join('')||'<div class="flow350-note">Nenhuma solicitação registrada.</div>'}</div></div>${user().role==='admin'?portalSettingsHtml(r,companies):''}`;
 $$('[data-portal-review]').forEach(b=>b.onclick=()=>setStatus(b.dataset.portalReview,'reviewing'));
 $$('[data-portal-approve]').forEach(b=>b.onclick=()=>approve(b.dataset.portalApprove));
 $$('[data-portal-reject]').forEach(b=>b.onclick=()=>setStatus(b.dataset.portalReject,'rejected'));
 if(user().role==='admin')bindSettings(r);
}
function rowHtml(r,x){const st=String(x.status||'submitted');return `<div class="portal370-row"><div><b>${esc(workerName(r,x.workerId))} • ${esc(epiName(r,x.epiId))}</b><small>${x.category==='problem'?'Problema comunicado':'Solicitação de troca'} • ${esc(x.reason||'Outro')} • ${esc(new Date(x.createdAt||Date.now()).toLocaleString('pt-BR'))}${x.note?'<br>'+esc(x.note):''}${x.authorizationId?'<br>Liberação vinculada: '+esc(x.authorizationId):''}</small></div><div class="portal370-actions"><span class="portal370-badge ${esc(st)}">${esc(statusLabel(st))}</span>${['submitted'].includes(st)?'<button data-portal-review="'+esc(x.id)+'">Em análise</button>':''}${['submitted','reviewing'].includes(st)?'<button class="primary" data-portal-approve="'+esc(x.id)+'">Aprovar e liberar</button><button class="danger" data-portal-reject="'+esc(x.id)+'">Rejeitar</button>':''}</div></div>`}
async function setStatus(id,status){const r=read(),x=requests(r).find(a=>a.id===id);if(!x)return;x.status=status;x.decidedAt=now();x.decidedBy=who();x.updatedAt=now();upsert(r,x);write(r);await sync();toast(status==='reviewing'?'Solicitação marcada em análise.':'Solicitação não aprovada.');renderRequests()}
async function approve(id){
 const r=read(),x=requests(r).find(a=>a.id===id);if(!x)return;const set=settings(r,x.companyId),qty=1;if(set.reserveStock!==false&&available(r,x.companyId,x.epiId)<qty)return toast('Estoque disponível insuficiente para liberar este EPI.');
 const created=now(),days=Math.max(1,Math.min(30,Number(set.defaultExpiryDays||5))),authId=uid('auth'),u=who(),auth={id:authId,type:'epi_authorization',code:'LIB-'+authId.replace(/[^A-Za-z0-9]/g,'').slice(-8).toUpperCase(),companyId:x.companyId,workerId:x.workerId,items:[{epiId:x.epiId,qty:1,deliveredQty:0}],reason:x.category==='problem'?'Atendimento de problema informado no Portal':'Solicitação de troca pelo trabalhador',note:(x.reason||'')+(x.note?' • '+x.note:''),status:'pending',authorizedBy:u,authorizedAt:created,createdAt:created,updatedAt:created,expiresAt:new Date(Date.now()+days*86400000).toISOString(),sourceRequestId:x.id};
 x.status='approved';x.authorizationId=authId;x.decidedAt=created;x.decidedBy=u;x.updatedAt=created;upsert(r,auth);upsert(r,x);write(r);await sync();toast('Solicitação aprovada e EPI liberado para retirada.');renderRequests()
}
function portalSettingsHtml(r,companies){const c=companies[0]?.id||'';return `<div class="flow350-card"><h3>Contato exibido no Portal</h3><p class="flow350-note">Configure telefone e e-mail do SST/almoxarifado por empresa.</p><div class="portal370-settings"><label>Empresa<select id="portal370Company">${companies.map(x=>'<option value="'+esc(x.id)+'">'+esc(x.name)+'</option>').join('')}</select></label><label>Telefone<input id="portal370Phone" placeholder="Ex.: (86) 99999-9999"></label><label>E-mail<input id="portal370Email" type="email" placeholder="sst@empresa.com.br"></label><div style="align-self:end"><button class="flow350-btn primary" id="portal370Save">Salvar contato</button></div></div></div>`}
function bindSettings(r){
 const sel=$('#portal370Company'),load=()=>{const st=settings(read(),sel.value);$('#portal370Phone').value=st.portalContactPhone||'';$('#portal370Email').value=st.portalContactEmail||''};sel.onchange=load;load();$('#portal370Save').onclick=async()=>{const root=read(),c=sel.value,old=settings(root,c),row={...old,id:old.id||'flowset_'+c,type:'epi_flow_settings',companyId:c,portalContactPhone:$('#portal370Phone').value.trim(),portalContactEmail:$('#portal370Email').value.trim(),updatedAt:now(),createdAt:old.createdAt||now(),updatedBy:who()};upsert(root,row);write(root);await sync();toast('Contato do Portal atualizado.')};
}
function bind(){
 document.addEventListener('click',e=>{const b=e.target.closest?.('[data-flowtab="portalRequests370"]');if(b){e.preventDefault();e.stopImmediatePropagation();renderRequests()}},true);
 [600,1400,3000].forEach(ms=>setTimeout(()=>{ensureTab();ensureCentral()},ms));
 document.addEventListener('gestao-epi-sync-applied',()=>setTimeout(()=>{ensureTab();ensureCentral();if($('#epiFlowV350')?.classList.contains('active')&&$('[data-flowtab="portalRequests370"]')?.classList.contains('active'))renderRequests()},100));
 document.addEventListener('auditar-epi-data-changed',()=>setTimeout(ensureCentral,100));
}
function boot(){style();bind()}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();