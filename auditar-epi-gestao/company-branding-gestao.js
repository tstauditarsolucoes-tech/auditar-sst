(() => {
  const CACHE='auditarEpiGestaoCacheV1';
  const KEY='auditarEpiCentralKey';
  const DEVICE='auditarEpiGestaoDeviceId';
  const ENDPOINT='https://script.google.com/macros/s/AKfycbxqMnKiTlAJTFv3-odS2dB1NRcSD8wwvtNxxa-zCFhTM6GeNZszib_1N6eT9wSnOnOyjg/exec';
  const $=(s,r=document)=>r.querySelector(s);

  function toast(msg){const el=$('#toast');if(!el)return alert(msg);el.textContent=msg;el.classList.add('show');setTimeout(()=>el.classList.remove('show'),2800);}
  function blank(){return {version:1,revision:0,updatedAt:'',app:{companies:[],workers:[],epis:[],deliveries:[]},stock:{startedAt:'',processedDeliveryIds:[],movements:[],minimums:{}}};}
  function load(){try{const x=JSON.parse(localStorage.getItem(CACHE)||'{}');return {...blank(),...x,app:{...blank().app,...(x.app||{})},stock:{...blank().stock,...(x.stock||{})}};}catch{return blank();}}
  function save(x){localStorage.setItem(CACHE,JSON.stringify(x));}
  function deviceId(){let id=localStorage.getItem(DEVICE);if(!id){id=`gestao_logo_${Date.now()}_${Math.random().toString(36).slice(2,8)}`;localStorage.setItem(DEVICE,id);}return id;}

  function imageFromFile(file){return new Promise((resolve,reject)=>{const r=new FileReader();r.onload=()=>{const img=new Image();img.onload=()=>resolve(img);img.onerror=()=>reject(new Error('Não foi possível abrir a imagem.'));img.src=String(r.result||'');};r.onerror=()=>reject(new Error('Não foi possível ler a imagem.'));r.readAsDataURL(file);});}
  async function compactLogo(file){
    if(!file?.type?.startsWith('image/'))throw new Error('Selecione uma imagem válida.');if(file.size>8*1024*1024)throw new Error('Use uma logo com até 8 MB.');
    const img=await imageFromFile(file);const maxW=520,maxH=220;const scale=Math.min(1,maxW/img.naturalWidth,maxH/img.naturalHeight);const w=Math.max(1,Math.round(img.naturalWidth*scale)),h=Math.max(1,Math.round(img.naturalHeight*scale));
    const c=document.createElement('canvas');c.width=w;c.height=h;c.getContext('2d').drawImage(img,0,0,w,h);let out=c.toDataURL('image/webp',0.9);
    if(out.length>220000){const c2=document.createElement('canvas');const s=Math.min(1,360/w,150/h);c2.width=Math.max(1,Math.round(w*s));c2.height=Math.max(1,Math.round(h*s));c2.getContext('2d').drawImage(c,0,0,c2.width,c2.height);out=c2.toDataURL('image/webp',0.82);}return out;
  }

  function styles(){if($('#brandCompanyStyle'))return;const s=document.createElement('style');s.id='brandCompanyStyle';s.textContent=`
    .company-brand-panel{margin-bottom:16px}.company-brand-grid{display:grid;grid-template-columns:minmax(220px,1fr) 190px 1.4fr;gap:18px;align-items:center}.company-brand-preview{height:100px;border:1px dashed #b8ceca;border-radius:14px;background:#fff;display:flex;align-items:center;justify-content:center;overflow:hidden;color:#809591;font-size:12px;text-align:center;padding:8px}.company-brand-preview img{max-width:100%;max-height:100%;object-fit:contain}.company-brand-actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:9px}.company-brand-actions button{min-height:40px}.company-brand-help{font-size:12px;color:#657d79;line-height:1.5}.company-brand-help b{color:#284b47}.company-brand-saved{color:#16724d;font-weight:800;margin-top:6px;display:block}@media(max-width:900px){.company-brand-grid{grid-template-columns:1fr}.company-brand-preview{width:190px}}
  `;document.head.appendChild(s);}

  function inject(){
    const view=$('#companies');if(!view||$('#companyBrandPanel'))return;styles();const firstPanel=view.querySelector('.panel');const p=document.createElement('article');p.id='companyBrandPanel';p.className='panel company-brand-panel';p.innerHTML=`
      <div class="panel-head"><div><h2>🖼️ Logo da empresa</h2><p>Cadastre uma vez para usar automaticamente nos documentos.</p></div></div>
      <div class="company-brand-grid">
        <label>Empresa<select id="brandCompanySelect"></select></label>
        <div id="brandCompanyPreview" class="company-brand-preview">Selecione uma empresa</div>
        <div><div class="company-brand-help"><b>Onde será usada?</b><br>Ficha de EPI, comprovante de entrega, PDF e outros documentos emitidos para esta empresa.</div><div class="company-brand-actions"><button id="btnBrandChoose" class="primary" type="button">🖼️ Escolher / trocar logo</button><button id="btnBrandRemove" class="secondary" type="button">Remover logo</button><input id="brandCompanyFile" type="file" accept="image/png,image/jpeg,image/webp,image/*" hidden></div><small id="brandCompanySaved" class="company-brand-saved"></small></div>
      </div>`;
    view.insertBefore(p,firstPanel||null);
    $('#brandCompanySelect').addEventListener('change',renderPreview);$('#btnBrandChoose').addEventListener('click',()=>{if(!$('#brandCompanySelect').value)return toast('Selecione a empresa.');$('#brandCompanyFile').click();});$('#brandCompanyFile').addEventListener('change',onFile);$('#btnBrandRemove').addEventListener('click',removeLogo);
    $('#globalCompany')?.addEventListener('change',()=>{const id=$('#globalCompany').value;if(id&&[...$('#brandCompanySelect').options].some(o=>o.value===id)){$('#brandCompanySelect').value=id;renderPreview();}});
    refreshCompanies();
  }

  function refreshCompanies(){
    const sel=$('#brandCompanySelect');if(!sel)return;const root=load(),old=sel.value||$('#globalCompany')?.value||'';const rows=(root.app.companies||[]).slice().sort((a,b)=>String(a.name).localeCompare(String(b.name)));
    sel.innerHTML='<option value="">Selecione a empresa</option>'+rows.map(c=>`<option value="${String(c.id).replace(/"/g,'&quot;')}">${String(c.name||'Empresa').replace(/</g,'&lt;')}</option>`).join('');if(rows.some(c=>c.id===old))sel.value=old;renderPreview();
  }

  function renderPreview(){const id=$('#brandCompanySelect')?.value||'';const c=(load().app.companies||[]).find(x=>x.id===id);const prev=$('#brandCompanyPreview');if(!prev)return;prev.innerHTML=c?.logoDataUrl?`<img src="${c.logoDataUrl}" alt="Logo ${c.name||'empresa'}">`:(id?'Sem logo cadastrada':'Selecione uma empresa');$('#btnBrandRemove').disabled=!c?.logoDataUrl;$('#brandCompanySaved').textContent=c?.logoDataUrl?'✓ Logo cadastrada para esta empresa':'';}

  async function onFile(e){const file=e.target.files?.[0];if(!file)return;const id=$('#brandCompanySelect').value;if(!id)return toast('Selecione a empresa.');try{const logo=await compactLogo(file);await updateLogo(id,logo);toast('Logo salva e sincronizada.');}catch(err){toast(err.message||'Não foi possível salvar a logo.');}finally{e.target.value='';}}
  async function removeLogo(){const id=$('#brandCompanySelect')?.value;if(!id)return toast('Selecione a empresa.');const c=(load().app.companies||[]).find(x=>x.id===id);if(!c?.logoDataUrl)return;if(!confirm('Remover a logo desta empresa?'))return;await updateLogo(id,'');toast('Logo removida.');}

  async function updateLogo(id,logo){
    const root=load(),c=(root.app.companies||[]).find(x=>x.id===id);if(!c)throw new Error('Empresa não encontrada.');const at=new Date().toISOString();if(logo)c.logoDataUrl=logo;else delete c.logoDataUrl;if(logo)c.logoUpdatedAt=at;else delete c.logoUpdatedAt;c.updatedAt=at;root.updatedAt=at;save(root);renderPreview();
    const key=(localStorage.getItem(KEY)||'').trim();if(!key)return toast('Logo salva neste computador. Sincronize quando estiver conectado.');
    const res=await fetch(ENDPOINT,{method:'POST',headers:{'Content-Type':'text/plain;charset=utf-8'},body:JSON.stringify({action:'epi_sync_merge',syncKey:key,deviceId:deviceId(),client:'gestao-logo',payload:root})});const json=await res.json();if(!json?.ok)throw new Error(json?.message||'Falha na sincronização.');if(json.payload)save(json.payload);renderPreview();
  }

  function setup(){inject();setInterval(refreshCompanies,5000);window.GestaoEpiCompanyBranding={getLogo:(companyId)=>(load().app.companies||[]).find(c=>c.id===companyId)?.logoDataUrl||''};}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',setup);else setup();
})();
