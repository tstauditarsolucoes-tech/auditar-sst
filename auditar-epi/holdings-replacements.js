(() => {
  const APP_KEY='auditarEpiV1';
  const STOCK_KEY='auditarEpiStockV1';
  const RETURN_MARK='DEVOLUÇÃO EPI';
  const $=(s,r=document)=>r.querySelector(s);
  const esc=(v='')=>String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const norm=(v='')=>String(v??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim();
  const fmt=(iso)=>{try{return new Intl.DateTimeFormat('pt-BR',{dateStyle:'short'}).format(new Date(iso));}catch{return '—';}};
  const addDays=(iso,days)=>{const d=new Date(iso);d.setDate(d.getDate()+Number(days||0));return d;};
  const dayDiff=(a,b)=>Math.ceil((a-b)/(24*60*60*1000));

  function readApp(){try{return {companies:[],workers:[],epis:[],deliveries:[],...JSON.parse(localStorage.getItem(APP_KEY)||'{}')};}catch{return {companies:[],workers:[],epis:[],deliveries:[]};}}
  function readStock(){try{return {movements:[],...JSON.parse(localStorage.getItem(STOCK_KEY)||'{}')};}catch{return {movements:[]};}}
  function getField(note,key){const p=String(note||'').split('|').map(x=>x.trim()).find(x=>x.toLowerCase().startsWith(key.toLowerCase()+':'));return p?p.slice(p.indexOf(':')+1).trim():'';}
  function isReturn(m){return String(m?.note||'').trim().startsWith(RETURN_MARK);}
  function returnedQty(stock,workerId,epiId){return stock.movements.filter(m=>isReturn(m)&&m.epiId===epiId&&getField(m.note,'workerId')===workerId).reduce((s,m)=>s+Math.max(0,Number(getField(m.note,'qtd')||0)),0);}
  function deliveryItems(app,workerId,epiId){return app.deliveries.filter(d=>d.workerId===workerId).flatMap(d=>(d.items||[]).filter(i=>i.epiId===epiId).map(i=>({delivery:d,qty:Number(i.qty||0)})));}
  function deliveredQty(app,workerId,epiId){return deliveryItems(app,workerId,epiId).reduce((s,x)=>s+Math.max(0,x.qty),0);}
  function heldQty(app,stock,workerId,epiId){return Math.max(0,deliveredQty(app,workerId,epiId)-returnedQty(stock,workerId,epiId));}
  function latestDelivery(app,workerId,epiId){return deliveryItems(app,workerId,epiId).sort((a,b)=>String(b.delivery.createdAt||'').localeCompare(String(a.delivery.createdAt||'')))[0]?.delivery||null;}
  function companyName(app,id){return app.companies.find(x=>x.id===id)?.name||'Empresa';}
  function epi(app,id){return app.epis.find(x=>x.id===id);}

  function allHeldRows(){
    const app=readApp(),stock=readStock(),rows=[];
    app.workers.filter(w=>w.active!==false).forEach(w=>{
      app.epis.forEach(e=>{
        const qty=heldQty(app,stock,w.id,e.id);if(!qty)return;
        const d=latestDelivery(app,w.id,e.id);
        const cycle=Number(e.cycle||0);
        const due=d&&cycle>0?addDays(d.createdAt,cycle):null;
        rows.push({worker:w,epi:e,qty,latest:d,due,company:companyName(app,w.companyId)});
      });
    });
    return rows;
  }

  function statusOf(row){
    if(!row.due)return {key:'none',label:'Sem prazo',cls:'neutral',days:null};
    const days=dayDiff(row.due,new Date());
    if(days<0)return {key:'overdue',label:`Vencido há ${Math.abs(days)} dia(s)`,cls:'bad',days};
    if(days<=15)return {key:'soon',label:`Troca em ${days} dia(s)`,cls:'warn',days};
    return {key:'ok',label:`Em dia • ${days} dia(s)`,cls:'ok',days};
  }

  function injectStyles(){if($('#holdReplaceStyle'))return;const s=document.createElement('style');s.id='holdReplaceStyle';s.textContent=`
    .hr-card{background:#fff;border:1px solid var(--line,#d9e5e2);border-radius:18px;padding:14px;margin-bottom:12px}.hr-grid{display:grid;grid-template-columns:1fr 1fr;gap:9px}.hr-btn{border:1px solid #d7e5e1;background:#fff;border-radius:16px;padding:15px;text-align:left;min-height:92px;color:#173d39}.hr-btn span{font-size:24px;display:block}.hr-btn b{display:block;margin-top:6px}.hr-btn small{display:block;color:#6b817e;margin-top:3px}.hr-filter{display:grid;gap:9px}.hr-filter input,.hr-filter select{min-height:48px;border:1px solid #cededa;border-radius:13px;padding:0 12px;background:#fff}.hr-list{display:grid;gap:9px}.hr-row{border:1px solid #dce8e5;border-radius:14px;padding:12px;background:#fbfdfd}.hr-row-head{display:flex;justify-content:space-between;gap:10px}.hr-row b{color:#173d39}.hr-row small{display:block;color:#6b817e;margin-top:4px;line-height:1.35}.hr-pill{display:inline-block;padding:4px 8px;border-radius:999px;font-size:10px;font-weight:900;white-space:nowrap}.hr-pill.ok{background:#e9f8f2;color:#08795e}.hr-pill.warn{background:#fff5d9;color:#8a6110}.hr-pill.bad{background:#fdeaea;color:#a33131}.hr-pill.neutral{background:#eef2f2;color:#627471}.hr-empty{text-align:center;padding:22px;color:#708581}.hr-kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:10px}.hr-kpi{background:#f4f9f8;border-radius:13px;padding:10px;text-align:center}.hr-kpi strong{display:block;font-size:20px;color:#173d39}.hr-kpi span{font-size:10px;color:#6b817e}.hr-action{margin-top:9px;width:100%;min-height:42px;border:0;border-radius:11px;background:#0f766e;color:white;font-weight:850}
    @media(max-width:480px){.hr-grid{grid-template-columns:1fr 1fr}.hr-kpis{grid-template-columns:repeat(3,1fr)}}`;
    document.head.appendChild(s);
  }

  function injectHome(){const home=$('#home');if(!home||$('#hrHome'))return;const wrap=document.createElement('div');wrap.id='hrHome';wrap.className='hr-grid';wrap.innerHTML=`<button class="hr-btn" data-go="epiHeld"><span>👷</span><b>EPIs em posse</b><small>Veja o que cada trabalhador está usando</small></button><button class="hr-btn" data-go="epiReplacements"><span>🔄</span><b>Trocas</b><small>Vencidas, próximas e em dia</small></button>`;const stats=home.querySelector('.stats-grid');(stats||home.querySelector('.hero-card'))?.insertAdjacentElement('afterend',wrap);}

  function injectViews(){const main=$('.app-shell')||$('main');if(!main||$('#epiHeld'))return;
    const held=document.createElement('section');held.id='epiHeld';held.className='view';held.innerHTML=`<div class="view-head"><button class="back" data-go="home">←</button><div><h2>EPIs em posse</h2><p>Veja o que está vinculado a cada trabalhador.</p></div></div><div class="hr-card hr-filter"><select id="heldCompany"></select><input id="heldSearch" placeholder="Buscar trabalhador, setor ou EPI"></div><div id="heldList" class="hr-list"></div>`;
    const repl=document.createElement('section');repl.id='epiReplacements';repl.className='view';repl.innerHTML=`<div class="view-head"><button class="back" data-go="home">←</button><div><h2>Trocas de EPI</h2><p>Acompanhe vencimentos e substituições.</p></div></div><div class="hr-kpis"><div class="hr-kpi"><strong id="repOverdue">0</strong><span>Vencidos</span></div><div class="hr-kpi"><strong id="repSoon">0</strong><span>Próximos 15 dias</span></div><div class="hr-kpi"><strong id="repOk">0</strong><span>Em dia</span></div></div><div class="hr-card hr-filter"><select id="repCompany"></select><select id="repStatus"><option value="all">Todos</option><option value="overdue">Vencidos</option><option value="soon">Próximos</option><option value="ok">Em dia</option><option value="none">Sem prazo</option></select><input id="repSearch" placeholder="Buscar trabalhador, setor ou EPI"></div><div id="repList" class="hr-list"></div>`;
    main.appendChild(held);main.appendChild(repl);
  }

  function fillCompanies(){const app=readApp();['heldCompany','repCompany'].forEach(id=>{const sel=$('#'+id);if(!sel)return;const old=sel.value;sel.innerHTML='<option value="">Todas as empresas</option>'+app.companies.map(c=>`<option value="${esc(c.id)}">${esc(c.name)}</option>`).join('');if(app.companies.some(c=>c.id===old))sel.value=old;});}
  function rowMatch(row,companyId,q){if(companyId&&row.worker.companyId!==companyId)return false;if(!q)return true;return [row.worker.name,row.worker.reg,row.worker.role,row.worker.sector,row.epi.name,row.epi.ca].some(v=>norm(v).includes(q));}

  function renderHeld(){const root=$('#heldList');if(!root)return;const companyId=$('#heldCompany')?.value||'',q=norm($('#heldSearch')?.value||'');const rows=allHeldRows().filter(r=>rowMatch(r,companyId,q)).sort((a,b)=>String(a.worker.name).localeCompare(String(b.worker.name))||String(a.epi.name).localeCompare(String(b.epi.name)));root.innerHTML=rows.length?rows.map(r=>{const st=statusOf(r);return `<div class="hr-row"><div class="hr-row-head"><div><b>${esc(r.worker.name)}</b><small>${esc(r.company)}${r.worker.sector?' • '+esc(r.worker.sector):''}</small></div><span class="hr-pill ${st.cls}">${esc(st.label)}</span></div><small><b>${esc(r.epi.name)}</b>${r.epi.ca?' • CA '+esc(r.epi.ca):''} • Quantidade em posse: <b>${r.qty}</b></small><small>Última entrega: ${r.latest?fmt(r.latest.createdAt):'—'}${r.due?' • Próxima troca: '+fmt(r.due):''}</small><button class="hr-action" data-go="epiReturn">↩ Registrar devolução</button></div>`;}).join(''):'<div class="hr-empty">Nenhum EPI em posse encontrado.</div>';}

  function renderReplacements(){const root=$('#repList');if(!root)return;const companyId=$('#repCompany')?.value||'',q=norm($('#repSearch')?.value||''),filter=$('#repStatus')?.value||'all';const all=allHeldRows();const counts={overdue:0,soon:0,ok:0};all.forEach(r=>{const k=statusOf(r).key;if(counts[k]!=null)counts[k]++;});$('#repOverdue').textContent=counts.overdue;$('#repSoon').textContent=counts.soon;$('#repOk').textContent=counts.ok;const rows=all.filter(r=>{const st=statusOf(r);return rowMatch(r,companyId,q)&&(filter==='all'||st.key===filter);}).sort((a,b)=>{const sa=statusOf(a),sb=statusOf(b);const rank={overdue:0,soon:1,ok:2,none:3};return rank[sa.key]-rank[sb.key]||((a.due?.getTime()||9e15)-(b.due?.getTime()||9e15));});root.innerHTML=rows.length?rows.map(r=>{const st=statusOf(r);return `<div class="hr-row"><div class="hr-row-head"><div><b>${esc(r.worker.name)}</b><small>${esc(r.company)}${r.worker.sector?' • '+esc(r.worker.sector):''}</small></div><span class="hr-pill ${st.cls}">${esc(st.label)}</span></div><small><b>${esc(r.epi.name)}</b>${r.epi.cycle?` • ciclo ${Number(r.epi.cycle)} dia(s)`:''}</small><small>Última entrega: ${r.latest?fmt(r.latest.createdAt):'—'}${r.due?' • Data prevista: '+fmt(r.due):''}</small><button class="hr-action" data-go="delivery" data-replace-worker="${esc(r.worker.id)}" data-replace-epi="${esc(r.epi.id)}">＋ Registrar troca / nova entrega</button></div>`;}).join(''):'<div class="hr-empty">Nenhuma troca encontrada neste filtro.</div>';}

  function ensureReasons(){const sel=$('#deliveryReason');if(!sel)return;const wanted=['Primeira entrega','Substituição por vencimento previsto','Substituição por desgaste','Substituição por dano','Perda','Necessidade operacional','Outro'];const current=[...sel.options].map(o=>o.textContent);wanted.forEach(v=>{if(!current.includes(v)){const o=document.createElement('option');o.textContent=v;o.value=v;sel.appendChild(o);}});}
  function prefillReplacement(btn){setTimeout(()=>{const app=readApp(),w=app.workers.find(x=>x.id===btn.dataset.replaceWorker);if(w&&$('#deliveryCompany')){$('#deliveryCompany').value=w.companyId;$('#deliveryCompany').dispatchEvent(new Event('change',{bubbles:true}));setTimeout(()=>{if($('#deliveryWorker'))$('#deliveryWorker').value=w.id;},50);}if($('#deliveryReason'))$('#deliveryReason').value='Substituição por vencimento previsto';setTimeout(()=>{const epiId=btn.dataset.replaceEpi;const first=$('.item-epi');if(first&&[...first.options].some(o=>o.value===epiId))first.value=epiId;},80);},80);}

  function bind(){['heldCompany','heldSearch'].forEach(id=>$('#'+id)?.addEventListener(id.includes('Search')?'input':'change',renderHeld));['repCompany','repStatus'].forEach(id=>$('#'+id)?.addEventListener('change',renderReplacements));$('#repSearch')?.addEventListener('input',renderReplacements);document.addEventListener('click',e=>{const b=e.target.closest('[data-replace-worker]');if(b)prefillReplacement(b);});document.addEventListener('auditar-epi-data-changed',()=>{fillCompanies();renderHeld();renderReplacements();});window.addEventListener('storage',()=>{fillCompanies();renderHeld();renderReplacements();});}
  function boot(){injectStyles();injectViews();injectHome();fillCompanies();ensureReasons();renderHeld();renderReplacements();bind();setTimeout(()=>{fillCompanies();ensureReasons();renderHeld();renderReplacements();},900);}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
