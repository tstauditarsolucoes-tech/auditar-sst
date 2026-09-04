(() => {
  const CA_URL='https://caepi.trabalho.gov.br/internet/ConsultaCAInternet.aspx';
  const $=(s,r=document)=>r.querySelector(s);
  let selectedFile=null,previewUrl='';

  function toast(msg){const el=$('#toast');if(!el)return alert(msg);el.textContent=msg;el.classList.add('show');setTimeout(()=>el.classList.remove('show'),2600);}
  const digits=v=>String(v||'').replace(/\D/g,'');
  const clean=v=>String(v||'').replace(/\s+/g,' ').trim();
  const norm=v=>clean(v).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toUpperCase();

  function injectStyles(){
    if($('#epiPhotoCaStyle'))return;
    const s=document.createElement('style');s.id='epiPhotoCaStyle';s.textContent=`
      .epi-photo-ca{border:1px solid #cfe4e0;background:linear-gradient(180deg,#f7fcfb,#eef9f6);border-radius:18px;padding:15px;margin-bottom:14px;box-shadow:0 8px 24px rgba(15,168,142,.08)}
      .epi-photo-ca h3{margin:0 0 4px;font-size:17px}.epi-photo-ca p{margin:0;color:#617b77;font-size:12px;line-height:1.45}
      .epi-photo-actions{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:12px}.epi-photo-actions button{min-height:48px}
      .epi-photo-input{display:none}.epi-photo-preview{display:none;margin-top:10px;border:1px solid #d8e7e4;border-radius:14px;overflow:hidden;background:#fff}.epi-photo-preview.show{display:block}
      .epi-photo-preview img{display:block;width:100%;max-height:250px;object-fit:contain;background:#f3f7f6}.epi-photo-status{padding:9px 11px;font-size:12px;font-weight:800;color:#355b57}.epi-photo-status.error{color:#b42318}
      .epi-photo-result{display:none;margin-top:10px;padding:10px;border-radius:12px;background:#fff;border:1px solid #d7e7e4;font-size:12px;line-height:1.5}.epi-photo-result.show{display:block}.epi-photo-result b{color:#173d39}
      @media(max-width:520px){.epi-photo-actions{grid-template-columns:1fr}.epi-photo-ca{padding:13px}}
    `;document.head.appendChild(s);
  }

  function injectUi(){
    const section=$('#epis'),form=$('#epiForm');if(!section||!form||$('#epiPhotoCaBox'))return;
    injectStyles();
    const box=document.createElement('div');box.id='epiPhotoCaBox';box.className='epi-photo-ca';box.innerHTML=`
      <h3>📷 Cadastrar EPI por foto do CA</h3>
      <p>Tire uma foto da etiqueta ou gravação do EPI. O app lê o CA e tenta preencher nome, fabricante/modelo e tamanho. Confira antes de salvar.</p>
      <input id="epiCaPhotoInput" class="epi-photo-input" type="file" accept="image/*" capture="environment">
      <div class="epi-photo-actions">
        <button id="btnEpiCaPhoto" type="button" class="primary">📷 Tirar foto do CA</button>
        <button id="btnEpiCaRead" type="button" class="secondary" disabled>✨ Ler foto e preencher</button>
      </div>
      <div id="epiCaPreview" class="epi-photo-preview"><img id="epiCaPreviewImg" alt="Foto do CA"><div id="epiCaPhotoStatus" class="epi-photo-status">Aguardando foto.</div></div>
      <div id="epiCaPhotoResult" class="epi-photo-result"></div>`;
    form.parentNode.insertBefore(box,form);
    $('#btnEpiCaPhoto').onclick=()=>$('#epiCaPhotoInput').click();
    $('#btnEpiCaRead').onclick=readPhoto;
    $('#epiCaPhotoInput').onchange=e=>selectPhoto(e.target.files?.[0]||null);
    enforceRole();
  }

  function enforceRole(){const box=$('#epiPhotoCaBox');if(!box)return;const role=document.body.dataset.epiRole||'';box.style.display=role&&role!=='admin'?'none':'';}

  function selectPhoto(file){
    selectedFile=file;if(previewUrl){URL.revokeObjectURL(previewUrl);previewUrl='';}
    const preview=$('#epiCaPreview'),btn=$('#btnEpiCaRead');
    if(!file){preview?.classList.remove('show');if(btn)btn.disabled=true;return;}
    if(!file.type.startsWith('image/')){toast('Selecione uma foto válida.');return;}
    previewUrl=URL.createObjectURL(file);$('#epiCaPreviewImg').src=previewUrl;preview.classList.add('show');btn.disabled=false;setStatus('Foto pronta. Toque em “Ler foto e preencher”.');$('#epiCaPhotoResult').classList.remove('show');
  }

  function setStatus(text,error=false){const el=$('#epiCaPhotoStatus');if(!el)return;el.textContent=text;el.classList.toggle('error',error);}

  function loadTesseract(){
    if(window.Tesseract)return Promise.resolve();
    return new Promise((resolve,reject)=>{
      const old=$('script[data-tesseract-ca]');if(old){old.addEventListener('load',resolve,{once:true});old.addEventListener('error',()=>reject(new Error('Falha ao carregar leitor de imagem.')),{once:true});return;}
      const s=document.createElement('script');s.src='https://cdn.jsdelivr.net/npm/tesseract.js@5/dist/tesseract.min.js';s.dataset.tesseractCa='1';s.onload=resolve;s.onerror=()=>reject(new Error('Falha ao carregar leitor de imagem. Verifique a internet.'));document.head.appendChild(s);
    });
  }

  async function prepareImage(file){
    const url=URL.createObjectURL(file);try{
      const img=await new Promise((resolve,reject)=>{const i=new Image();i.onload=()=>resolve(i);i.onerror=reject;i.src=url;});
      const max=1800,scale=Math.min(1.7,max/Math.max(img.naturalWidth,img.naturalHeight));
      const w=Math.max(1,Math.round(img.naturalWidth*scale)),h=Math.max(1,Math.round(img.naturalHeight*scale));
      const c=document.createElement('canvas');c.width=w;c.height=h;const x=c.getContext('2d',{willReadFrequently:true});x.fillStyle='#fff';x.fillRect(0,0,w,h);x.drawImage(img,0,0,w,h);
      const data=x.getImageData(0,0,w,h),p=data.data;
      for(let i=0;i<p.length;i+=4){const g=.299*p[i]+.587*p[i+1]+.114*p[i+2];const v=Math.max(0,Math.min(255,(g-128)*1.28+128));p[i]=p[i+1]=p[i+2]=v;}
      x.putImageData(data,0,0);return c;
    }finally{URL.revokeObjectURL(url);}
  }

  function parseText(text){
    const raw=String(text||''),flat=norm(raw),lines=raw.split(/\r?\n/).map(clean).filter(Boolean);
    let ca='';
    const caPatterns=[/(?:^|\b)C\.?\s*A\.?\s*(?:N[º°O.]*)?\s*[:#\-]?\s*(\d{3,7})\b/i,/CERTIFICADO\s+DE\s+APROVA(?:C|Ç)(?:A|Ã)O[^\d]{0,30}(\d{3,7})/i];
    for(const r of caPatterns){const m=flat.match(r);if(m){ca=m[1];break;}}
    if(!ca){const nums=(flat.match(/\b\d{4,7}\b/g)||[]).filter(n=>!(Number(n)>=1900&&Number(n)<=2100));if(nums.length)ca=nums.sort((a,b)=>b.length-a.length)[0];}

    const keywords=['CAPACETE','OCULOS','ÓCULOS','LUVA','RESPIRADOR','PROTETOR','BOTINA','CALCADO','CALÇADO','CINTURAO','CINTURÃO','MASCARA','MÁSCARA','VESTIMENTA','AVENTAL','ABAFADOR','VISEIRA','CREME','MANGOTE','PERNEIRA','COLETE'];
    const bad=['CNPJ','LOTE','VALIDADE','DATA','CERTIFICADO','APROVACAO','APROVAÇÃO','MINISTERIO','TRABALHO'];
    let name='';
    for(const line of lines){const n=norm(line);if(n.length<4||n.length>100||bad.some(x=>n.includes(x)))continue;if(keywords.some(k=>n.includes(norm(k)))){name=clean(line.replace(/^(EPI|PRODUTO|DESCRI[CÇ][AÃ]O)\s*[:\-]?\s*/i,''));break;}}
    if(!name){const l=lines.find(line=>/^(?:produto|descri[cç][aã]o)\s*[:\-]/i.test(line));if(l)name=clean(l.replace(/^[^:\-]+[:\-]\s*/,''));}

    let manufacturer='',model='';
    for(const line of lines){
      let m=line.match(/(?:FABRICANTE|MARCA)\s*[:\-]\s*(.+)/i);if(m&&!manufacturer)manufacturer=clean(m[1]);
      m=line.match(/(?:MODELO|REF(?:ER[EÊ]NCIA)?\.?|REFERENCIA)\s*[:#\-]?\s*(.+)/i);if(m&&!model)model=clean(m[1]);
    }
    let size='';const sizeMatch=flat.match(/(?:TAM(?:ANHO)?|SIZE|NUMERA[CÇ][AÃ]O)\s*[:#\-]?\s*([A-Z0-9]{1,4}(?:\/[A-Z0-9]{1,4})?)/i);if(sizeMatch)size=sizeMatch[1];
    const combined=[manufacturer,model].filter(Boolean).join(' • ');
    return {ca,name,model:combined,size,raw};
  }

  function applyResult(r){
    if(r.ca)$('#epiCa').value=r.ca;
    if(r.name)$('#epiName').value=r.name;
    if(r.model)$('#epiModel').value=r.model;
    if(r.size)$('#epiSize').value=r.size;
    const out=$('#epiCaPhotoResult');out.innerHTML=`<b>Leitura concluída</b><br>CA: ${r.ca||'não identificado'}<br>EPI: ${r.name||'revisar manualmente'}${r.model?`<br>Fabricante/modelo: ${r.model}`:''}${r.size?`<br>Tamanho: ${r.size}`:''}${r.ca?`<br><button id="btnCheckPhotoCa" type="button" class="secondary" style="margin-top:8px">🔎 Conferir CA no MTE</button>`:''}`;out.classList.add('show');
    $('#btnCheckPhotoCa')?.addEventListener('click',()=>window.open(`${CA_URL}?txtNumeroCA=${encodeURIComponent(r.ca)}`,'_blank'));
    $('#epiForm').scrollIntoView({behavior:'smooth',block:'start'});
  }

  async function readPhoto(){
    if(!selectedFile)return toast('Tire ou selecione uma foto primeiro.');
    const btn=$('#btnEpiCaRead');btn.disabled=true;btn.textContent='⏳ Lendo foto…';setStatus('Preparando a foto…');
    try{
      await loadTesseract();const image=await prepareImage(selectedFile);
      const result=await Tesseract.recognize(image,'por',{logger:m=>{if(m.status==='recognizing text')setStatus(`Lendo etiqueta… ${Math.round((m.progress||0)*100)}%`);else if(m.status)setStatus('Processando imagem…');}});
      const parsed=parseText(result?.data?.text||'');
      if(!parsed.ca&&!parsed.name)throw new Error('Não consegui ler o CA nessa foto. Aproxime a câmera, use boa luz e deixe a etiqueta inteira visível.');
      applyResult(parsed);setStatus(parsed.ca?'CA identificado. Confira os dados antes de salvar.':'Foto lida. Confira e complete o CA antes de salvar.');toast('Dados preenchidos pela foto.');
    }catch(e){setStatus(e.message||'Falha ao ler a foto.',true);toast(e.message||'Falha ao ler a foto.');}
    finally{btn.disabled=false;btn.textContent='✨ Ler foto e preencher';}
  }

  function init(){injectUi();enforceRole();document.addEventListener('gestao-epi-auth-ready',()=>setTimeout(enforceRole,100));new MutationObserver(enforceRole).observe(document.body,{attributes:true,attributeFilter:['data-epi-role']});}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
