(()=>{
  const CACHE='auditarEpiGestaoCacheV1';
  const $=(s,r=document)=>r.querySelector(s),$$=(s,r=document)=>[...r.querySelectorAll(s)];
  const esc=(v='')=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const norm=(v='')=>String(v??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim();
  function read(){try{const r=JSON.parse(localStorage.getItem(CACHE)||'{}');r.app=r.app&&typeof r.app==='object'?r.app:{};for(const k of ['companies','workers','deliveries'])r.app[k]=Array.isArray(r.app[k])?r.app[k]:[];return r}catch{return{app:{companies:[],workers:[],deliveries:[]}}}}
  function external(w){return w?.workerType==='external'||w?.employmentType==='external'}
  function company(id,r){return r.app.companies.find(c=>c.id===id)||{}}
  function fmt(x){if(!x)return'—';try{return new Intl.DateTimeFormat('pt-BR',{dateStyle:'short'}).format(new Date(x))}catch{return String(x)}}

  function cleanBlinkText(root=document.body){
    if(!root)return;
    const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);let n;
    while((n=walker.nextNode())){
      const old=n.nodeValue||'';
      let next=old
        .replace(/\s*e não foi exigido piscar\.?/gi,'.')
        .replace(/\s*sem exigência de piscar\.?/gi,'')
        .replace(/\s*não foi exigido piscar\.?/gi,'');
      next=next.replace(/\.\./g,'.').replace(/\s+\./g,'.');
      if(next!==old)n.nodeValue=next;
    }
  }

  function styles(){if($('#v272FichaStyles'))return;const s=document.createElement('style');s.id='v272FichaStyles';s.textContent=`
    .v272-view{display:none}.v272-view.active{display:block}.v272-head{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:14px}.v272-head h2{margin:0;color:#173d39;font-size:19px}.v272-head p{margin:4px 0 0;color:#6d827e;font-size:11px}.v272-card{background:#fff;border:1px solid #dbe8e5;border-radius:16px;padding:15px}.v272-filters{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px}.v272-filters label{display:grid;gap:5px;font-size:10px;font-weight:850;color:#526d68}.v272-filters input,.v272-filters select{width:100%;box-sizing:border-box;border:1px solid #cbded9;border-radius:10px;padding:10px;background:#fff}.v272-table{width:100%;border-collapse:collapse;font-size:10px}.v272-table th,.v272-table td{padding:9px;border-bottom:1px solid #e4eeec;text-align:left;vertical-align:middle}.v272-table th{background:#f4f8f7;color:#536d68;font-size:9px;text-transform:uppercase}.v272-open{border:0;border-radius:9px;background:#0f766e;color:#fff;padding:8px 10px;font-size:10px;font-weight:900;cursor:pointer}.v272-empty{padding:22px;text-align:center;color:#70847f;border:1px dashed #cbded9;border-radius:12px}.v272-quick{margin-left:8px}@media(max-width:800px){.v272-filters{grid-template-columns:1fr}.v272-table{font-size:9px}}
  `;document.head.appendChild(s)}

  function openView(){
    $$('.view').forEach(v=>v.classList.toggle('active',v.id==='employeeSheetsPc'));
    $$('.nav').forEach(n=>n.classList.toggle('active',n.dataset.view==='employeeSheetsPc'));
    if($('#viewTitle'))$('#viewTitle').textContent='Fichas de EPI';
    if($('#viewSub'))$('#viewSub').textContent='Encontre rapidamente a ficha individual de qualquer funcionário.';
    render();$('.main')?.scrollTo({top:0,behavior:'smooth'});
  }

  function ensure(){
    const main=$('.main'),nav=$('.sidebar nav');if(!main||!nav)return false;
    if(!$('#employeeSheetsPc')){
      const sec=document.createElement('section');sec.id='employeeSheetsPc';sec.className='view v272-view';sec.innerHTML=`<div class="v272-head"><div><h2>📄 Fichas de EPI dos funcionários</h2><p>Consulte o histórico completo e salve a ficha em PDF.</p></div></div><div class="v272-card"><div class="v272-filters"><label>Empresa<select id="v272FichaCompany"><option value="">Todas as empresas</option></select></label><label>Buscar funcionário<input id="v272FichaSearch" placeholder="Nome, CPF, matrícula, cargo ou setor"></label></div><div id="v272FichaList"></div></div>`;main.appendChild(sec);
      $('#v272FichaCompany').onchange=render;$('#v272FichaSearch').oninput=render;
    }
    if(!nav.querySelector('[data-view="employeeSheetsPc"]')){
      const b=document.createElement('button');b.className='nav pc-new';b.dataset.view='employeeSheetsPc';b.innerHTML='📄 <span>Fichas de EPI</span>';const ref=nav.querySelector('[data-view="deliveries"]');ref?nav.insertBefore(b,ref):nav.appendChild(b);b.onclick=openView;
    }
    const head=$('#workers .split-head');
    if(head&&!$('#v272FichaQuick')){
      const b=document.createElement('button');b.id='v272FichaQuick';b.type='button';b.className='secondary v272-quick';b.textContent='📄 Fichas de EPI';b.onclick=openView;head.appendChild(b);
    }
    return true;
  }

  function fillCompanies(r){const s=$('#v272FichaCompany');if(!s)return;const old=s.value;const rows=r.app.companies.slice().sort((a,b)=>String(a.name||'').localeCompare(String(b.name||'')));s.innerHTML='<option value="">Todas as empresas</option>'+rows.map(c=>`<option value="${esc(c.id)}">${esc(c.name||'Empresa')}</option>`).join('');if(rows.some(c=>c.id===old))s.value=old}

  function render(){const r=read();fillCompanies(r);const c=$('#v272FichaCompany')?.value||'',q=norm($('#v272FichaSearch')?.value||'');const list=r.app.workers.filter(w=>!external(w)&&(!c||w.companyId===c)&&(!q||[w.name,w.cpf,w.reg,w.role,w.sector].some(v=>norm(v).includes(q)))).sort((a,b)=>String(a.name||'').localeCompare(String(b.name||'')));const box=$('#v272FichaList');if(!box)return;box.innerHTML=list.length?`<table class="v272-table"><thead><tr><th>Funcionário</th><th>Empresa</th><th>Cargo / setor</th><th>Situação</th><th>Última entrega</th><th></th></tr></thead><tbody>${list.map(w=>{const ds=r.app.deliveries.filter(d=>d.workerId===w.id&&!d.cancelled).sort((a,b)=>String(b.createdAt||'').localeCompare(String(a.createdAt||'')));return`<tr><td><b>${esc(w.name||'—')}</b><br><small>${esc(w.cpf||w.reg||'')}</small></td><td>${esc(company(w.companyId,r).name||'—')}</td><td>${esc(w.role||'—')}${w.sector?`<br><small>${esc(w.sector)}</small>`:''}</td><td>${w.active===false?'Desligado / inativo':'Ativo'}</td><td>${ds[0]?fmt(ds[0].createdAt):'Sem entrega'}</td><td><button type="button" class="v272-open" data-worker-sheet="${esc(w.id)}">Abrir ficha</button></td></tr>`}).join('')}</tbody></table>`:'<div class="v272-empty">Nenhum funcionário encontrado.</div>'}

  function boot(){styles();let tries=0;const t=setInterval(()=>{tries++;if(ensure()||tries>100){clearInterval(t);render()}},100);const obs=new MutationObserver(()=>cleanBlinkText(document.body));obs.observe(document.body,{childList:true,subtree:true,characterData:true});cleanBlinkText(document.body);document.addEventListener('click',e=>{if(e.target.closest('[data-pc-receipt],#workerSheetPrint,[data-worker-sheet]'))setTimeout(()=>cleanBlinkText(document.body),150)},true);window.addEventListener('storage',e=>{if(e.key===CACHE&&$('#employeeSheetsPc')?.classList.contains('active'))render()})}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
