(() => {
  const APP_KEY='auditarEpiV1';
  const STOCK_KEY='auditarEpiStockV1';
  const MARK='DEVOLUÇÃO EPI';
  const $=(s,r=document)=>r.querySelector(s);
  const $$=(s,r=document)=>[...r.querySelectorAll(s)];
  const esc=(v='')=>String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const norm=(v='')=>String(v).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim();
  const uid=p=>`${p}_${Date.now()}_${Math.random().toString(36).slice(2,8)}`;

  function readApp(){try{return {companies:[],workers:[],epis:[],deliveries:[],...JSON.parse(localStorage.getItem(APP_KEY)||'{}')};}catch{return {companies:[],workers:[],epis:[],deliveries:[]};}}
  function readStock(){try{return {startedAt:'',processedDeliveryIds:[],movements:[],minimums:{},...JSON.parse(localStorage.getItem(STOCK_KEY)||'{}')};}catch{return {startedAt:'',processedDeliveryIds:[],movements:[],minimums:{}};}}
  function writeStock(x){localStorage.setItem(STOCK_KEY,JSON.stringify(x));document.dispatchEvent(new CustomEvent('auditar-epi-data-changed'));}
  function toast(msg){const el=$('#toast');if(!el)return alert(msg);el.textContent=msg;el.classList.add('show');setTimeout(()=>el.classList.remove('show'),2800);}
  function safe(v=''){return String(v).replace(/\|/g,'/').replace(/\s+/g,' ').trim();}
  function sk(c,e){return `${c}::${e}`;}
  function balance(stock,c,e){return stock.movements.filter(m=>m.companyId===c&&m.epiId===e).reduce((s,m)=>s+Number(m.delta||0),0);}
  function getField(note,key){const part=String(note||'').split('|').map(x=>x.trim()).find(x=>x.toLowerCase().startsWith(key.toLowerCase()+':'));return part?part.slice(part.indexOf(':')+1).trim():'';}
  function isReturn(m){return String(m?.note||'').trim().startsWith(MARK);}
  function returnedQty(stock,workerId,epiId){return stock.movements.filter(m=>isReturn(m)&&m.epiId===epiId&&getField(m.note,'workerId')===workerId).reduce((s,m)=>s+Math.max(0,Number(getField(m.note,'qtd')||0)),0);}
  function deliveredQty(app,workerId,epiId){return app.deliveries.filter(d=>d.workerId===workerId).reduce((sum,d)=>sum+(d.items||[]).filter(i=>i.epiId===epiId).reduce((s,i)=>s+Math.max(0,Number(i.qty||0)),0),0);}
  function heldQty(app,stock,workerId,epiId){return Math.max(0,deliveredQty(app,workerId,epiId)-returnedQty(stock,workerId,epiId));}
  function companyName(app,id){return app.companies.find(x=>x.id===id)?.name||'Empresa';}
  function workerName(app,id){return app.workers.find(x=>x.id===id)?.name||'Colaborador';}
  function epiName(app,id){return app.epis.find(x=>x.id===id)?.name||'EPI';}

  function injectStyles(){if($('#epiReturnStyle'))return;const s=document.createElement('style');s.id='epiReturnStyle';s.textContent=`
    .return-hero-btn{width:100%;min-height:66px;border:0;border-radius:17px;background:#fff;color:#0f766e;border:2px solid #0f766e;font-weight:950;font-size:17px;margin-top:10px;box-shadow:0 8px 22px rgba(15,118,110,.12)}
    .return-card{background:#fff;border:1px solid var(--line,#d9e5e2);border-radius:18px;padding:15px;margin-bottom:12px;box-shadow:0 8px 22px rgba(17,55,50,.06)}
    .return-grid{display:grid;gap:12px}.return-grid label{display:grid;gap:6px;font-weight:850;color:#355b57;font-size:12px}.return-grid input,.return-grid select,.return-grid textarea{width:100%;box-sizing:border-box;min-height:50px;border:1px solid #cededa;border-radius:13px;padding:10px 12px;background:#fff;color:#173d39;font-size:15px}.return-grid textarea{min-height:78px;resize:vertical}
    .return-balance{padding:10px 12px;border-radius:12px;background:#eef8f6;color:#176f65;font-weight:850;font-size:12px}.return-help{font-size:11px;color:#69807d;line-height:1.4;margin-top:-5px}.return-dest{display:grid;grid-template-columns:1fr 1fr;gap:9px}.return-choice{border:1px solid #cededa;border-radius:14px;padding:12px;display:flex!important;gap:8px!important;align-items:flex-start;font-size:12px!important}.return-choice input{width:auto!important;min-height:auto!important;margin-top:2px}.return-choice strong{display:block;font-size:13px;color:#173d39}.return-choice small{display:block;color:#69807d;margin-top:3px;font-weight:600}
    .return-save{width:100%;min-height:58px;border:0;border-radius:15px;background:#0f766e;color:#fff;font-weight:950;font-size:16px}.return-history{display:grid;gap:8px}.return-row{border:1px solid #dce8e5;border-radius:13px;padding:11px 12px;background:#fbfdfd}.return-row b{display:block;color:#173d39}.return-row small{display:block;color:#6b817e;margin-top:4px;line-height:1.35}.return-pill{display:inline-block;padding:3px 7px;border-radius:999px;background:#eef8f6;color:#0f766e;font-size:10px;font-weight:900;margin-top:6px}.return-pill.no{background:#fff3e8;color:#a45a12}
    @media(max-width:480px){.return-dest{grid-template-columns:1fr}.return-card{padding:13px}.return-hero-btn{font-size:16px}}
  `;document.head.appendChild(s);}

  function injectView(){
    if($('#epiReturn'))return;
    const main=$('.app-shell')||$('main');if(!main)return;
    const sec=document.createElement('section');sec.id='epiReturn';sec.className='view';sec.innerHTML=`
      <div class="view-head"><button class="back" data-go="home">←</button><div><h2>Devolver EPI</h2><p>Registre a devolução em poucos toques.</p></div></div>
      <div class="return-card return-grid">
        <label>Empresa<select id="returnCompany"></select></label>
        <label>Buscar trabalhador<input id="returnWorkerSearch" placeholder="Digite nome, CPF ou matrícula" autocomplete="off"></label>
        <label>Trabalhador<select id="returnWorker"></select></label>
        <label>EPI a devolver<select id="returnEpi"></select></label>
        <div id="returnBalance" class="return-balance">Selecione o trabalhador e o EPI.</div>
        <label>Quantidade<input id="returnQty" type="number" min="1" inputmode="numeric" value="1"></label>
        <label>Motivo<select id="returnReason"><option>Troca / substituição</option><option>Desligamento</option><option>Fim de atividade</option><option>EPI entregue indevidamente</option><option>Devolução voluntária</option><option>Outro</option></select></label>
        <label>Condição do EPI<select id="returnCondition"><option value="good">Bom / reutilizável</option><option value="clean">Precisa higienização / avaliação</option><option value="damaged">Danificado</option><option value="discard">Inservível / descarte</option></select></label>
        <div>
          <b style="display:block;margin-bottom:8px;color:#355b57;font-size:12px">Voltar ao estoque?</b>
          <div class="return-dest">
            <label class="return-choice"><input type="radio" name="returnToStock" value="yes" checked><span><strong>Sim</strong><small>Soma a quantidade devolvida ao saldo.</small></span></label>
            <label class="return-choice"><input type="radio" name="returnToStock" value="no"><span><strong>Não</strong><small>Registra a devolução sem aumentar o estoque.</small></span></label>
          </div>
          <p id="returnDestHelp" class="return-help">Para EPI em bom estado, o padrão é voltar ao estoque.</p>
        </div>
        <label>Responsável pelo recebimento<input id="returnResponsible" placeholder="Nome do responsável"></label>
        <label>Observação<textarea id="returnNote" placeholder="Opcional. Ex.: separado para higienização"></textarea></label>
        <button id="btnSaveReturn" class="return-save" type="button">↩ Confirmar devolução</button>
      </div>
      <div class="return-card"><h3 style="margin:0 0 10px;color:#173d39">Últimas devoluções</h3><div id="returnHistory" class="return-history"></div></div>`;
    main.appendChild(sec);
  }

  function ensureHomeEntry(){
    if($('#btnEpiReturnHome'))return;
    const home=$('#home');if(!home)return;
    const btn=document.createElement('button');btn.id='btnEpiReturnHome';btn.className='return-hero-btn';btn.type='button';btn.dataset.go='epiReturn';btn.textContent='↩ Devolver EPI';
    const hero=home.querySelector('.hero-card');if(hero)hero.insertAdjacentElement('afterend',btn);else home.prepend(btn);
  }

  function fillCompanies(){const app=readApp(),sel=$('#returnCompany');if(!sel)return;const old=sel.value;sel.innerHTML='<option value="">Selecione a empresa</option>'+app.companies.map(c=>`<option value="${esc(c.id)}">${esc(c.name)}</option>`).join('');if(app.companies.some(c=>c.id===old))sel.value=old;else if(app.companies.length===1)sel.value=app.companies[0].id;fillWorkers();}
  function workersForCompany(){const app=readApp(),c=$('#returnCompany')?.value||'',q=norm($('#returnWorkerSearch')?.value||'');return app.workers.filter(w=>w.active!==false&&(!c||w.companyId===c)&&(!q||[w.name,w.cpf,w.reg,w.role,w.sector].some(v=>norm(v).includes(q))));}
  function fillWorkers(){const sel=$('#returnWorker');if(!sel)return;const old=sel.value,rows=workersForCompany();sel.innerHTML='<option value="">Selecione o trabalhador</option>'+rows.map(w=>`<option value="${esc(w.id)}">${esc(w.name)}${w.sector?' • '+esc(w.sector):''}</option>`).join('');if(rows.some(w=>w.id===old))sel.value=old;fillHeldEpis();}
  function fillHeldEpis(){const app=readApp(),stock=readStock(),workerId=$('#returnWorker')?.value||'',sel=$('#returnEpi');if(!sel)return;const old=sel.value;const rows=workerId?app.epis.map(e=>({e,qty:heldQty(app,stock,workerId,e.id)})).filter(x=>x.qty>0):[];sel.innerHTML='<option value="">'+(workerId?'Selecione o EPI':'Selecione o trabalhador primeiro')+'</option>'+rows.map(x=>`<option value="${esc(x.e.id)}">${esc(x.e.name)}${x.e.ca?' • CA '+esc(x.e.ca):''} • em posse: ${x.qty}</option>`).join('');if(rows.some(x=>x.e.id===old))sel.value=old;updateBalance();}
  function updateBalance(){const app=readApp(),stock=readStock(),workerId=$('#returnWorker')?.value||'',epiId=$('#returnEpi')?.value||'',el=$('#returnBalance');if(!el)return;if(!workerId||!epiId){el.textContent=workerId?'Escolha qual EPI será devolvido.':'Selecione o trabalhador e o EPI.';return;}const q=heldQty(app,stock,workerId,epiId);el.textContent=`Quantidade ainda vinculada ao trabalhador: ${q}`;const input=$('#returnQty');input.max=String(q);if(Number(input.value||1)>q)input.value=String(Math.max(1,q));}
  function applyConditionDefault(){const cond=$('#returnCondition')?.value||'good';const yes=$('input[name="returnToStock"][value="yes"]'),no=$('input[name="returnToStock"][value="no"]'),help=$('#returnDestHelp');if(cond==='good'){yes.checked=true;help.textContent='EPI em bom estado: o padrão é voltar ao estoque.';}else if(cond==='clean'){no.checked=true;help.textContent='Precisa higienização/avaliação: o padrão é não voltar ao saldo agora.';}else{no.checked=true;help.textContent='EPI danificado ou inservível: o padrão é não voltar ao estoque.';}}

  function buildNote(meta){return `${MARK} | workerId:${safe(meta.workerId)} | trabalhador:${safe(meta.worker)} | qtd:${meta.qty} | motivo:${safe(meta.reason)} | condição:${safe(meta.condition)} | estoque:${meta.toStock?'SIM':'NÃO'} | responsável:${safe(meta.responsible||'—')}${meta.obs?` | obs:${safe(meta.obs)}`:''}`;}
  function conditionLabel(v){return ({good:'Bom / reutilizável',clean:'Precisa higienização / avaliação',damaged:'Danificado',discard:'Inservível / descarte'})[v]||v;}

  function saveReturn(){
    const app=readApp(),stock=readStock();const companyId=$('#returnCompany')?.value||'',workerId=$('#returnWorker')?.value||'',epiId=$('#returnEpi')?.value||'',qty=Math.max(0,Number($('#returnQty')?.value||0));
    if(!companyId)return toast('Selecione a empresa.');if(!workerId)return toast('Selecione o trabalhador.');if(!epiId)return toast('Selecione o EPI.');if(!qty)return toast('Informe a quantidade devolvida.');
    const available=heldQty(app,stock,workerId,epiId);if(qty>available)return toast(`O trabalhador possui ${available} unidade(s) deste EPI vinculada(s).`);
    const toStock=$('input[name="returnToStock"]:checked')?.value==='yes',condition=$('#returnCondition')?.value||'good',reason=$('#returnReason')?.value||'Outro',responsible=String($('#returnResponsible')?.value||'').trim(),obs=String($('#returnNote')?.value||'').trim();
    const meta={workerId,worker:workerName(app,workerId),qty,reason,condition:conditionLabel(condition),toStock,responsible,obs};
    const current=balance(stock,companyId,epiId);if(!toStock&&current<0)return toast('O estoque está negativo. Ajuste o saldo antes de registrar devolução sem retorno ao estoque.');
    const key=sk(companyId,epiId);if(stock.minimums[key]==null)stock.minimums[key]=5;
    stock.movements.unshift({id:uid('sm'),type:toStock?'IN':'SET',delta:toStock?qty:0,companyId,epiId,note:buildNote(meta),createdAt:new Date().toISOString(),updatedAt:new Date().toISOString()});
    writeStock(stock);
    toast(toStock?'Devolução registrada e EPI voltou ao estoque.':'Devolução registrada sem retorno ao estoque.');
    $('#returnQty').value='1';$('#returnNote').value='';fillHeldEpis();renderHistory();rewriteStockHistory();
  }

  function renderHistory(){const root=$('#returnHistory');if(!root)return;const app=readApp(),stock=readStock(),c=$('#returnCompany')?.value||'';const rows=stock.movements.filter(m=>isReturn(m)&&(!c||m.companyId===c)).slice(0,40);root.innerHTML=rows.length?rows.map(m=>{const to=getField(m.note,'estoque')==='SIM',qty=getField(m.note,'qtd')||'0',worker=getField(m.note,'trabalhador')||workerName(app,getField(m.note,'workerId')),reason=getField(m.note,'motivo')||'—',cond=getField(m.note,'condição')||'—';return `<div class="return-row"><b>${esc(worker)} • ${esc(epiName(app,m.epiId))}</b><small>${new Intl.DateTimeFormat('pt-BR',{dateStyle:'short',timeStyle:'short'}).format(new Date(m.createdAt))} • Qtd. ${esc(qty)}<br>${esc(reason)} • ${esc(cond)}</small><span class="return-pill ${to?'':'no'}">${to?'VOLTOU AO ESTOQUE':'NÃO VOLTOU AO ESTOQUE'}</span></div>`;}).join(''):'<div class="empty">Nenhuma devolução registrada.</div>';}

  function rewriteStockHistory(){setTimeout(()=>{$$('#stockHistory .stock-move small').forEach(el=>{if(el.textContent.includes(MARK))el.textContent=el.textContent.replace(/^Entrada\s*•|^Ajuste\s*•/,'Devolução •');});},80);}

  function bind(){
    document.addEventListener('click',e=>{if(e.target.closest('[data-go="epiReturn"]'))setTimeout(()=>{fillCompanies();renderHistory();},30);});
    $('#returnCompany')?.addEventListener('change',()=>{fillWorkers();renderHistory();});$('#returnWorkerSearch')?.addEventListener('input',fillWorkers);$('#returnWorker')?.addEventListener('change',fillHeldEpis);$('#returnEpi')?.addEventListener('change',updateBalance);$('#returnCondition')?.addEventListener('change',applyConditionDefault);$('#btnSaveReturn')?.addEventListener('click',saveReturn);
    const hist=$('#stockHistory');if(hist)new MutationObserver(rewriteStockHistory).observe(hist,{childList:true,subtree:true});
    document.addEventListener('auditar-epi-data-changed',()=>setTimeout(()=>{if($('#epiReturn')?.classList.contains('active')){fillCompanies();renderHistory();}},120));
  }

  function boot(){injectStyles();injectView();ensureHomeEntry();bind();fillCompanies();renderHistory();applyConditionDefault();[300,900,1800].forEach(ms=>setTimeout(ensureHomeEntry,ms));}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();