(()=>{
'use strict';
const PC=!!document.querySelector('.sidebar')&&!!document.querySelector('#syncStatus');
const APP='auditarEpiV1',STOCK='auditarEpiStockV1',CACHE='auditarEpiGestaoCacheV1',REV='auditarEpiServerRevision';
const $=(s,r=document)=>r.querySelector(s),$$=(s,r=document)=>[...r.querySelectorAll(s)];
const esc=(v='')=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const norm=(v='')=>String(v??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim();
const now=()=>new Date().toISOString();

const MODULES=[
 {id:'delivery',label:'Entregas',desc:'Nova entrega e entrega em lote',cat:'Operação'},
 {id:'workers',label:'Trabalhadores',desc:'Cadastro, ficha, QR e externos',cat:'Operação'},
 {id:'epis',label:'EPIs',desc:'Cadastro de EPI',cat:'Operação'},
 {id:'stock',label:'Estoque',desc:'Saldo, entradas e movimentações',cat:'Operação'},
 {id:'history',label:'Histórico e comprovantes',desc:'Entregas, fichas e comprovantes',cat:'Operação'},
 {id:'replacements',label:'Trocas e devoluções',desc:'Posse, troca, devolução e desligamento',cat:'Operação'},
 {id:'ca',label:'Central de CA',desc:'Consulta e conferência de CA',cat:'Controle'},
 {id:'invoices',label:'Nota Fiscal',desc:'Entrada de EPI por PDF/XML e IA',cat:'Controle'},
 {id:'portal',label:'Portal do Trabalhador',desc:'Links, solicitações e acompanhamento',cat:'Controle'},
 {id:'biometrics',label:'Biometria facial',desc:'Cadastro e confirmação facial',cat:'Controle'},
 {id:'reports',label:'Relatórios e indicadores',desc:'Indicadores e relatórios gerenciais',cat:'Gestão'},
 {id:'operations',label:'Central Operacional',desc:'Pendências, liberações TST e almoxarifado',cat:'Gestão'},
 {id:'imports',label:'Importação de trabalhadores',desc:'PDF, Excel, CSV e TXT',cat:'Gestão'},
 {id:'advanced_stock',label:'Estoque avançado',desc:'Multiestoque, inventário, previsão, lote e auditoria',cat:'Avançado'},
 {id:'kits',label:'Kits por função',desc:'Kit padrão por cargo/função',cat:'Avançado'},
 {id:'compliance',label:'Fiscalização e compliance',desc:'Dossiê e recursos de conformidade',cat:'Avançado'},
 {id:'data_safety',label:'Segurança dos dados',desc:'Backup, integridade e recuperação',cat:'Avançado'}
];
const ALL=Object.fromEntries(MODULES.map(m=>[m.id,true]));
const ESSENTIAL={delivery:true,workers:true,epis:true,stock:true,history:true};
const OPERATIONAL={...ESSENTIAL,replacements:true,ca:true,invoices:true,portal:true,biometrics:true,reports:true,operations:true,imports:true};
const PRESETS={essential:ESSENTIAL,operational:OPERATIONAL,complete:ALL};

const VIEW_MAP={
 dashboard:null,home:null,companies:null,adaptiveModulesV380:null,
 fastDeliveryPc:'delivery',newDeliveryPc:'delivery',batchDeliveryPc:'delivery',delivery:'delivery',
 workers:'workers',workerProfilePc:'workers',qrPeoplePc:'workers',externalsPc:'workers',
 epis:'epis',
 stock:'stock',purchasesPc:'stock',
 deliveries:'history',history:'history',receiptsPc:'history',receiptDetailPc:'history',employeeSheetsPc:'history',auditPc:'history',
 returnsPc:'replacements',replacementPc:'replacements',epiReturn:'replacements',epiHeld:'replacements',epiReplacements:'replacements',
 caSmartPc:'ca',caCenterV330:'ca',
 nfImportPc:'invoices',
 faceEnrollPc:'biometrics',
 managerReportsPc:'reports',indicators:'reports',
 alertsPc:'operations',operationsCenterV340:'operations',epiFlowV350:'operations',pending:'operations',
 importWorkersPc:'imports',importWorkers:'imports',
 inventoryPc:'advanced_stock',dataQualityPc:'advanced_stock',advancedStockV380:null,
 rolePpePc:'kits',
 inspectionPc:'compliance',inspectionDossierPc:'compliance',legalCompliancePc:'compliance',
 dataSafetyPc:'data_safety',
 portalRequests370:'portal'
};

function blankApp(){return {companies:[],workers:[],epis:[],deliveries:[],purchases:[],batches:[],epiKits:[],returns:[],refusals:[],inventoryCounts:[],auditLog:[]}}
function blankStock(){return {startedAt:'',processedDeliveryIds:[],movements:[],minimums:{},warehouses:[],warehouseMinimums:{}}}
function readRoot(){
 try{
  if(PC){
   const r=JSON.parse(localStorage.getItem(CACHE)||'{}');r.app={...blankApp(),...(r.app||{})};r.stock={...blankStock(),...(r.stock||{})};
   for(const k of Object.keys(blankApp()))if(Array.isArray(blankApp()[k]))r.app[k]=Array.isArray(r.app[k])?r.app[k]:[];
   r.stock.movements=Array.isArray(r.stock.movements)?r.stock.movements:[];r.stock.warehouses=Array.isArray(r.stock.warehouses)?r.stock.warehouses:[];return r;
  }
  const app={...blankApp(),...JSON.parse(localStorage.getItem(APP)||'{}')},stock={...blankStock(),...JSON.parse(localStorage.getItem(STOCK)||'{}')};
  app.auditLog=Array.isArray(app.auditLog)?app.auditLog:[];return {version:1,revision:Number(localStorage.getItem(REV)||0),updatedAt:now(),app,stock};
 }catch(_){return {version:1,revision:0,updatedAt:'',app:blankApp(),stock:blankStock()}}
}
function writeRoot(r){
 r.updatedAt=now();
 if(PC)localStorage.setItem(CACHE,JSON.stringify(r));
 else{localStorage.setItem(APP,JSON.stringify(r.app));localStorage.setItem(STOCK,JSON.stringify(r.stock));document.dispatchEvent(new CustomEvent('auditar-epi-data-changed',{detail:{source:'adaptive-v380'}}))}
}
function user(){return window.GestaoEpiAuth?.user?.()||{}}
function isAdmin(){return user()?.role==='admin'}
function toast(m){const t=$('#toast');if(t){t.textContent=m;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),2600)}else alert(m)}
async function syncNow(){
 try{
  const api=window.GestaoEpiAuth?.api;if(!api)return false;const root=readRoot();
  const res=await api('epi_sync_merge',{deviceId:window.GestaoEpiAuth?.deviceId?.()||'',client:PC?'gestao':'campo',payload:root});
  if(!res?.ok)throw new Error(res?.message||'Falha na sincronização.');
  const remote=res.payload||root;
  if(PC)localStorage.setItem(CACHE,JSON.stringify(remote));else{localStorage.setItem(APP,JSON.stringify(remote.app||{}));localStorage.setItem(STOCK,JSON.stringify(remote.stock||{}));localStorage.setItem(REV,String(res.revision||remote.revision||0))}
  document.dispatchEvent(new CustomEvent('gestao-epi-sync-applied'));return true;
 }catch(e){toast(e?.message||'Não foi possível sincronizar.');return false}
}
function audit(root,type){return (root.app.auditLog||[]).filter(x=>x?.type===type)}
function upsert(root,row){const a=root.app.auditLog||(root.app.auditLog=[]),i=a.findIndex(x=>x.id===row.id);if(i>=0)a[i]=row;else a.unshift(row)}
function accountRow(root=readRoot()){return audit(root,'epi_account_module_profile')[0]||{id:'modules_account_v380',type:'epi_account_module_profile',preset:'complete',modules:{}}}
function userRow(username,root=readRoot()){return audit(root,'epi_user_module_profile').find(x=>norm(x.username)===norm(username))||{id:'modules_user_'+norm(username).replace(/[^a-z0-9]/g,'_'),type:'epi_user_module_profile',username,mode:'inherit',modules:{}}}
function workerCount(root=readRoot()){return (root.app.workers||[]).filter(w=>w.active!==false).length}
function autoPreset(root=readRoot()){const n=workerCount(root);return n<=25?'essential':n<=100?'operational':'complete'}
function presetModules(name,root=readRoot()){const p=name==='auto'?autoPreset(root):name;return {...ALL,...Object.fromEntries(Object.keys(ALL).map(k=>[k,false])),...(PRESETS[p]||ALL)}}
function accountModules(root=readRoot()){
 const row=accountRow(root),p=row.preset||'auto';
 if(p==='custom')return Object.fromEntries(MODULES.map(m=>[m.id,row.modules?.[m.id]!==false]));
 return presetModules(p,root);
}
function effectiveModules(root=readRoot()){
 const base=accountModules(root),u=user(),row=u?.username?userRow(u.username,root):null;
 if(!row||row.mode!=='custom')return base;
 const out={};for(const m of MODULES)out[m.id]=base[m.id]!==false&&row.modules?.[m.id]!==false;return out;
}
function moduleForElement(el){
 if(!el)return null;
 const id=el.dataset?.view||el.dataset?.go||el.dataset?.pcGo||el.dataset?.v260Go||el.dataset?.flowtab||'';
 if(VIEW_MAP[id]!==undefined)return VIEW_MAP[id];
 if(/invoice|nf/i.test(id))return'invoices';
 if(/ca/i.test(id))return'ca';
 if(/report|indicator/i.test(id))return'reports';
 if(/biometr|face/i.test(id))return'biometrics';
 if(/return|replacement|troca|held/i.test(id))return'replacements';
 if(/portal/i.test(id))return'portal';
 if(/inventory|warehouse|forecast|recall|advanced/i.test(id))return'advanced_stock';
 if(/kit|rolePpe/i.test(id))return'kits';
 return null;
}
function allowed(mod){if(!mod)return true;return effectiveModules()[mod]!==false}
function applyVisibility(){
 const eff=effectiveModules();
 const selectors=['.sidebar .nav[data-view]','[data-go]','[data-pc-go]','[data-v260-go]','[data-flowtab]'];
 for(const sel of selectors)$$(sel).forEach(el=>{
  if(el.closest('#adaptiveModulesV380'))return;
  const mod=moduleForElement(el);el.classList.toggle('adaptive380-hidden',!!mod&&eff[mod]===false);
 });
 const adv=$('#advancedStockV380');if(adv&&eff.advanced_stock===false&&adv.classList.contains('active'))openHome();
}
function openHome(){if(PC)$('.sidebar .nav[data-view="dashboard"]')?.click();else $('[data-go="home"]')?.click()}
function installStyle(){
 if($('#adaptive380Style'))return;const s=document.createElement('style');s.id='adaptive380Style';s.textContent=`
.adaptive380-hidden{display:none!important}.adaptive380-wrap{display:grid;gap:12px}.adaptive380-card{background:#fff;border:1px solid #dce8e5;border-radius:15px;padding:14px}.adaptive380-head{display:flex;justify-content:space-between;gap:10px;align-items:center}.adaptive380-head h3{margin:0;color:#173d39}.adaptive380-head p{margin:3px 0 0;color:#6d817d;font-size:11px}.adaptive380-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}.adaptive380-module{border:1px solid #dce8e5;border-radius:12px;padding:10px;display:flex;gap:9px;align-items:flex-start;background:#fbfdfc}.adaptive380-module input{margin-top:2px;width:18px;height:18px}.adaptive380-module b{display:block;font-size:12px}.adaptive380-module small{display:block;color:#718480;font-size:10px;line-height:1.35;margin-top:2px}.adaptive380-note{padding:10px;border-radius:10px;background:#f3f8f7;color:#5d7570;font-size:11px;line-height:1.45}.adaptive380-actions{display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end;margin-top:12px}.adaptive380-actions button{border:1px solid #cfe0dc;background:#fff;border-radius:9px;padding:9px 11px;font-weight:850;color:#285f58}.adaptive380-actions .primary{background:#0f766e;color:#fff;border-color:#0f766e}.adaptive380-selects{display:grid;grid-template-columns:1fr 1fr;gap:9px}.adaptive380-selects label{display:grid;gap:5px;font-size:11px;font-weight:850;color:#46615d}.adaptive380-selects select{min-height:40px;border:1px solid #cfe0dc;border-radius:9px;padding:8px;background:#fff}@media(max-width:700px){.adaptive380-grid,.adaptive380-selects{grid-template-columns:1fr}}
`;document.head.appendChild(s)
}
function injectNav(){
 if(!isAdmin())return;
 if(PC){const nav=$('.sidebar nav');if(nav&&!nav.querySelector('[data-view="adaptiveModulesV380"]')){const b=document.createElement('button');b.className='nav pc-new';b.dataset.view='adaptiveModulesV380';b.innerHTML='⚙️ <span>Módulos e acesso</span>';nav.appendChild(b)}}
 else{const grid=$('#moreFunctions .more323-grid');if(grid&&!grid.querySelector('[data-go="adaptiveModulesV380"]')){const b=document.createElement('button');b.className='more323-card';b.dataset.go='adaptiveModulesV380';b.innerHTML='<span>⚙️</span><b>Módulos e acesso</b><small>Adaptar o sistema por conta</small>';grid.appendChild(b)}}
}
function injectView(){
 if($('#adaptiveModulesV380'))return;
 const main=PC?$('.main'):($('.app-shell')||document.body);if(!main)return;
 const sec=document.createElement('section');sec.id='adaptiveModulesV380';sec.className='view'+(PC?' pc-modern-view':'');
 sec.innerHTML=`${PC?'<div class="pc-modern-head"><div><h2>Módulos e acesso</h2><p>Deixe o Gestão EPI simples para cada empresa e usuário.</p></div></div>':'<div class="view-head"><button class="back" data-go="moreFunctions">←</button><div><h2>Módulos e acesso</h2><p>Escolha apenas o que a conta precisa usar.</p></div></div>'}<div class="adaptive380-wrap"><div id="adaptive380Body"></div></div>`;
 main.appendChild(sec);
}
function open(){
 if(!isAdmin())return toast('Somente o Administrador pode configurar módulos.');
 injectView();
 if(PC){$$('.view').forEach(v=>v.classList.toggle('active',v.id==='adaptiveModulesV380'));$$('.sidebar .nav').forEach(n=>n.classList.toggle('active',n.dataset.view==='adaptiveModulesV380'));if($('#viewTitle'))$('#viewTitle').textContent='Módulos e acesso';if($('#viewSub'))$('#viewSub').textContent='Adapte o sistema ao tamanho e à rotina da empresa.'}
 else{$$('.view').forEach(v=>v.classList.remove('active'));$('#adaptiveModulesV380').classList.add('active');window.scrollTo(0,0)}
 render();
}
function moduleGrid(values,disabled=false,prefix='acc'){
 const cats=[...new Set(MODULES.map(m=>m.cat))];return cats.map(cat=>`<div class="adaptive380-card"><div class="adaptive380-head"><div><h3>${esc(cat)}</h3></div></div><div class="adaptive380-grid" style="margin-top:10px">${MODULES.filter(m=>m.cat===cat).map(m=>`<label class="adaptive380-module"><input type="checkbox" data-adaptive380="${prefix}:${m.id}" ${values[m.id]!==false?'checked':''} ${disabled?'disabled':''}><span><b>${esc(m.label)}</b><small>${esc(m.desc)}</small></span></label>`).join('')}</div></div>`).join('')
}
function render(){
 const root=readRoot(),row=accountRow(root),count=workerCount(root),auto=autoPreset(root),preset=row.preset||'auto',vals=accountModules(root),box=$('#adaptive380Body');if(!box)return;
 box.innerHTML=`<div class="adaptive380-card"><div class="adaptive380-head"><div><h3>Perfil da conta</h3><p>Você pode usar um perfil pronto ou personalizar.</p></div></div><div class="adaptive380-selects" style="margin-top:10px"><label>Perfil<select id="adaptive380Preset"><option value="auto" ${preset==='auto'?'selected':''}>Automático pelo porte</option><option value="essential" ${preset==='essential'?'selected':''}>Essencial</option><option value="operational" ${preset==='operational'?'selected':''}>Operacional</option><option value="complete" ${preset==='complete'?'selected':''}>Completo</option><option value="custom" ${preset==='custom'?'selected':''}>Personalizado</option></select></label><div class="adaptive380-note"><b>${count} trabalhador(es) ativo(s)</b><br>No modo automático, o sistema usaria <b>${auto==='essential'?'Essencial':auto==='operational'?'Operacional':'Completo'}</b>.</div></div></div><div id="adaptive380AccountModules">${moduleGrid(vals,preset!=='custom','acc')}</div><div class="adaptive380-actions"><button class="primary" id="adaptive380SaveAccount">Salvar perfil da conta</button></div><div class="adaptive380-card"><div class="adaptive380-head"><div><h3>Permissões por usuário</h3><p>O usuário pode herdar a conta ou ter uma versão ainda mais simples.</p></div></div><div id="adaptive380Users" class="adaptive380-note" style="margin-top:10px">Carregando usuários…</div></div>`;
 $('#adaptive380Preset').onchange=()=>{const p=$('#adaptive380Preset').value,values=p==='custom'?vals:presetModules(p,root);$('#adaptive380AccountModules').innerHTML=moduleGrid(values,p!=='custom','acc')};
 $('#adaptive380SaveAccount').onclick=saveAccount;loadUsers();
}
async function saveAccount(){
 const root=readRoot(),old=accountRow(root),preset=$('#adaptive380Preset').value,mods={};MODULES.forEach(m=>{const i=$('[data-adaptive380="acc:'+m.id+'"]');mods[m.id]=i?i.checked:true});
 const row={...old,id:'modules_account_v380',type:'epi_account_module_profile',preset,modules:mods,updatedAt:now(),createdAt:old.createdAt||now(),updatedBy:{username:user().username||'',name:user().name||user().username||''}};
 upsert(root,row);writeRoot(root);await syncNow();toast('Perfil da conta atualizado.');applyVisibility();render();
}
async function loadUsers(){
 const box=$('#adaptive380Users');if(!box)return;
 try{
  const res=await window.GestaoEpiAuth?.api?.('tenant_list_users');if(!res?.ok)throw new Error(res?.message||'Falha ao carregar usuários.');
  const root=readRoot(),base=accountModules(root),users=(res.users||[]).filter(u=>u.role!=='master');
  box.className='';box.innerHTML=users.map(u=>{const r=userRow(u.username,root),mode=r.mode||'inherit';return `<div class="adaptive380-card" data-adaptive-user="${esc(u.username)}"><div class="adaptive380-head"><div><h3>${esc(u.name||u.username)}</h3><p>@${esc(u.username)} • ${esc(u.role||'')}</p></div><select data-adaptive-mode="${esc(u.username)}"><option value="inherit" ${mode==='inherit'?'selected':''}>Herdar perfil da conta</option><option value="custom" ${mode==='custom'?'selected':''}>Personalizar este usuário</option></select></div><div class="adaptive380-grid" style="margin-top:10px">${MODULES.map(m=>`<label class="adaptive380-module"><input type="checkbox" data-adaptive-user-module="${esc(u.username)}:${m.id}" ${(mode==='custom'?r.modules?.[m.id]!==false:base[m.id]!==false)?'checked':''} ${mode!=='custom'||base[m.id]===false?'disabled':''}><span><b>${esc(m.label)}</b></span></label>`).join('')}</div><div class="adaptive380-actions"><button data-adaptive-save-user="${esc(u.username)}" class="primary">Salvar usuário</button></div></div>`}).join('')||'<div class="adaptive380-note">Nenhum usuário encontrado.</div>';
  $('[data-adaptive-mode]').forEach(sel=>sel.onchange=()=>{const username=sel.dataset.adaptiveMode,custom=sel.value==='custom';MODULES.forEach(m=>{const i=$('[data-adaptive-user-module]').find(x=>x.dataset.adaptiveUserModule===username+':'+m.id);if(i){i.disabled=!custom||base[m.id]===false;if(custom&&base[m.id]!==false&&i.dataset.adaptiveTouched!=='1')i.checked=true}})});$('[data-adaptive-user-module]').forEach(i=>i.onchange=()=>i.dataset.adaptiveTouched='1');$('[data-adaptive-save-user]').forEach(b=>b.onclick=()=>saveUser(b.dataset.adaptiveSaveUser));
 }catch(e){box.className='adaptive380-note';box.textContent=e?.message||'Não foi possível carregar usuários.'}
}
async function saveUser(username){
 const root=readRoot(),old=userRow(username,root),mode=$('[data-adaptive-mode="'+CSS.escape(username)+'"]')?.value||'inherit',mods={};
 MODULES.forEach(m=>{const i=$('[data-adaptive-user-module="'+CSS.escape(username+':'+m.id)+'"]');mods[m.id]=i?i.checked:true});
 const row={...old,id:old.id||'modules_user_'+norm(username).replace(/[^a-z0-9]/g,'_'),type:'epi_user_module_profile',username,mode,modules:mods,updatedAt:now(),createdAt:old.createdAt||now(),updatedBy:{username:user().username||'',name:user().name||user().username||''}};
 upsert(root,row);writeRoot(root);await syncNow();toast('Permissões de '+username+' atualizadas.');applyVisibility();loadUsers();
}
function guard(e){
 const el=e.target.closest?.('[data-view],[data-go],[data-pc-go],[data-v260-go],[data-flowtab]');if(!el||el.closest('#adaptiveModulesV380'))return;const mod=moduleForElement(el);if(mod&&!allowed(mod)){e.preventDefault();e.stopImmediatePropagation();toast('Este módulo não está disponível para sua conta.')}
}
function bind(){
 document.addEventListener('click',e=>{if(e.target.closest(PC?'[data-view="adaptiveModulesV380"]':'[data-go="adaptiveModulesV380"]')){e.preventDefault();e.stopImmediatePropagation();open()}},true);
 document.addEventListener('click',guard,true);
 const gc=$('#globalCompany');gc?.addEventListener('change',()=>setTimeout(applyVisibility,50));
 document.addEventListener('gestao-epi-sync-applied',()=>setTimeout(()=>{injectNav();injectView();applyVisibility()},120));
 document.addEventListener('auditar-epi-data-changed',()=>setTimeout(applyVisibility,120));
}
function boot(){installStyle();injectNav();injectView();bind();[400,1000,2200,4000].forEach(ms=>setTimeout(()=>{injectNav();injectView();applyVisibility()},ms));window.GestaoEpiModulesV380={allowed,effectiveModules,applyVisibility,MODULES}}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();