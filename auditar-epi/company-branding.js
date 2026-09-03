(() => {
  const APP_KEY='auditarEpiV1';
  const $=(s,r=document)=>r.querySelector(s);
  let pendingNewLogo='';
  let editCompanyId='';

  function toast(msg){const el=$('#toast');if(!el)return alert(msg);el.textContent=msg;el.classList.add('show');setTimeout(()=>el.classList.remove('show'),2600);}
  function load(){try{return {companies:[],workers:[],epis:[],deliveries:[],...JSON.parse(localStorage.getItem(APP_KEY)||'{}')};}catch{return {companies:[],workers:[],epis:[],deliveries:[]};}}
  function save(root){localStorage.setItem(APP_KEY,JSON.stringify(root));document.dispatchEvent(new CustomEvent('auditar-epi-data-changed'));}

  function imageFromFile(file){return new Promise((resolve,reject)=>{const r=new FileReader();r.onload=()=>{const img=new Image();img.onload=()=>resolve(img);img.onerror=()=>reject(new Error('Não foi possível abrir a imagem.'));img.src=String(r.result||'');};r.onerror=()=>reject(new Error('Não foi possível ler a imagem.'));r.readAsDataURL(file);});}
  async function compactLogo(file){
    if(!file?.type?.startsWith('image/'))throw new Error('Selecione uma imagem válida.');
    if(file.size>8*1024*1024)throw new Error('A imagem é muito grande. Use uma logo com até 8 MB.');
    const img=await imageFromFile(file);const maxW=520,maxH=220;const scale=Math.min(1,maxW/img.naturalWidth,maxH/img.naturalHeight);
    const w=Math.max(1,Math.round(img.naturalWidth*scale)),h=Math.max(1,Math.round(img.naturalHeight*scale));
    const c=document.createElement('canvas');c.width=w;c.height=h;const ctx=c.getContext('2d');ctx.clearRect(0,0,w,h);ctx.drawImage(img,0,0,w,h);
    let out=c.toDataURL('image/webp',0.9);
    if(out.length>220000){const c2=document.createElement('canvas');const s=Math.min(1,360/w,150/h);c2.width=Math.max(1,Math.round(w*s));c2.height=Math.max(1,Math.round(h*s));c2.getContext('2d').drawImage(c,0,0,c2.width,c2.height);out=c2.toDataURL('image/webp',0.82);}
    return out;
  }

  function styles(){
    if($('#companyBrandStyle'))return;const s=document.createElement('style');s.id='companyBrandStyle';s.textContent=`
      .company-logo-field{grid-column:1/-1;border:1px solid #d8e6e4;background:#f8fbfb;border-radius:14px;padding:12px;display:grid;gap:9px}
      .company-logo-field b{font-size:13px}.company-logo-field small{color:#687f7b;line-height:1.35}
      .company-logo-row{display:flex;align-items:center;gap:12px;flex-wrap:wrap}.company-logo-preview{width:110px;height:64px;border:1px dashed #9db7b3;border-radius:11px;background:#fff;display:flex;align-items:center;justify-content:center;overflow:hidden;color:#76908c;font-size:11px;text-align:center;padding:4px}.company-logo-preview img{max-width:100%;max-height:100%;object-fit:contain}
      .company-logo-btn{border:1px solid #bdd4d0;background:#fff;color:#0f766e;border-radius:11px;min-height:42px;padding:0 14px;font-weight:850}
      .company-logo-thumb{width:48px;height:38px;border:1px solid #d9e5e3;border-radius:8px;background:#fff;display:flex;align-items:center;justify-content:center;overflow:hidden;flex:0 0 auto}.company-logo-thumb img{max-width:100%;max-height:100%;object-fit:contain}.company-logo-thumb span{font-size:9px;color:#8aa09d}
      .company-logo-remove{color:#a23a32!important}
      .receipt-company-logo{text-align:center;margin:0 0 12px}.receipt-company-logo img{max-width:180px;max-height:82px;object-fit:contain}
      @media print{.receipt-company-logo img{max-width:170px;max-height:72px}}
    `;document.head.appendChild(s);
  }

  function preview(el,data){if(!el)return;el.innerHTML=data?`<img src="${data}" alt="Logo da empresa">`:'<span>Sem logo</span>';}

  function setupNewCompany(){
    const form=$('#companyForm');if(!form||$('#companyLogoInput'))return;
    const saveBtn=form.querySelector('button[type="submit"]');const box=document.createElement('div');box.className='company-logo-field';box.innerHTML=`<b>Logo da empresa</b><small>Opcional. Ela aparecerá nas fichas, comprovantes e PDFs desta empresa.</small><div class="company-logo-row"><div id="companyLogoPreview" class="company-logo-preview"><span>Sem logo</span></div><button id="btnChooseCompanyLogo" class="company-logo-btn" type="button">🖼️ Escolher logo</button><input id="companyLogoInput" type="file" accept="image/png,image/jpeg,image/webp,image/*" hidden></div>`;
    form.insertBefore(box,saveBtn);
    $('#btnChooseCompanyLogo').addEventListener('click',()=>$('#companyLogoInput').click());
    $('#companyLogoInput').addEventListener('change',async e=>{const file=e.target.files?.[0];if(!file)return;try{pendingNewLogo=await compactLogo(file);preview($('#companyLogoPreview'),pendingNewLogo);toast('Logo pronta para salvar.');}catch(err){toast(err.message||'Não foi possível preparar a logo.');}});
    form.addEventListener('submit',()=>{
      const logo=pendingNewLogo;const name=$('#companyName')?.value?.trim()||'';if(!logo||!name)return;
      setTimeout(()=>{const root=load();const matches=(root.companies||[]).filter(c=>c.name===name).sort((a,b)=>String(b.createdAt||'').localeCompare(String(a.createdAt||'')));const c=matches[0];if(!c)return;c.logoDataUrl=logo;c.logoUpdatedAt=new Date().toISOString();c.updatedAt=c.logoUpdatedAt;save(root);pendingNewLogo='';preview($('#companyLogoPreview'),'');decorateCompanies();toast('Empresa salva com a logo.');},80);
    },true);
  }

  function setupEditInput(){
    if($('#companyLogoEditInput'))return;const input=document.createElement('input');input.id='companyLogoEditInput';input.type='file';input.accept='image/png,image/jpeg,image/webp,image/*';input.hidden=true;document.body.appendChild(input);
    input.addEventListener('change',async()=>{const file=input.files?.[0];if(!file||!editCompanyId)return;try{const logo=await compactLogo(file);const root=load();const c=(root.companies||[]).find(x=>x.id===editCompanyId);if(!c)return;c.logoDataUrl=logo;c.logoUpdatedAt=new Date().toISOString();c.updatedAt=c.logoUpdatedAt;save(root);decorateCompanies();patchReceipt();toast('Logo da empresa atualizada.');}catch(err){toast(err.message||'Não foi possível salvar a logo.');}finally{input.value='';editCompanyId='';}});
  }

  function decorateCompanies(){
    const list=$('#companyList');if(!list)return;const root=load();
    list.querySelectorAll('.list-item').forEach(item=>{
      const del=item.querySelector('[data-del-company]');const id=del?.dataset.delCompany;if(!id)return;const c=(root.companies||[]).find(x=>x.id===id);if(!c)return;
      let thumb=item.querySelector('.company-logo-thumb');if(!thumb){thumb=document.createElement('div');thumb.className='company-logo-thumb';item.insertBefore(thumb,item.firstChild);}thumb.innerHTML=c.logoDataUrl?`<img src="${c.logoDataUrl}" alt="Logo ${c.name||''}">`:'<span>SEM<br>LOGO</span>';
      const actions=item.querySelector('.list-actions')||item;if(!actions.querySelector('[data-company-logo]')){const b=document.createElement('button');b.type='button';b.className='tiny';b.dataset.companyLogo=id;b.textContent=c.logoDataUrl?'Trocar logo':'Adicionar logo';actions.insertBefore(b,del||null);}
      const b=actions.querySelector('[data-company-logo]');if(b)b.textContent=c.logoDataUrl?'Trocar logo':'Adicionar logo';
      let rem=actions.querySelector('[data-company-logo-remove]');if(c.logoDataUrl&&!rem){rem=document.createElement('button');rem.type='button';rem.className='tiny company-logo-remove';rem.dataset.companyLogoRemove=id;rem.textContent='Remover logo';actions.insertBefore(rem,del||null);}else if(!c.logoDataUrl&&rem)rem.remove();
    });
  }

  function patchReceipt(){
    const content=$('#receiptContent');if(!content||!content.children.length||content.querySelector('.receipt-company-logo'))return;
    const meta=content.querySelector('.receipt-meta > div');const text=meta?.textContent||'';const root=load();const c=(root.companies||[]).find(x=>cMatch(x,text));if(!c?.logoDataUrl)return;
    const wrap=document.createElement('div');wrap.className='receipt-company-logo';wrap.innerHTML=`<img src="${c.logoDataUrl}" alt="Logo ${c.name||'empresa'}">`;content.insertBefore(wrap,content.firstChild);
  }
  function cMatch(c,text){return !!c?.name&&text.includes(c.name)&&(!c.cnpj||text.includes(c.cnpj));}

  function bind(){
    setupNewCompany();setupEditInput();decorateCompanies();patchReceipt();
    const list=$('#companyList');if(list)new MutationObserver(decorateCompanies).observe(list,{childList:true,subtree:true});
    const receipt=$('#receiptContent');if(receipt)new MutationObserver(()=>setTimeout(patchReceipt,0)).observe(receipt,{childList:true,subtree:true});
    document.addEventListener('click',e=>{const b=e.target.closest('[data-company-logo]');if(b){editCompanyId=b.dataset.companyLogo;$('#companyLogoEditInput').click();return;}const r=e.target.closest('[data-company-logo-remove]');if(r){const root=load();const c=(root.companies||[]).find(x=>x.id===r.dataset.companyLogoRemove);if(!c)return;if(!confirm('Remover a logo desta empresa?'))return;delete c.logoDataUrl;delete c.logoUpdatedAt;c.updatedAt=new Date().toISOString();save(root);decorateCompanies();toast('Logo removida.');}});
    window.GestaoEpiCompanyBranding={getLogo:(companyId)=>(load().companies||[]).find(c=>c.id===companyId)?.logoDataUrl||''};
  }

  styles();if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',bind);else bind();
})();
