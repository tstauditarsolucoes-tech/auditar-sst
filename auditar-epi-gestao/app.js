(() => {
  const ENDPOINT='https://script.google.com/macros/s/AKfycbxqMnKiTlAJTFv3-odS2dB1NRcSD8wwvtNxxa-zCFhTM6GeNZszib_1N6eT9wSnOnOyjg/exec';
  const KEY_STORE='auditarEpiCentralKey';
  const CACHE_STORE='auditarEpiGestaoCacheV1';
  const DEVICE_STORE='auditarEpiGestaoDeviceId';
  let data=blank();
  let syncing=false;
  let dialogSaveHandler=null;

  const $=(s,root=document)=>root.querySelector(s);
  const $$=(s,root=document)=>[...root.querySelectorAll(s)];
  const esc=(v='')=>String(v).replace(/[&<>'\"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','\"':'&quot;'}[c]));
  const norm=(v='')=>String(v??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim();
  const digits=(v='')=>String(v).replace(/\D/g,'');
  const uid=p=>`${p}_${Date.now()}_${Math.random().toString(36).slice(2,9)}`;
  const now=()=>new Date().toISOString();

  function blank(){return {version:1,revision:0,updatedAt:'',app:{companies:[],workers:[],epis:[],deliveries:[]},stock:{startedAt:'',processedDeliveryIds:[],movements:[],minimums:{}}};}
  function normalize(root){
    const x=root&&typeof root==='object'?root:{};
    const app=x.app&&typeof x.app==='object'?x.app:{};
    const stock=x.stock&&typeof x.stock==='object'?x.stock:{};
    return {version:1,revision:Number(x.revision||0),updatedAt:String(x.updatedAt||''),app:{companies:Array.isArray(app.companies)?app.companies:[],workers:Array.isArray(app.workers)?app.workers:[],epis:Array.isArray(app.epis)?app.epis:[],deliveries:Array.isArray(app.deliveries)?app.deliveries:[]},stock:{startedAt:String(stock.startedAt||''),processedDeliveryIds:Array.isArray(stock.processedDeliveryIds)?stock.processedDeliveryIds:[],movements:Array.isArray(stock.movements)?stock.movements:[],minimums:stock.minimums&&typeof stock.minimums==='object'?stock.minimums:{}}};
  }
  function loadCache(){try{return normalize(JSON.parse(localStorage.getItem(CACHE_STORE)||'{}'));}catch{return blank();}}
  function saveCache(){localStorage.setItem(CACHE_STORE,JSON.stringify(data));}
  function deviceId(){let x=localStorage.getItem(DEVICE_STORE);if(!x){x=uid('gestao');localStorage.setItem(DEVICE_STORE,x);}return x;}
  function company(id){return data.app.companies.find(x=>x.id===id);}
  function worker(id){return data.app.workers.find(x=>x.id===id);}
  function epi(id){return data.app.epis.find(x=>x.id===id);}
  function sk(companyId,epiId){return `${companyId}::${epiId}`;}
  function balance(companyId,epiId){return data.stock.movements.filter(m=>m.companyId===companyId&&m.epiId===epiId).reduce((s,m)=>s+Number(m.delta||0),0);}
  function selectedCompany(){return $('#globalCompany')?.value||'';}
  function companyMatch(id){const c=selectedCompany();return !c||c===id;}

  function toast(msg){const el=$('#toast');if(!el)return;el.textContent=msg;el.classList.add('show');setTimeout(()=>el.classList.remove('show'),2600);}
  function setSync(kind,text){const dot=$('#syncDot');if(dot)dot.className='sync-dot '+kind;$('#syncStatus').textContent=text;if(kind==='ok')$('#syncTime').textContent='Atualizado '+new Intl.DateTimeFormat('pt-BR',{hour:'2-digit',minute:'2-digit'}).format(new Date());}

  async function sync({silent=false}={}){
    const key=(localStorage.getItem(KEY_STORE)||'').trim();
    if(!key){showConnect();return false;}
    if(syncing)return false;
    if(!navigator.onLine){setSync('error','Sem internet');return false;}
    syncing=true;setSync('busy','Sincronizando…');
    try{
      const res=await fetch(ENDPOINT,{method:'POST',headers:{'Content-Type':'text/plain;charset=utf-8'},body:JSON.stringify({action:'epi_sync_merge',syncKey:key,deviceId:deviceId(),client:'gestao',payload:data})});
      const json=await res.json();
      if(!json?.ok)throw new Error(json?.message||'Falha na sincronização.');
      data=normalize(json.payload||{});saveCache();setSync('ok','Sincronizado');renderAll();hideConnect();if(!silent)toast('Dados sincronizados.');return true;
    }catch(err){setSync('error','Falha na sync');if(!silent)toast(err.message||'Falha na sincronização.');return false;}
    finally{syncing=false;}
  }

  function showConnect(){const o=$('#connectOverlay');if(o)o.classList.remove('hidden');}
  function hideConnect(){const o=$('#connectOverlay');if(o)o.classList.add('hidden');}

  function connect(){
    const key=($('#connectKey')?.value||'').trim();
    if(!key)return toast('Informe a chave de sincronização.');
    localStorage.setItem(KEY_STORE,key);sync();
  }

  function fillCompanySelect(){
    const sel=$('#globalCompany');if(!sel)return;
    const old=sel.value;
    sel.innerHTML='<option value="">Todas as empresas</option>'+data.app.companies.map(c=>`<option value="${esc(c.id)}">${esc(c.name)}</option>`).join('');
    if(data.app.companies.some(c=>c.id===old))sel.value=old;
  }

  function stockRows(){
    const keys=new Set(Object.keys(data.stock.minimums||{}));
    data.stock.movements.forEach(m=>keys.add(sk(m.companyId,m.epiId)));
    return [...keys].map(key=>{
      const parts=key.split('::');const companyId=parts.shift();const epiId=parts.join('::');const e=epi(epiId)||{id:epiId,name:'EPI não encontrado'};
      return {companyId,epiId,epi:e,company:company(companyId),saldo:balance(companyId,epiId),min:Number(data.stock.minimums[key]??5)};
    }).filter(r=>companyMatch(r.companyId));
  }

  function renderDashboard(){
    const deliveries=data.app.deliveries.filter(d=>companyMatch(d.companyId));
    const today=new Date().toISOString().slice(0,10);
    $('#mToday').textContent=deliveries.filter(d=>String(d.createdAt||'').slice(0,10)===today).length;
    $('#mWorkers').textContent=data.app.workers.filter(w=>w.active!==false&&companyMatch(w.companyId)).length;
    const epiUsed=new Set();stockRows().forEach(r=>epiUsed.add(r.epiId));
    $('#mEpis').textContent=selectedCompany()?epiUsed.size:data.app.epis.length;
    const low=stockRows().filter(r=>r.saldo<=r.min).sort((a,b)=>a.saldo-b.saldo);
    $('#mLow').textContent=low.length;
    $('#dashboardLow').innerHTML=low.length?table(['EPI','Empresa','Saldo','Mínimo','Situação'],low.slice(0,8).map(r=>[epiLabel(r.epi),esc(r.company?.name||'—'),String(r.saldo),String(r.min),statusHtml(r)])):'<div class="empty">Nenhum item com estoque baixo.</div>';
    const latest=deliveries.slice().sort((a,b)=>String(b.createdAt).localeCompare(String(a.createdAt))).slice(0,8);
    $('#dashboardDeliveries').innerHTML=latest.length?latest.map(d=>`<div class="list-item"><div><b>${esc(worker(d.workerId)?.name||'Colaborador')}</b><small>${esc(company(d.companyId)?.name||'—')} • ${fmt(d.createdAt)}</small></div><strong>${(d.items||[]).reduce((s,i)=>s+Number(i.qty||0),0)} item(ns)</strong></div>`).join(''):'<div class="empty">Sem entregas sincronizadas.</div>';
  }

  function renderStock(){
    const q=norm($('#stockSearch')?.value||'');
    const rows=stockRows().filter(r=>!q||[r.epi.name,r.epi.ca,r.epi.model,r.epi.size].some(v=>norm(v).includes(q))).sort((a,b)=>(a.saldo<=a.min?0:1)-(b.saldo<=b.min?0:1)||String(a.epi.name).localeCompare(String(b.epi.name)));
    const all=stockRows();
    $('#sItems').textContent=all.length;$('#sUnits').textContent=all.reduce((s,r)=>s+r.saldo,0);$('#sLow').textContent=all.filter(r=>r.saldo<=r.min).length;
    $('#stockTable').innerHTML=rows.length?table(['EPI','Empresa','CA','Tamanho','Saldo','Mín.','Situação',''],rows.map(r=>[esc(r.epi.name),esc(r.company?.name||'—'),esc(r.epi.ca||'—'),esc(r.epi.size||'—'),`<b>${r.saldo}</b>`,String(r.min),statusHtml(r),`<button class="link" data-adjust-stock="${esc(r.companyId)}|${esc(r.epiId)}">Ajustar</button>`])):'<div class="empty">Nenhum item de estoque encontrado.</div>';
  }

  function renderEpis(){
    const q=norm($('#epiSearch')?.value||'');
    const rows=data.app.epis.filter(e=>!q||[e.name,e.ca,e.model,e.size].some(v=>norm(v).includes(q))).sort((a,b)=>String(a.name).localeCompare(String(b.name)));
    $('#epiTable').innerHTML=rows.length?table(['EPI','CA','Modelo','Tamanho','Troca prevista'],rows.map(e=>[esc(e.name),esc(e.ca||'—'),esc(e.model||'—'),esc(e.size||'—'),e.cycle?`${Number(e.cycle)} dias`:'—'])):'<div class="empty">Nenhum EPI cadastrado.</div>';
  }

  function renderWorkers(){
    const q=norm($('#workerSearch')?.value||'');
    const rows=data.app.workers.filter(w=>companyMatch(w.companyId)&&w.active!==false&&(!q||[w.name,w.cpf,w.reg,w.role,w.sector].some(v=>norm(v).includes(q)))).sort((a,b)=>String(a.name).localeCompare(String(b.name)));
    $('#workerTable').innerHTML=rows.length?table(['Nome','Empresa','Matrícula','Cargo','Setor'],rows.map(w=>[esc(w.name),esc(company(w.companyId)?.name||'—'),esc(w.reg||'—'),esc(w.role||'—'),esc(w.sector||'—')])):'<div class="empty">Nenhum trabalhador encontrado.</div>';
  }

  function deliveryEpis(d){return (d.items||[]).map(i=>{const e=epi(i.epiId);return `${e?.name||'EPI'} (${i.qty||0})`;}).join(', ');}
  function renderDeliveries(){
    const q=norm($('#deliverySearch')?.value||'');
    const rows=data.app.deliveries.filter(d=>companyMatch(d.companyId)&&(!q||norm(worker(d.workerId)?.name).includes(q)||norm(deliveryEpis(d)).includes(q))).sort((a,b)=>String(b.createdAt).localeCompare(String(a.createdAt)));
    $('#deliveryCount').textContent=`${rows.length} registro(s)`;
    $('#deliveryTable').innerHTML=rows.length?table(['Data','Trabalhador','Empresa','EPIs','Motivo'],rows.map(d=>[fmt(d.createdAt),esc(worker(d.workerId)?.name||'—'),esc(company(d.companyId)?.name||'—'),esc(deliveryEpis(d)||'—'),esc(d.reason||'—')])):'<div class="empty">Nenhuma entrega encontrada.</div>';
  }

  function renderCompanies(){
    const rows=data.app.companies.slice().sort((a,b)=>String(a.name).localeCompare(String(b.name)));
    $('#companyTable').innerHTML=rows.length?table(['Empresa','CNPJ','Trabalhadores','Entregas'],rows.map(c=>[esc(c.name),esc(c.cnpj||'—'),String(data.app.workers.filter(w=>w.companyId===c.id&&w.active!==false).length),String(data.app.deliveries.filter(d=>d.companyId===c.id).length)])):'<div class="empty">Nenhuma empresa cadastrada.</div>';
  }

  function renderAll(){fillCompanySelect();renderDashboard();renderStock();renderEpis();renderWorkers();renderDeliveries();renderCompanies();}

  function table(headers,rows){return `<table class="data-table"><thead><tr>${headers.map(h=>`<th>${h}</th>`).join('')}</tr></thead><tbody>${rows.map(r=>`<tr>${r.map(v=>`<td>${v}</td>`).join('')}</tr>`).join('')}</tbody></table>`;}
  function epiLabel(e){return `${esc(e.name||'EPI')}<div class="muted">${e.ca?'CA '+esc(e.ca):''}${e.size?' • Tam. '+esc(e.size):''}</div>`;}
  function statusHtml(r){const cls=r.saldo<0?'negative':r.saldo<=r.min?'low':'ok';const txt=r.saldo<0?'NEGATIVO':r.saldo<=r.min?'BAIXO':'OK';return `<span class="status ${cls}">${txt}</span>`;}
  function fmt(iso){if(!iso)return '—';try{return new Intl.DateTimeFormat('pt-BR',{dateStyle:'short',timeStyle:'short'}).format(new Date(iso));}catch{return iso;}}

  function openView(id){
    $$('.view').forEach(v=>v.classList.toggle('active',v.id===id));
    $$('.nav').forEach(n=>n.classList.toggle('active',n.dataset.view===id));
    const titles={dashboard:['Visão geral','Acompanhe entregas e estoque do Auditar EPI.'],stock:['Estoque','Controle de saldo sincronizado com o campo.'],epis:['EPIs','Cadastros disponíveis em todos os aparelhos.'],workers:['Trabalhadores','Cadastro compartilhado entre Campo e Gestão.'],deliveries:['Entregas','Histórico recebido dos celulares.'],companies:['Empresas','Empresas atendidas pelo Auditar EPI.']};
    const t=titles[id]||titles.dashboard;$('#viewTitle').textContent=t[0];$('#viewSub').textContent=t[1];
  }

  function fieldsHtml(fields){return fields.map(f=>`<label class="${f.full?'full':''}">${f.label}${f.type==='select'?`<select id="df_${f.key}">${(f.options||[]).map(o=>`<option value="${esc(o.value)}">${esc(o.label)}</option>`).join('')}</select>`:`<input id="df_${f.key}" type="${f.type||'text'}" ${f.min!=null?`min="${f.min}"`:''} value="${esc(f.value??'')}" placeholder="${esc(f.placeholder||'')}">`}</label>`).join('');}
  function openDialog(title,sub,fields,onSave){
    $('#dialogTitle').textContent=title;$('#dialogSub').textContent=sub||'';$('#dialogFields').innerHTML=fieldsHtml(fields);dialogSaveHandler=onSave;$('#formDialog').showModal();setTimeout(()=>$('#dialogFields input,#dialogFields select')?.focus(),50);
  }

  function val(key){return ($('#df_'+key)?.value||'').trim();}

  function newCompany(){openDialog('Nova empresa','O cadastro aparecerá também no celular',[{key:'name',label:'Nome da empresa',full:true},{key:'cnpj',label:'CNPJ'}],async()=>{const name=val('name');if(!name)return toast('Informe o nome da empresa.');data.app.companies.push({id:uid('c'),name,cnpj:val('cnpj'),createdAt:now(),updatedAt:now()});await persistAndSync('Empresa cadastrada.');});}
  function newEpi(){openDialog('Novo EPI','Cadastre uma vez e use no Campo e no Estoque',[{key:'name',label:'EPI',full:true},{key:'ca',label:'CA'},{key:'model',label:'Fabricante / modelo'},{key:'size',label:'Tamanho / numeração'},{key:'cycle',label:'Troca prevista (dias)',type:'number',min:0}],async()=>{const name=val('name');if(!name)return toast('Informe o EPI.');data.app.epis.push({id:uid('e'),name,ca:val('ca'),model:val('model'),size:val('size'),cycle:Number(val('cycle')||0),createdAt:now(),updatedAt:now()});await persistAndSync('EPI cadastrado.');});}
  function newWorker(){
    if(!data.app.companies.length)return toast('Cadastre uma empresa primeiro.');
    openDialog('Novo trabalhador','Ficará disponível para entrega no celular',[{key:'companyId',label:'Empresa',type:'select',options:data.app.companies.map(c=>({value:c.id,label:c.name}))},{key:'name',label:'Nome completo',full:true},{key:'cpf',label:'CPF'},{key:'reg',label:'Matrícula'},{key:'role',label:'Cargo'},{key:'sector',label:'Setor'}],async()=>{const name=val('name');if(!name)return toast('Informe o nome.');data.app.workers.push({id:uid('w'),companyId:val('companyId'),name,cpf:val('cpf'),reg:val('reg'),role:val('role'),sector:val('sector'),active:true,createdAt:now(),updatedAt:now()});await persistAndSync('Trabalhador cadastrado.');});
  }
  function stockEntry(preset){
    if(!data.app.companies.length||!data.app.epis.length)return toast('Cadastre empresa e EPI primeiro.');
    const companyOptions=data.app.companies.map(c=>({value:c.id,label:c.name}));
    const epiOptions=data.app.epis.map(e=>({value:e.id,label:`${e.name}${e.size?' • '+e.size:''}${e.ca?' • CA '+e.ca:''}`}));
    openDialog(preset?'Ajustar estoque':'Nova movimentação','Entrada soma ao saldo. Ajuste define o saldo físico atual',[{key:'companyId',label:'Empresa',type:'select',options:companyOptions},{key:'epiId',label:'EPI',type:'select',options:epiOptions},{key:'operation',label:'Operação',type:'select',options:[{value:'IN',label:'Entrada de estoque'},{value:'SET',label:'Saldo inicial / ajuste'}]},{key:'qty',label:'Quantidade',type:'number',min:0},{key:'minimum',label:'Estoque mínimo',type:'number',min:0,value:'5'},{key:'note',label:'Observação',full:true,placeholder:'Ex.: Compra NF 1234'}],async()=>{
      const companyId=val('companyId'),epiId=val('epiId'),op=val('operation'),qty=Number(val('qty')||0),minimum=Math.max(0,Number(val('minimum')||0));
      if(!companyId||!epiId)return toast('Selecione empresa e EPI.');if(qty<0||!Number.isFinite(qty))return toast('Quantidade inválida.');if(op==='IN'&&qty<=0)return toast('Informe a quantidade recebida.');
      const current=balance(companyId,epiId);const delta=op==='SET'?qty-current:qty;data.stock.minimums[sk(companyId,epiId)]=minimum;data.stock.movements.unshift({id:uid('sm'),type:op,delta,companyId,epiId,note:val('note')||(op==='SET'?'Ajuste de saldo':'Entrada de estoque'),createdAt:now(),updatedAt:now()});await persistAndSync(op==='SET'?'Saldo ajustado.':'Entrada registrada.');
    });
    if(preset){setTimeout(()=>{$('#df_companyId').value=preset.companyId;$('#df_epiId').value=preset.epiId;$('#df_operation').value='SET';$('#df_qty').value=String(balance(preset.companyId,preset.epiId));$('#df_minimum').value=String(data.stock.minimums[sk(preset.companyId,preset.epiId)]??5);},0);}
  }

  async function persistAndSync(message){data.updatedAt=now();saveCache();renderAll();$('#formDialog').close();if(message)toast(message);await sync({silent:true});}

  function bind(){
    $('#btnConnect').addEventListener('click',connect);$('#connectKey').addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();connect();}});
    $('#btnRefresh').addEventListener('click',()=>sync());
    $('#globalCompany').addEventListener('change',renderAll);
    $$('.nav').forEach(n=>n.addEventListener('click',()=>openView(n.dataset.view)));
    document.addEventListener('click',e=>{const go=e.target.closest('[data-view]');if(go&&!go.classList.contains('nav'))openView(go.dataset.view);const a=e.target.closest('[data-adjust-stock]');if(a){const [companyId,epiId]=a.dataset.adjustStock.split('|');stockEntry({companyId,epiId});}});
    $('#stockSearch').addEventListener('input',renderStock);$('#epiSearch').addEventListener('input',renderEpis);$('#workerSearch').addEventListener('input',renderWorkers);$('#deliverySearch').addEventListener('input',renderDeliveries);
    $('#btnNewCompany').addEventListener('click',newCompany);$('#btnNewEpi').addEventListener('click',newEpi);$('#btnNewWorker').addEventListener('click',newWorker);$('#btnStockEntry').addEventListener('click',()=>stockEntry());
    $('#dynamicForm').addEventListener('submit',e=>{e.preventDefault();});
    $('#dialogSave').addEventListener('click',e=>{e.preventDefault();if(dialogSaveHandler)dialogSaveHandler();});
    window.addEventListener('online',()=>sync({silent:true}));window.addEventListener('offline',()=>setSync('error','Sem internet'));
  }

  document.addEventListener('DOMContentLoaded',()=>{
    data=loadCache();bind();renderAll();
    const key=(localStorage.getItem(KEY_STORE)||'').trim();
    if(key){hideConnect();sync({silent:true});}else showConnect();
    setInterval(()=>{if(!document.hidden&&navigator.onLine&&(localStorage.getItem(KEY_STORE)||'').trim())sync({silent:true});},20000);
  });
})();