(()=>{
'use strict';
const $=(q,r=document)=>r.querySelector(q),$$=(q,r=document)=>[...r.querySelectorAll(q)];
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const norm=x=>String(x||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
let workerId='',busy=false;
function app(){try{const r=JSON.parse(localStorage.getItem('auditarEpiV1')||'{}');return {workers:r.workers||[],companies:r.companies||[],epis:r.epis||[],deliveries:r.deliveries||[]}}catch(_){return {workers:[],companies:[],epis:[],deliveries:[]}}}
function toast(msg){const e=$('#toast');if(!e)return alert(msg);e.textContent=msg;e.classList.add('show');setTimeout(()=>e.classList.remove('show'),6500)}
function date(t){try{return new Intl.DateTimeFormat('pt-BR',{dateStyle:'short',timeStyle:'short'}).format(new Date(t))}catch(_){return String(t||'')}}
function proof(d){return d.biometricVerified||d.confirmationMethod==='face-biometric'?'Biometria facial verificada':/^data:image\/(?:png|jpeg|webp);base64,/i.test(d.signature||'')?'Assinatura eletrônica':'Evidência não identificada'}
function rows(r,d){return (d.items||[]).map(i=>{const e=r.epis.find(x=>x.id===i.epiId)||{};return {name:e.name||'EPI',ca:e.ca||'',model:e.model||'',size:e.size||'',qty:Number(i.qty||0)}})}
function current(){const r=app(),w=r.workers.find(x=>String(x.id)===String(workerId));if(!w)return null;const c=r.companies.find(x=>x.id===w.companyId)||{},d=r.deliveries.filter(x=>x.workerId===w.id&&!x.cancelled).sort((a,b)=>String(b.createdAt||'').localeCompare(String(a.createdAt||'')));return {r,w,c,d}}
function payload(){
 const x=current();if(!x)throw Error('Selecione um trabalhador.');
 const map=new Map();x.d.forEach(d=>rows(x.r,d).forEach(i=>{const k=[i.name,i.ca,i.model,i.size].join('::');const old=map.get(k);map.set(k,{...i,qty:i.qty+Number(old?.qty||0)})}));
 return {documentType:'worker_sheet',deliveryId:'worker_'+String(x.w.id),company:String(x.c.name||''),cnpj:String(x.c.cnpj||''),worker:String(x.w.name||''),cpf:String(x.w.cpf||''),registration:String(x.w.reg||''),roleSector:[x.w.role,x.w.sector].filter(Boolean).join(' / '),date:date(Date.now()),items:[...map.values()],deliveries:x.d.slice(0,250).map(d=>({id:String(d.id||''),date:date(d.createdAt),type:d.deliveryFlow==='direct'?'Entrega direta':d.authorizationId?'Entrega autorizada':'Entrega',items:rows(x.r,d).map(i=>i.name+' • CA '+(i.ca||'não informado')+' • qtd. '+i.qty).join(' | '),method:proof(d),reason:d.reason||'',deliveredBy:d.warehouseDeliveredBy?.name||d.registeredBy?.name||d.responsible||'Não registrado'}))};
}
function plugin(){try{if(window.Capacitor?.registerPlugin)return window.Capacitor.registerPlugin('NativePrint')}catch(_){}return window.Capacitor?.Plugins?.NativePrint||null}
async function pdf(share){
 if(busy)return;
 let record;try{record=payload()}catch(e){return toast(e.message)}
 const p=plugin(),action=share?'sharePdf':'print';
 if(!window.Capacitor?.isNativePlatform?.()||typeof p?.[action]!=='function')return toast('Atualize o Android para exportar a ficha individual em PDF.');
 busy=true;$$('[data-ficha382-pdf]').forEach(b=>b.disabled=true);
 try{await p[action]({receipt:record,jobName:'Ficha Individual de EPI'})}
 catch(e){toast('Erro ao gerar/compartilhar ficha: '+String(e?.message||e))}
 finally{busy=false;$$('[data-ficha382-pdf]').forEach(b=>b.disabled=false)}
}
function install(){
 if($('#ficha382Css'))return;
 const st=document.createElement('style');st.id='ficha382Css';
 st.textContent='#fichas382{padding-bottom:110px}.f382-card{background:#fff;border:1px solid #dbe9e5;border-radius:16px;padding:14px;margin:11px 0}.f382-row{display:flex;justify-content:space-between;align-items:center;gap:10px;border:1px solid #e1eeea;border-radius:12px;padding:11px;margin:8px 0}.f382-row small{display:block;color:#627a74;font-size:12px;margin-top:5px}.f382-btn{min-height:45px;border:1px solid #bdd9d2;border-radius:11px;background:#e9f7f3;color:#0b715e;font-size:14px;font-weight:800;padding:9px 12px}.f382-btn.primary{background:#0d866f;color:#fff}.f382-actions{display:grid;grid-template-columns:1fr 1fr;gap:9px;margin:13px 0}.f382-meta{display:grid;grid-template-columns:1fr 1fr;gap:9px}.f382-meta span{background:#f4faf8;padding:10px;border-radius:10px;word-break:break-word;font-size:13px}.f382-search{width:100%;font-size:16px;min-height:45px}.f382-note{color:#61776f;font-size:12px;line-height:1.5}#workerList .list-actions [data-ficha382-worker]{order:1}.f382-admin-actions{align-self:center;order:8;font-size:13px;color:#55766e}.f382-admin-actions summary{list-style:none;cursor:pointer;text-decoration:underline;padding:10px 5px}.f382-admin-actions [data-del-worker]{margin-top:9px;display:block}@media(max-width:450px){.f382-row{display:block}.f382-row button{width:100%;margin-top:9px}.f382-meta{grid-template-columns:1fr}}';
 document.head.appendChild(st)
}
function ensure(){
 const main=$('main.app-shell')||$('main');if(!main)return;
 if(!$('#fichas382')){
  const s=document.createElement('section');s.className='view';s.id='fichas382';
  s.innerHTML='<div class="view-head"><button class="back" data-ficha382-back="1">←</button><div><h2>Fichas individuais de EPI</h2><p>Consultar, imprimir e compartilhar a ficha completa.</p></div></div><div class="f382-card"><input class="f382-search" id="ficha382Query" placeholder="Buscar nome, CPF ou matrícula"><div id="ficha382List"></div></div><div id="ficha382Details"></div>';
  main.appendChild(s);$('#ficha382Query').addEventListener('input',list);
 }
 const menu=$('#moreFunctions .more323-grid')||$('#home .menu-grid');
 if(menu&&!menu.querySelector('[data-ficha382-start]')){
  const b=document.createElement('button');b.type='button';b.className=menu.classList.contains('more323-grid')?'more323-card':'menu-card';b.dataset.ficha382Start='1';b.innerHTML='<span>📑</span><b>Fichas completas</b><small>Consultar e imprimir em PDF</small>';menu.appendChild(b);
 }
}
function open(){ensure();$$('.view').forEach(v=>v.classList.remove('active'));$('#fichas382').classList.add('active');workerId='';$('#ficha382Details').innerHTML='';list();window.scrollTo(0,0)}
function list(){
 if(!$('#ficha382List'))return;
 const r=app(),q=norm($('#ficha382Query').value),ws=r.workers.filter(w=>w.active!==false&&(!q||norm([w.name,w.reg,w.cpf,w.role].join(' ')).includes(q))).sort((a,b)=>String(a.name||'').localeCompare(String(b.name||''))).slice(0,100);
 $('#ficha382List').innerHTML=ws.map(w=>'<div class="f382-row"><div><b>'+esc(w.name||'Trabalhador')+'</b><small>'+esc([w.reg,w.role].filter(Boolean).join(' • '))+'</small></div><button class="f382-btn" data-ficha382-worker="'+esc(w.id)+'">Abrir ficha completa</button></div>').join('')||'<p>Nenhum trabalhador encontrado.</p>'
}
function detail(id){
 workerId=id;const x=current();if(!x)return toast('Trabalhador não encontrado.');
 ensure();$$('.view').forEach(v=>v.classList.remove('active'));$('#fichas382').classList.add('active');
 const r=x.r,totals=new Map();x.d.forEach(d=>rows(r,d).forEach(i=>{const k=i.name+'::'+i.ca;totals.set(k,{...i,qty:i.qty+Number(totals.get(k)?.qty||0)})}));
 const cell=(label,value)=>'<span><b>'+label+'</b><div>'+esc(value||'Não informado')+'</div></span>';
 $('#ficha382Details').innerHTML='<div class="f382-card"><h2>'+esc(x.w.name)+'</h2><p>Ficha individual de EPI</p><div class="f382-meta">'+cell('Empresa',x.c.name)+cell('CPF',x.w.cpf)+cell('Matrícula',x.w.reg)+cell('Função / setor',[x.w.role,x.w.sector].filter(Boolean).join(' / '))+'</div><div class="f382-actions"><button type="button" class="f382-btn primary" data-ficha382-pdf="print">🖨️ Ficha PDF</button><button type="button" class="f382-btn" data-ficha382-pdf="share">↗ Compartilhar PDF</button></div><p class="f382-note">Quantidades abaixo representam o histórico de entregas, não necessariamente o saldo em posse após devoluções.</p><h3>EPIs registrados</h3>'+([...totals.values()].map(i=>'<div class="f382-row"><div><b>'+esc(i.name)+'</b><small>CA '+esc(i.ca||'não informado')+' • quantidade entregue '+i.qty+'</small></div></div>').join('')||'<p>Sem EPIs.</p>')+'<h3>Histórico de entregas</h3>'+(x.d.map(d=>'<div class="f382-row"><div><b>'+esc(date(d.createdAt))+'</b><small>'+esc(rows(r,d).map(i=>i.name+' x'+i.qty).join(', '))+'</small><small>'+esc(proof(d))+'</small></div><button type="button" class="f382-btn" data-ficha382-receipt="'+esc(d.id)+'">Comprovante</button></div>').join('')||'<p>Sem entregas.</p>')+'</div>';window.scrollTo(0,0)
}
function decorate(){
 const list=$('#workerList');if(list)list.querySelectorAll('.list-item').forEach(row=>{
  const id=row.querySelector('[data-del-worker]')?.dataset.delWorker,actions=row.querySelector('.list-actions');if(!id||!actions)return;
  const summary=row.querySelector('[data-ux-worker]');if(summary&&summary.textContent.trim()==='Abrir')summary.textContent='Resumo 360°';
  if(!row.querySelector('[data-ficha382-worker]')){const b=document.createElement('button');b.type='button';b.className='tiny';b.dataset.ficha382Worker=id;b.textContent='📑 Ficha completa';actions.prepend(b)}
  const del=row.querySelector('[data-del-worker]');if(del&&!row.querySelector('.f382-admin-actions')){const more=document.createElement('details');more.className='f382-admin-actions';const summary=document.createElement('summary');summary.textContent='Mais opções';more.appendChild(summary);more.appendChild(del);actions.appendChild(more)}
 });
 const actions=$('#ux300Modal .ux300-actions');if(actions&&!$('#ficha382From360')){const b=document.createElement('button');b.type='button';b.id='ficha382From360';b.className='ux300-action';b.textContent='📑 Ficha completa';actions.appendChild(b)}
}
function boot(){
 install();ensure();decorate();
 const captureBottom=()=>{
  const nav=$('#bottomNav');if(!nav)return;
  const b=$('[data-go]',nav).find(x=>/fichas/i.test(String(x.textContent||'')));
  if(b){b.dataset.ficha382Start='1';b.setAttribute?.('aria-label','Abrir fichas individuais de EPI');}
 };
 captureBottom();
 // Captura o atalho Fichas antes do roteador antigo (que o leva a Colaboradores).
 // Não modifica data-go de outros botões nem afeta a navegação restante.
 document.addEventListener('click',e=>{
  const bottom=e.target.closest?.('#bottomNav button');
  if(bottom&&/\bfichas\b/i.test(String(bottom.textContent||''))){
    e.preventDefault();e.stopImmediatePropagation();open();return;
  }
  const b=e.target.closest?.('[data-ficha382-start],[data-ficha382-worker],[data-ficha382-back],[data-ficha382-pdf],[data-ficha382-receipt],#ficha382From360,[data-ux-worker]');if(!b)return;
  if(b.matches('[data-ux-worker]')){workerId=b.dataset.uxWorker;setTimeout(decorate,80);return}
  if(b.id==='ficha382From360'){e.preventDefault();e.stopImmediatePropagation();if(workerId){$('#ux300Modal')?.classList.remove('open');detail(workerId)}return}
  if(b.dataset.ficha382Start){e.preventDefault();e.stopImmediatePropagation();open();return}
  if(b.dataset.ficha382Back){e.preventDefault();e.stopImmediatePropagation();$('[data-go="workers"]')?.click();return}
  if(b.dataset.ficha382Worker){e.preventDefault();e.stopImmediatePropagation();$('#ux300Modal')?.classList.remove('open');detail(b.dataset.ficha382Worker);return}
  if(b.dataset.ficha382Pdf){e.preventDefault();e.stopImmediatePropagation();pdf(b.dataset.ficha382Pdf==='share');return}
  if(b.dataset.ficha382Receipt){e.preventDefault();e.stopImmediatePropagation();const x=document.createElement('button');x.type='button';x.hidden=true;x.dataset.receipt=b.dataset.ficha382Receipt;document.body.appendChild(x);try{x.click()}finally{x.remove()}}
 },true);
 document.addEventListener('auditar-epi-data-changed',()=>{decorate();if($('#fichas382')?.classList.contains('active')&&!workerId)list()});
 document.addEventListener('gestao-epi-sync-applied',()=>{decorate();if($('#fichas382')?.classList.contains('active')&&!workerId)list()});
 const ls=$('#workerList');if(ls){let pending=false;new MutationObserver(()=>{if(pending)return;pending=true;requestAnimationFrame(()=>{pending=false;decorate()})}).observe(ls,{childList:true})}
 [500,1500,3000].forEach(ms=>setTimeout(()=>{ensure();decorate();captureBottom()},ms));
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();