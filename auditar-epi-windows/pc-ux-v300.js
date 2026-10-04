(()=>{
  'use strict';
  const CACHE='auditarEpiGestaoCacheV1';
  const UX_KEY='gestaoEpiPcUxV300';
  const $=(s,r=document)=>r.querySelector(s);
  const $$=(s,r=document)=>[...r.querySelectorAll(s)];
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const norm=v=>String(v??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim();
  const fmt=v=>{if(!v)return '—';const d=new Date(v);if(Number.isNaN(d.getTime()))return '—';return new Intl.DateTimeFormat('pt-BR',{dateStyle:'short',timeStyle:'short'}).format(d);};
  let timer=0,observer=null;

  function read(){
    try{
      const root=JSON.parse(localStorage.getItem(CACHE)||'{}');
      root.app=root.app&&typeof root.app==='object'?root.app:{};
      root.app.companies=Array.isArray(root.app.companies)?root.app.companies:[];
      root.app.workers=Array.isArray(root.app.workers)?root.app.workers:[];
      root.app.epis=Array.isArray(root.app.epis)?root.app.epis:[];
      root.app.deliveries=Array.isArray(root.app.deliveries)?root.app.deliveries:[];
      root.stock=root.stock&&typeof root.stock==='object'?root.stock:{};
      root.stock.movements=Array.isArray(root.stock.movements)?root.stock.movements:[];
      return root;
    }catch(_){return {app:{companies:[],workers:[],epis:[],deliveries:[]},stock:{movements:[]}};}
  }
  function readUx(){try{const x=JSON.parse(localStorage.getItem(UX_KEY)||'{}');return {favorites:Array.isArray(x.favorites)?x.favorites:[],recent:Array.isArray(x.recent)?x.recent:[],kits:x.kits&&typeof x.kits==='object'?x.kits:{}};}catch(_){return {favorites:[],recent:[],kits:{}};}}
  function writeUx(x){localStorage.setItem(UX_KEY,JSON.stringify(x));}
  function toast(msg){const e=$('#toast');if(!e)return alert(msg);e.textContent=msg;e.classList.add('show');setTimeout(()=>e.classList.remove('show'),2800);}
  function companyName(root,id){return root.app.companies.find(c=>c.id===id)?.name||'Empresa';}
  function epi(root,id){return root.app.epis.find(e=>e.id===id)||{};}
  function roleKey(role){return norm(role).replace(/[^a-z0-9]+/g,'-');}
  function getField(note,key){const p=String(note||'').split('|').map(x=>x.trim()).find(x=>x.toLowerCase().startsWith(String(key).toLowerCase()+':'));return p?p.slice(p.indexOf(':')+1).trim():'';}
  function returnedQty(root,workerId,epiId){return (root.stock.movements||[]).filter(m=>String(m?.note||'').trim().startsWith('DEVOLUÇÃO EPI')&&m.epiId===epiId&&getField(m.note,'workerId')===workerId).reduce((s,m)=>s+Math.max(0,Number(getField(m.note,'qtd')||0)),0);}
  function holdings(workerId){
    const root=read(),rows=[];
    root.app.epis.forEach(e=>{
      const ds=root.app.deliveries.filter(d=>d.workerId===workerId&&d.cancelled!==true).flatMap(d=>(d.items||[]).filter(i=>i.epiId===e.id).map(i=>({d,qty:Number(i.qty||0)})));
      const qty=Math.max(0,ds.reduce((s,x)=>s+Math.max(0,x.qty),0)-returnedQty(root,workerId,e.id));if(!qty)return;
      const latest=ds.sort((a,b)=>String(b.d.createdAt||'').localeCompare(String(a.d.createdAt||'')))[0]?.d||null;
      const cycle=Number(e.cycle||0);let due=null,days=null,status='none';
      if(latest&&cycle>0){const dt=new Date(latest.createdAt);if(!Number.isNaN(dt.getTime())){due=new Date(dt.getTime()+cycle*86400000);days=Math.ceil((due-Date.now())/86400000);status=days<0?'overdue':days<=15?'soon':'ok';}}
      rows.push({e,qty,latest,due,days,status});
    });
    return rows.sort((a,b)=>({overdue:0,soon:1,ok:2,none:3}[a.status]-({overdue:0,soon:1,ok:2,none:3}[b.status])));
  }

  function styles(){
    if($('#pcUxV300Styles'))return;
    const s=document.createElement('style');s.id='pcUxV300Styles';s.textContent=`
      :root{--v300:#078468;--v300b:#0b5d56;--v300ink:#173b47;--v300line:#d9e7e3;--v300muted:#6b817d}
      .sidebar-brand{padding:14px 12px 10px!important}.sidebar-brand .logo{font-size:0!important;display:flex!important;align-items:center!important;gap:9px!important}.sidebar-brand .logo img{width:44px;height:44px}.sidebar-brand .logo::after{content:'Gestão EPI';font-size:17px;color:#fff;font-weight:950}.sidebar-brand>small{margin-left:53px!important;margin-top:-12px!important;color:#9fc9c1!important}
      .gestao-auth-overlay{background:linear-gradient(145deg,#e9f5f2,#fbfcfc 52%,#eef7f5)!important}.gestao-auth-card{max-width:440px!important;border-radius:24px!important;padding:25px!important;box-shadow:0 30px 80px rgba(18,62,57,.18)!important}.gestao-auth-logo,.gestao-auth-mark{background:transparent!important;width:auto!important;height:auto!important}.pc-v300-login-logo{display:block;width:min(290px,80vw);margin:0 auto 10px}.pc-v300-benefit{background:#f0f8f6;border:1px solid #d7e9e4;border-radius:13px;padding:10px 12px;color:#46645e;font-size:10px;line-height:1.5;margin:10px 0 12px}.pc-v300-benefit b{color:var(--v300b)}
      .pc-v300-worker{border:1px solid #cde1dc;background:#edf8f5;color:var(--v300b);border-radius:8px;padding:6px 8px;font-size:10px;font-weight:900;margin-left:5px}
      .pc-v300-modal{position:fixed;inset:0;z-index:50000;background:rgba(7,35,32,.72);display:none;align-items:center;justify-content:center;padding:22px}.pc-v300-modal.open{display:flex}.pc-v300-card{width:min(850px,100%);max-height:90vh;overflow:auto;background:#fff;border-radius:22px;padding:20px;box-shadow:0 35px 100px rgba(0,0,0,.3)}.pc-v300-head{display:flex;justify-content:space-between;gap:15px;align-items:flex-start}.pc-v300-head h2{margin:0;color:var(--v300ink)}.pc-v300-head p{margin:4px 0 0;color:var(--v300muted);font-size:11px}.pc-v300-close{width:40px;height:40px;border:0;border-radius:10px;background:#edf5f3;font-size:20px}.pc-v300-hero{margin:14px 0;background:linear-gradient(135deg,#123f48,#08725f);color:#fff;border-radius:16px;padding:16px}.pc-v300-meta{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:10px}.pc-v300-meta div{border:1px solid rgba(255,255,255,.16);border-radius:10px;padding:8px}.pc-v300-meta small{display:block;color:#c7e2dd;font-size:8px;font-weight:900;text-transform:uppercase}.pc-v300-meta b{font-size:10px}.pc-v300-actions{display:flex;gap:7px;flex-wrap:wrap}.pc-v300-actions button{border:1px solid var(--v300line);background:#fff;color:var(--v300b);border-radius:10px;padding:9px 11px;font-weight:900}.pc-v300-actions .p{background:var(--v300);color:#fff;border-color:var(--v300)}.pc-v300-section{border:1px solid var(--v300line);border-radius:15px;padding:13px;margin-top:12px}.pc-v300-section h3{margin:0 0 9px;color:var(--v300ink);font-size:14px}.pc-v300-held{display:grid;grid-template-columns:1fr 1fr;gap:8px}.pc-v300-row{border:1px solid #e2ece9;border-radius:11px;padding:10px;background:#fbfdfc}.pc-v300-row b{font-size:11px;color:var(--v300ink)}.pc-v300-row small{display:block;color:var(--v300muted);font-size:9px;line-height:1.4;margin-top:3px}.pc-v300-pill{display:inline-block;margin-top:6px;border-radius:999px;padding:4px 7px;font-size:8px;font-weight:900}.pc-v300-pill.ok{background:#e8f7ef;color:#11633c}.pc-v300-pill.soon{background:#fff4e3;color:#985600}.pc-v300-pill.overdue{background:#fff0ee;color:#b42318}.pc-v300-pill.none{background:#eef2f2;color:#627471}.pc-v300-row-actions{display:flex;gap:5px;margin-top:7px}.pc-v300-row-actions button{border:0;background:#e9f5f2;color:#0b6a5d;border-radius:7px;padding:5px 7px;font-size:8px;font-weight:900}.pc-v300-checks{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin:12px 0}.pc-v300-check{display:flex;gap:8px;align-items:center;border:1px solid var(--v300line);border-radius:10px;padding:8px}.pc-v300-qr{display:grid;place-items:center;min-height:230px;border:1px solid var(--v300line);border-radius:12px;margin:12px 0}.pc-v300-code{font:10px monospace;background:#f1f6f5;padding:8px;border-radius:8px;word-break:break-all}
      @media(max-width:800px){.pc-v300-meta{grid-template-columns:1fr 1fr}.pc-v300-held,.pc-v300-checks{grid-template-columns:1fr}}
    `;document.head.appendChild(s);
  }

  function brand(){
    const logo=$('.sidebar-brand .logo');if(logo&&!logo.querySelector('img'))logo.innerHTML='<img src="gestao-epi-icon-v300.svg" alt=""><span style="display:none">Gestão EPI</span>';
  }
  function login(){
    const card=$('#gestaoAuthOverlay .gestao-auth-card');if(!card)return;
    const existing=card.querySelector('.pc-v300-login-logo');
    if(!existing){
      const img=document.createElement('img');img.className='pc-v300-login-logo';img.src='gestao-epi-logo-v300.svg';img.alt='Gestão EPI Auditar';
      card.insertBefore(img,card.firstChild);
    }
    const h=card.querySelector('h1');if(h)h.textContent='Bem-vindo ao Gestão EPI';
    const p=card.querySelector('p');if(p)p.textContent='Controle de EPI com segurança, rastreabilidade e produtividade.';
    if(!card.querySelector('.pc-v300-benefit')){
      const x=document.createElement('div');x.className='pc-v300-benefit';x.innerHTML='<b>Gestão profissional em um só lugar.</b><br>Entregas, estoque, CA, biometria, trocas, comprovantes e Portal do Trabalhador.';
      const label=card.querySelector('label');card.insertBefore(x,label);
    }
  }

  function decorateWorkers(){
    const table=$('#workerTable');if(!table)return;
    table.querySelectorAll('[data-worker-sheet]').forEach(sheet=>{
      const id=sheet.dataset.workerSheet;if(!id||sheet.parentElement.querySelector('[data-pc-v300-worker]'))return;
      const b=document.createElement('button');b.type='button';b.className='pc-v300-worker';b.dataset.pcV300Worker=id;b.textContent='360°';
      sheet.insertAdjacentElement('afterend',b);
    });
  }

  function modal(){
    let d=$('#pcV300Modal');if(d)return d;
    d=document.createElement('div');d.id='pcV300Modal';d.className='pc-v300-modal';d.innerHTML='<div class="pc-v300-card"><div class="pc-v300-head"><div><h2>Trabalhador 360°</h2><p>Entrega, posse, trocas e acesso em uma tela.</p></div><button class="pc-v300-close">×</button></div><div id="pcV300Body"></div></div>';
    document.body.appendChild(d);d.querySelector('.pc-v300-close').onclick=()=>d.classList.remove('open');d.addEventListener('click',e=>{if(e.target===d)d.classList.remove('open');});return d;
  }

  function remember(id){const ux=readUx();ux.recent=[id,...ux.recent.filter(x=>x!==id)].slice(0,10);writeUx(ux);}
  function kitFor(w){const ux=readUx();return w?.role&&Array.isArray(ux.kits[roleKey(w.role)])?ux.kits[roleKey(w.role)]:[];}

  function open360(id){
    const root=read(),w=root.app.workers.find(x=>x.id===id);if(!w)return;remember(id);
    const rows=holdings(id),ds=root.app.deliveries.filter(d=>d.workerId===id&&d.cancelled!==true).sort((a,b)=>String(b.createdAt||'').localeCompare(String(a.createdAt||'')));
    const d=modal(),body=$('#pcV300Body');
    body.innerHTML=`<div class="pc-v300-hero"><h2 style="margin:0">${esc(w.name||'Trabalhador')}</h2><p style="margin:5px 0 0;color:#d5ece7">${esc(companyName(root,w.companyId))}</p><div class="pc-v300-meta"><div><small>Cargo</small><b>${esc(w.role||'—')}</b></div><div><small>Setor</small><b>${esc(w.sector||'—')}</b></div><div><small>Matrícula</small><b>${esc(w.reg||'—')}</b></div><div><small>Entregas</small><b>${ds.length}</b></div></div></div>
      <div class="pc-v300-actions"><button class="p" data-pcv-deliver="${esc(id)}">＋ Entregar EPI</button><button data-pcv-kit="${esc(id)}">🧰 Kit da função</button><button data-pcv-qr="${esc(id)}">▣ QR</button><button data-pcv-portal="${esc(id)}">🌐 Portal</button><button data-pcv-sheet="${esc(id)}">📄 Ficha</button></div>
      <div class="pc-v300-section"><h3>EPIs em posse</h3><div class="pc-v300-held">${rows.length?rows.map(r=>rowHtml(id,r)).join(''):'<div class="empty">Nenhum EPI em posse.</div>'}</div></div>
      <div class="pc-v300-section"><h3>Últimas entregas</h3>${ds.length?ds.slice(0,6).map(x=>`<div class="pc-v300-row"><b>${fmt(x.createdAt)} • ${esc(x.reason||'Entrega')}</b><small>${(x.items||[]).map(i=>esc(epi(root,i.epiId).name||'EPI')+' × '+Number(i.qty||0)).join(' • ')}</small></div>`).join(''):'<div class="empty">Sem entregas.</div>'}</div>`;
    d.classList.add('open');
  }

  function rowHtml(workerId,r){
    const label=r.status==='overdue'?`Vencido há ${Math.abs(r.days)}d`:r.status==='soon'?`Troca em ${r.days}d`:r.status==='ok'?`Em dia • ${r.days}d`:'Sem prazo';
    return `<div class="pc-v300-row"><b>${esc(r.e.name||'EPI')} • Qtd. ${r.qty}</b><small>${r.e.ca?'CA '+esc(r.e.ca)+' • ':''}${r.latest?'Última '+fmt(r.latest.createdAt):''}${r.due?' • Próxima '+fmt(r.due):''}</small><span class="pc-v300-pill ${r.status}">${esc(label)}</span><div class="pc-v300-row-actions"><button data-pcv-swap="${esc(workerId)}|${esc(r.e.id)}">Trocar agora</button></div></div>`;
  }

  function openView(id){const b=$('.sidebar .nav[data-view="'+id+'"]');if(b){b.click();return;}document.querySelector('[data-view="'+id+'"]')?.click();}
  function prefillDelivery(workerId,epiIds=[],reason=''){
    const root=read(),w=root.app.workers.find(x=>x.id===workerId);if(!w)return;
    $('#pcV300Modal')?.classList.remove('open');openView('newDeliveryPc');
    setTimeout(()=>{
      if($('#pcDeliveryCompany')){$('#pcDeliveryCompany').value=w.companyId;$('#pcDeliveryCompany').dispatchEvent(new Event('change',{bubbles:true}));}
      setTimeout(()=>{if($('#pcDeliveryWorker'))$('#pcDeliveryWorker').value=workerId;if(reason&&$('#pcDeliveryReason'))$('#pcDeliveryReason').value=reason;
        while($$('.pc-delivery-item').length<epiIds.length)$('#pcAddDeliveryItem')?.click();
        $$('.pc-delivery-item').forEach((row,i)=>{if(i<epiIds.length){const s=row.querySelector('.pc-item-epi');if(s)s.value=epiIds[i];}});
      },140);
    },120);
  }

  function openKit(workerId){
    const root=read(),w=root.app.workers.find(x=>x.id===workerId);if(!w||!w.role)return toast('Informe o cargo/função do trabalhador primeiro.');
    const d=modal(),selected=new Set(kitFor(w)),body=$('#pcV300Body');
    body.innerHTML=`<div class="pc-v300-section"><h3>Kit da função • ${esc(w.role)}</h3><p style="font-size:10px;color:#6b817d">Selecione os EPIs padrão desta função. A configuração fica local neste computador.</p><div class="pc-v300-checks">${root.app.epis.filter(e=>e.active!==false).map(e=>`<label class="pc-v300-check"><input type="checkbox" value="${esc(e.id)}" ${selected.has(e.id)?'checked':''}><span>${esc(e.name)}${e.ca?' • CA '+esc(e.ca):''}</span></label>`).join('')}</div><div class="pc-v300-actions"><button class="p" id="pcVSaveKit">Salvar kit</button><button id="pcVUseKit">Usar na entrega</button></div></div>`;
    $('#pcVSaveKit').onclick=()=>{const ux=readUx();ux.kits[roleKey(w.role)]=$$('#pcV300Body input:checked').map(x=>x.value);writeUx(ux);toast('Kit salvo neste computador.');open360(workerId);};
    $('#pcVUseKit').onclick=()=>{const ids=$$('#pcV300Body input:checked').map(x=>x.value);if(!ids.length)return toast('Selecione pelo menos um EPI.');prefillDelivery(workerId,ids,'Primeira entrega');};
    d.classList.add('open');
  }

  async function loadQr(){
    if(window.QRCode)return true;if(!navigator.onLine)return false;
    return new Promise(resolve=>{const s=document.createElement('script');s.src='https://cdn.jsdelivr.net/gh/davidshimjs/qrcodejs/qrcode.min.js';s.onload=()=>resolve(!!window.QRCode);s.onerror=()=>resolve(false);document.head.appendChild(s);});
  }
  async function openQr(workerId){
    const root=read(),w=root.app.workers.find(x=>x.id===workerId);if(!w)return;
    const d=modal(),body=$('#pcV300Body'),code='GEPI|'+workerId;
    body.innerHTML=`<div class="pc-v300-section"><h3>QR do trabalhador • ${esc(w.name)}</h3><div id="pcVQr" class="pc-v300-qr"></div><div class="pc-v300-code">${esc(code)}</div><p style="font-size:10px;color:#6b817d">O QR usa somente o identificador interno do trabalhador.</p><div class="pc-v300-actions"><button class="p" onclick="window.print()">Imprimir cartão</button></div></div>`;
    d.classList.add('open');const ok=await loadQr(),box=$('#pcVQr');box.innerHTML='';if(ok)new window.QRCode(box,{text:code,width:210,height:210,colorDark:'#173b47',colorLight:'#fff',correctLevel:window.QRCode.CorrectLevel.H});else box.innerHTML='<div class="empty">Conecte à internet uma vez para gerar o QR.</div>';
  }

  async function portal(workerId){
    const root=read(),w=root.app.workers.find(x=>x.id===workerId);if(!w)return;
    const api=window.GestaoEpiAuth?.api;if(!api)return toast('Entre no sistema primeiro.');if(!navigator.onLine)return toast('Conecte à internet para gerar o portal.');
    try{const r=await api('tenant_worker_portal_link',{workerId,days:90});if(!r?.ok)throw new Error(r?.message||'Falha ao gerar portal.');await navigator.clipboard.writeText(r.url);toast('Link do Portal copiado.');}catch(e){toast(e?.message||'Falha ao gerar portal.');}
  }

  function bind(){
    document.addEventListener('click',e=>{
      const b=e.target.closest('[data-pc-v300-worker]');if(b){open360(b.dataset.pcV300Worker);return;}
      const d=e.target.closest('[data-pcv-deliver]');if(d){const root=read(),w=root.app.workers.find(x=>x.id===d.dataset.pcvDeliver);prefillDelivery(w.id,kitFor(w),kitFor(w).length?'Primeira entrega':'');return;}
      const k=e.target.closest('[data-pcv-kit]');if(k){openKit(k.dataset.pcvKit);return;}
      const q=e.target.closest('[data-pcv-qr]');if(q){openQr(q.dataset.pcvQr);return;}
      const p=e.target.closest('[data-pcv-portal]');if(p){portal(p.dataset.pcvPortal);return;}
      const s=e.target.closest('[data-pcv-sheet]');if(s){$('#pcV300Modal')?.classList.remove('open');const sheet=document.querySelector('[data-worker-sheet="'+CSS.escape(s.dataset.pcvSheet)+'"]');sheet?.click();return;}
      const sw=e.target.closest('[data-pcv-swap]');if(sw){const [wid,eid]=sw.dataset.pcvSwap.split('|');prefillDelivery(wid,[eid],'Substituição por desgaste');return;}
    },true);
    window.addEventListener('online',decorate);window.addEventListener('offline',decorate);
  }

  function decorate(){
    clearTimeout(timer);timer=0;brand();login();decorateWorkers();
  }
  function queue(){if(timer)return;timer=setTimeout(decorate,70);}
  function boot(){
    styles();modal();decorate();bind();
    observer=new MutationObserver(queue);observer.observe(document.body,{childList:true,subtree:true});
    [250,800,1800,4200].forEach(ms=>setTimeout(queue,ms));
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();