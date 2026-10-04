(()=>{
  'use strict';
  const $=(s,r=document)=>r.querySelector(s);
  const $$=(s,r=document)=>[...r.querySelectorAll(s)];
  const api=(action,extra={})=>window.GestaoEpiAuth?.api?.(action,extra);
  let currentWorkerId='',currentWorkerName='',observer=null,decorateTimer=0;

  function esc(v=''){return String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
  function canOperate(){const role=String(window.GestaoEpiAuth?.user?.()?.role||'');return role==='admin'||role==='campo';}
  function toast(msg){const e=$('#toast');if(!e)return alert(msg);e.textContent=msg;e.classList.add('show');setTimeout(()=>e.classList.remove('show'),2800);}
  function fmt(v){if(!v)return '—';const d=new Date(v);if(Number.isNaN(d.getTime()))return '—';return new Intl.DateTimeFormat('pt-BR',{dateStyle:'short',timeStyle:'short'}).format(d);}

  function styles(){
    if($('#pcWorkerPortalStyle'))return;
    const s=document.createElement('style');s.id='pcWorkerPortalStyle';s.textContent=`
      .worker-portal-btn{border:1px solid #b8d8d2;background:#eaf7f4;color:#0f766e;border-radius:9px;padding:7px 9px;font-weight:900;font-size:10px;cursor:pointer;white-space:nowrap;margin-left:5px}
      .worker-portal-btn:hover{background:#dff2ee}.worker-portal-btn:disabled{opacity:.55;cursor:wait}
      .worker-portal-modal{position:fixed;inset:0;z-index:33000;background:rgba(7,37,34,.74);display:none;align-items:center;justify-content:center;padding:22px}.worker-portal-modal.open{display:flex}
      .worker-portal-card{width:min(650px,100%);background:#fff;border-radius:22px;padding:22px;box-shadow:0 30px 90px rgba(0,0,0,.28)}
      .worker-portal-head{display:flex;justify-content:space-between;align-items:flex-start;gap:15px}.worker-portal-head h2{margin:0;color:#173d39;font-size:20px}.worker-portal-head p{margin:5px 0 0;color:#6b817d;font-size:11px}.worker-portal-close{border:0;background:#edf5f4;border-radius:11px;width:40px;height:40px;font-size:22px;cursor:pointer}
      .worker-portal-info{margin:16px 0;background:#f1f8f6;border:1px solid #d7e8e4;border-radius:14px;padding:13px;color:#355b57;font-size:11px;line-height:1.5}
      .worker-portal-actions{display:flex;gap:8px;flex-wrap:wrap}.worker-portal-actions button{border:0;border-radius:11px;padding:10px 13px;font-weight:900;font-size:11px;cursor:pointer}
      .worker-portal-actions .primary{background:#0f766e;color:#fff}.worker-portal-actions .soft{background:#eaf5f3;color:#0f665f}.worker-portal-actions .danger{background:#fff0ee;color:#b42318}
      .worker-portal-link{display:none;margin-top:15px}.worker-portal-link.open{display:block}.worker-portal-link label{display:block;font-size:10px;font-weight:900;color:#4a6561;margin-bottom:5px}.worker-portal-link input{width:100%;height:46px;border:1px solid #cedfdb;border-radius:11px;padding:0 11px;font-size:11px;color:#355b57;background:#fbfdfd}
      .worker-portal-expiry{margin:7px 0 12px;color:#6b817d;font-size:10px}.worker-portal-security{margin-top:14px;border-top:1px solid #e4eeec;padding-top:12px;color:#6b817d;font-size:10px;line-height:1.55}
      @media(max-width:700px){.worker-portal-card{padding:17px}.worker-portal-actions{display:grid;grid-template-columns:1fr 1fr}.worker-portal-actions button{width:100%}}
    `;document.head.appendChild(s);
  }

  function modal(){
    if($('#pcWorkerPortalModal'))return;
    const d=document.createElement('div');d.id='pcWorkerPortalModal';d.className='worker-portal-modal';d.innerHTML=`
      <div class="worker-portal-card">
        <div class="worker-portal-head">
          <div><h2>Portal do Trabalhador</h2><p id="pcWorkerPortalSubtitle">Acesso individual aos registros de EPI.</p></div>
          <button class="worker-portal-close" id="pcWorkerPortalClose" type="button">×</button>
        </div>
        <div class="worker-portal-info"><b>🔒 Link individual e revogável</b><br>Ao gerar um novo link, qualquer link anterior deste trabalhador deixa de funcionar. O trabalhador verá somente os próprios registros.</div>
        <div class="worker-portal-actions">
          <button id="pcWorkerPortalGenerate" class="primary" type="button">🔗 Gerar novo link</button>
          <button id="pcWorkerPortalCopy" class="soft" type="button" disabled>📋 Copiar link</button>
          <button id="pcWorkerPortalOpen" class="soft" type="button" disabled>↗ Abrir portal</button>
          <button id="pcWorkerPortalRevoke" class="danger" type="button">Revogar acesso</button>
        </div>
        <div id="pcWorkerPortalLinkBox" class="worker-portal-link">
          <label>Link para enviar ao trabalhador</label>
          <input id="pcWorkerPortalUrl" readonly>
          <div id="pcWorkerPortalExpiry" class="worker-portal-expiry"></div>
        </div>
        <div class="worker-portal-security">O link padrão vale por 90 dias. Se o trabalhador for inativado, o portal deixa de abrir. O portal não expõe template biométrico nem foto facial.</div>
      </div>`;document.body.appendChild(d);
    $('#pcWorkerPortalClose').onclick=close;
    d.addEventListener('click',e=>{if(e.target===d)close();});
    $('#pcWorkerPortalGenerate').onclick=generate;
    $('#pcWorkerPortalCopy').onclick=copy;
    $('#pcWorkerPortalOpen').onclick=openPortal;
    $('#pcWorkerPortalRevoke').onclick=revoke;
  }

  function open(workerId,name=''){
    currentWorkerId=String(workerId||'');currentWorkerName=String(name||'');
    if(!currentWorkerId)return;
    modal();
    $('#pcWorkerPortalSubtitle').textContent=(currentWorkerName||'Trabalhador')+' • acesso individual aos registros de EPI.';
    $('#pcWorkerPortalUrl').value='';$('#pcWorkerPortalExpiry').textContent='';
    $('#pcWorkerPortalLinkBox').classList.remove('open');
    $('#pcWorkerPortalCopy').disabled=true;$('#pcWorkerPortalOpen').disabled=true;
    $('#pcWorkerPortalModal').classList.add('open');
  }
  function close(){$('#pcWorkerPortalModal')?.classList.remove('open');}
  async function generate(){
    const b=$('#pcWorkerPortalGenerate');if(!currentWorkerId||!api)return;
    b.disabled=true;b.textContent='Gerando…';
    try{
      const r=await api('tenant_worker_portal_link',{workerId:currentWorkerId,days:90});
      if(!r?.ok)throw new Error(r?.message||'Não foi possível gerar o portal.');
      $('#pcWorkerPortalUrl').value=String(r.url||'');
      $('#pcWorkerPortalExpiry').textContent='Válido até '+fmt(r.expiresAt)+' • links anteriores foram invalidados.';
      $('#pcWorkerPortalLinkBox').classList.add('open');
      $('#pcWorkerPortalCopy').disabled=!r.url;$('#pcWorkerPortalOpen').disabled=!r.url;
      toast('Novo acesso do Portal do Trabalhador criado.');
    }catch(err){toast(err?.message||'Falha ao gerar link.');}
    finally{b.disabled=false;b.textContent='🔗 Gerar novo link';}
  }
  async function copy(){
    const url=$('#pcWorkerPortalUrl')?.value||'';if(!url)return;
    try{await navigator.clipboard.writeText(url);toast('Link copiado.');}
    catch(_){const i=$('#pcWorkerPortalUrl');i.focus();i.select();document.execCommand('copy');toast('Link copiado.');}
  }
  function openPortal(){const url=$('#pcWorkerPortalUrl')?.value||'';if(url)window.open(url,'_blank','noopener,noreferrer');}
  async function revoke(){
    if(!currentWorkerId||!api)return;
    if(!confirm('Revogar o acesso do Portal do Trabalhador? O histórico de EPI não será apagado.'))return;
    const b=$('#pcWorkerPortalRevoke');b.disabled=true;b.textContent='Revogando…';
    try{
      const r=await api('tenant_worker_portal_revoke',{workerId:currentWorkerId});
      if(!r?.ok)throw new Error(r?.message||'Não foi possível revogar.');
      $('#pcWorkerPortalUrl').value='';$('#pcWorkerPortalLinkBox').classList.remove('open');$('#pcWorkerPortalCopy').disabled=true;$('#pcWorkerPortalOpen').disabled=true;
      toast('Acesso do trabalhador revogado.');
    }catch(err){toast(err?.message||'Falha ao revogar acesso.');}
    finally{b.disabled=false;b.textContent='Revogar acesso';}
  }

  function decorate(){
    clearTimeout(decorateTimer);decorateTimer=0;
    if(!canOperate()){$('[data-worker-portal]').forEach(b=>b.remove());return;}
    $('#workerTable [data-worker-sheet]').forEach(sheet=>{
      const id=sheet.dataset.workerSheet;if(!id||sheet.parentElement.querySelector('[data-worker-portal]'))return;
      const b=document.createElement('button');b.type='button';b.className='worker-portal-btn';b.dataset.workerPortal=id;b.textContent='🌐 Portal';
      b.addEventListener('click',e=>{e.preventDefault();e.stopPropagation();const root=read();const w=root?.app?.workers?.find(x=>x.id===id);open(id,w?.name||'');});
      sheet.insertAdjacentElement('afterend',b);
    });
  }
  function read(){try{return JSON.parse(localStorage.getItem('auditarEpiGestaoCacheV1')||'{}');}catch(_){return {};}}
  function queue(){if(decorateTimer)return;decorateTimer=setTimeout(decorate,60);}
  function boot(){
    styles();modal();queue();
    const table=$('#workerTable');if(table){observer=new MutationObserver(queue);observer.observe(table,{childList:true,subtree:true});}
    document.addEventListener('click',e=>{if(e.target.closest('.nav[data-view="workers"]'))setTimeout(queue,120);});
    ['input','change'].forEach(type=>document.addEventListener(type,e=>{if(e.target?.matches?.('#workerSearch,#globalCompany'))setTimeout(queue,80);},true));
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();