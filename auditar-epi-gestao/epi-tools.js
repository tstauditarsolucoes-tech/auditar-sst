(() => {
  const CACHE='auditarEpiGestaoCacheV1';
  const CA_URL='https://caepi.trabalho.gov.br/internet/ConsultaCAInternet.aspx';
  const $=(s,r=document)=>r.querySelector(s);
  const esc=(v='')=>String(v??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
  const uid=p=>`${p}_${Date.now()}_${Math.random().toString(36).slice(2,9)}`;
  const now=()=>new Date().toISOString();

  function load(){
    try{return JSON.parse(localStorage.getItem(CACHE)||'{}');}
    catch{return {};}
  }
  function toast(msg){
    const el=$('#toast');if(!el)return;el.textContent=msg;el.classList.add('show');setTimeout(()=>el.classList.remove('show'),2400);
  }
  function onlyDigits(v){return String(v||'').replace(/\D/g,'');}
  function openCa(number){
    const ca=onlyDigits(number);
    const url=ca?`${CA_URL}?txtNumeroCA=${encodeURIComponent(ca)}`:CA_URL;
    window.open(url,'_blank');
  }
  function ensureStyles(){
    if($('#epiEasyStyles'))return;
    const style=document.createElement('style');style.id='epiEasyStyles';style.textContent=`
      .ca-box{background:#fff;border:1px solid var(--line);border-radius:var(--r);box-shadow:var(--shadow);padding:16px;margin-bottom:16px;display:flex;align-items:end;gap:12px;flex-wrap:wrap}
      .ca-box .ca-copy{flex:1;min-width:260px}.ca-box h3{margin:0 0 4px;font-size:16px}.ca-box p{margin:0;color:var(--muted);font-size:12px;line-height:1.4}.ca-search{display:flex;align-items:end;gap:8px;flex-wrap:wrap}.ca-search label{display:grid;gap:5px;font-size:11px;font-weight:850;color:var(--muted)}.ca-search input{width:170px}.ca-official{font-size:11px;color:var(--muted);width:100%;margin-top:5px}
      #quickEpiDialog .quick-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:16px}#quickEpiDialog label{display:grid;gap:6px;font-size:12px;font-weight:850;color:#526864}#quickEpiDialog .full{grid-column:1/-1}#quickEpiDialog details{grid-column:1/-1;border-top:1px solid var(--line);padding-top:10px}#quickEpiDialog summary{cursor:pointer;color:var(--brand);font-weight:850;font-size:12px}#quickEpiDialog .extra{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:10px}.ca-inline{display:flex;gap:7px}.ca-inline input{flex:1}.ca-inline button{white-space:nowrap}@media(max-width:720px){#quickEpiDialog .quick-grid,#quickEpiDialog .extra{grid-template-columns:1fr}#quickEpiDialog .full,#quickEpiDialog details{grid-column:auto}}
    `;document.head.appendChild(style);
  }
  function addCaPanel(){
    const section=$('#epis');if(!section||$('#caConsultPanel'))return;
    const panel=document.createElement('div');panel.id='caConsultPanel';panel.className='ca-box';
    panel.innerHTML=`<div class="ca-copy"><h3>🔎 Consultar CA</h3><p>Digite o número e abra a consulta oficial do Ministério do Trabalho.</p></div><div class="ca-search"><label>Número do CA<input id="caQuickNumber" inputmode="numeric" placeholder="Ex.: 12345"></label><button id="btnCaQuick" class="primary">Consultar CA</button><button id="btnCaFull" class="secondary">Consulta completa</button></div><div class="ca-official">A consulta abre no site oficial do MTE.</div>`;
    const head=section.querySelector('.split-head');if(head)head.insertAdjacentElement('afterend',panel);else section.prepend(panel);
    $('#btnCaQuick')?.addEventListener('click',()=>{const v=$('#caQuickNumber')?.value||'';if(!onlyDigits(v))return toast('Digite o número do CA.');openCa(v);});
    $('#btnCaFull')?.addEventListener('click',()=>openCa(''));
    $('#caQuickNumber')?.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();$('#btnCaQuick')?.click();}});
  }
  function addDialog(){
    if($('#quickEpiDialog'))return;
    const dialog=document.createElement('dialog');dialog.id='quickEpiDialog';
    dialog.innerHTML=`<form method="dialog" id="quickEpiForm"><div class="dialog-head"><div><h2>Cadastrar EPI</h2><p>Preencha só o necessário. Os outros campos são opcionais.</p></div><button value="cancel" class="x">×</button></div><div class="quick-grid"><label class="full">Nome do EPI<input id="qeName" placeholder="Ex.: Luva de proteção" required></label><label>CA<div class="ca-inline"><input id="qeCa" inputmode="numeric" placeholder="Número do CA"><button id="qeConsult" type="button" class="secondary">Consultar</button></div></label><label>Tamanho / numeração<input id="qeSize" placeholder="Ex.: M, G, 42"></label><label>Troca prevista (dias)<input id="qeCycle" type="number" min="0" placeholder="Opcional"></label><details><summary>＋ Mais informações (opcional)</summary><div class="extra"><label>Fabricante / modelo<input id="qeModel" placeholder="Opcional"></label></div></details></div><div class="dialog-actions"><button value="cancel" class="secondary">Cancelar</button><button id="qeSave" type="button" class="primary">Salvar EPI</button></div></form>`;
    document.body.appendChild(dialog);
    $('#qeConsult')?.addEventListener('click',()=>{const v=$('#qeCa')?.value||'';if(!onlyDigits(v))return toast('Digite o número do CA.');openCa(v);});
    $('#qeSave')?.addEventListener('click',saveEpi);
  }
  function saveEpi(){
    const name=String($('#qeName')?.value||'').trim();if(!name)return toast('Informe o nome do EPI.');
    const root=load();root.app=root.app&&typeof root.app==='object'?root.app:{};root.app.epis=Array.isArray(root.app.epis)?root.app.epis:[];
    const ca=onlyDigits($('#qeCa')?.value||'');
    const same=root.app.epis.some(e=>String(e.name||'').trim().toLowerCase()===name.toLowerCase()&&String(e.ca||'')===ca&&String(e.size||'').trim().toLowerCase()===String($('#qeSize')?.value||'').trim().toLowerCase());
    if(same)return toast('Esse EPI já está cadastrado.');
    root.app.epis.push({id:uid('e'),name,ca,model:String($('#qeModel')?.value||'').trim(),size:String($('#qeSize')?.value||'').trim(),cycle:Math.max(0,Number($('#qeCycle')?.value||0)),createdAt:now(),updatedAt:now()});
    root.updatedAt=now();localStorage.setItem(CACHE,JSON.stringify(root));toast('EPI cadastrado.');$('#quickEpiDialog')?.close();setTimeout(()=>location.reload(),450);
  }
  function replaceEpiButton(){
    const old=$('#btnNewEpi');if(!old||old.dataset.easy==='1')return;
    const btn=old.cloneNode(true);btn.dataset.easy='1';btn.textContent='＋ Cadastrar EPI';old.replaceWith(btn);btn.addEventListener('click',()=>{addDialog();$('#quickEpiDialog').showModal();setTimeout(()=>$('#qeName')?.focus(),50);});
  }
  function init(){ensureStyles();replaceEpiButton();addCaPanel();addDialog();}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();