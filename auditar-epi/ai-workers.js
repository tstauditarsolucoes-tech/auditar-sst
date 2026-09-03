(() => {
  const ENDPOINT = 'https://script.google.com/macros/s/AKfycbxNG-wU-jZMKMR2cb1nR9OUd31GSUpGM0FIEagZEUP7sAHxkahLDuJ6T3wZvEe9rm6WrQ/exec';
  const KEY_STORE = 'auditarEpiSyncKey';
  let selectedFile = null;

  const $ = (s, root=document) => root.querySelector(s);
  const esc = (v='') => String(v).replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
  const clean = (v='') => String(v ?? '').replace(/\s+/g,' ').trim();
  const norm = (v='') => clean(v).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();

  function toast(msg){
    const el=$('#toast');
    if(!el) return alert(msg);
    el.textContent=msg; el.classList.add('show');
    setTimeout(()=>el.classList.remove('show'),3000);
  }

  function injectUi(){
    const drop=$('#importFile')?.closest('.import-drop');
    if(!drop || $('#aiWorkersBox')) return;
    const box=document.createElement('div');
    box.id='aiWorkersBox';
    box.innerHTML=`
      <div style="margin-top:12px;padding:12px;border:1px solid #d7e7e4;border-radius:12px;background:#f7fbfa">
        <div style="display:flex;gap:10px;align-items:center;justify-content:space-between;flex-wrap:wrap">
          <div><b>✨ IA para lista difícil</b><br><small>Use quando o PDF estiver bagunçado, escaneado ou não for reconhecido direito.</small></div>
          <button id="btnAiWorkers" type="button" class="secondary">✨ Organizar com IA</button>
        </div>
        <div id="aiWorkersStatus" style="margin-top:8px;font-size:13px"></div>
        <div id="aiWorkersConfig" style="display:none;margin-top:10px">
          <label>Chave de sincronização do Auditar SST
            <input id="aiSyncKey" type="password" autocomplete="off" placeholder="Cole a chave uma única vez neste aparelho">
          </label>
          <button id="btnSaveAiKey" type="button" class="primary" style="margin-top:8px">Salvar e ativar IA</button>
          <small style="display:block;margin-top:6px">A chave fica salva somente neste aparelho. A chave da Gemini continua protegida no Apps Script.</small>
        </div>
      </div>`;
    drop.appendChild(box);
    $('#btnAiWorkers')?.addEventListener('click', runAi);
    $('#btnSaveAiKey')?.addEventListener('click',()=>{
      const value=clean($('#aiSyncKey')?.value);
      if(!value) return toast('Cole a chave de sincronização.');
      localStorage.setItem(KEY_STORE,value);
      $('#aiWorkersConfig').style.display='none';
      setStatus('IA ativada neste aparelho.');
      toast('IA ativada.');
    });
  }

  function setStatus(text, error=false){
    const el=$('#aiWorkersStatus'); if(!el) return;
    el.textContent=text; el.style.color=error?'#a12622':'#315f59';
  }

  function toDataUrl(file){
    return new Promise((resolve,reject)=>{
      const r=new FileReader(); r.onload=()=>resolve(String(r.result||'')); r.onerror=()=>reject(r.error||new Error('Falha ao ler arquivo.')); r.readAsDataURL(file);
    });
  }

  async function extractPdfLines(file){
    if(!window.pdfjsLib) return [];
    try{
      pdfjsLib.GlobalWorkerOptions.workerSrc='https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
      const data=new Uint8Array(await file.arrayBuffer());
      const pdf=await pdfjsLib.getDocument({data}).promise;
      const lines=[];
      for(let p=1;p<=pdf.numPages;p++){
        const page=await pdf.getPage(p); const tc=await page.getTextContent(); const groups=new Map();
        tc.items.forEach(item=>{
          const y=Math.round(item.transform?.[5]||0), x=item.transform?.[4]||0;
          const key=[...groups.keys()].find(k=>Math.abs(k-y)<=2) ?? y;
          if(!groups.has(key)) groups.set(key,[]);
          groups.get(key).push({x,text:clean(item.str)});
        });
        [...groups.entries()].sort((a,b)=>b[0]-a[0]).forEach(([,items])=>{
          const line=items.sort((a,b)=>a.x-b.x).map(i=>i.text).filter(Boolean).join(' ');
          if(line) lines.push(line);
        });
      }
      return lines;
    }catch(_){ return []; }
  }

  function enrichFromLines(worker, lines){
    const target=norm(worker.name);
    const line=lines.find(l=>norm(l).includes(target));
    if(!line) return {...worker,cpf:'',reg:''};
    const cpf=(line.match(/\b\d{3}\.?\d{3}\.?\d{3}[-\s]?\d{2}\b/)||[])[0]||'';
    let reg='';
    const m=line.match(/(?:matr[ií]cula|registro|chapa)\s*[:#-]?\s*([A-Za-z0-9.-]+)/i);
    if(m) reg=m[1];
    return {...worker,cpf,reg};
  }

  function csvEscape(v){
    const s=String(v??''); return /[;"\n]/.test(s)?`"${s.replace(/"/g,'""')}"`:s;
  }

  function sendRowsToImporter(rows){
    const header=['Nome','CPF','Matrícula','Cargo','Setor'];
    const body=rows.map(w=>[w.name,w.cpf||'',w.reg||'',w.role||'',w.sector||''].map(csvEscape).join(';'));
    const blob=new Blob([[header.join(';'),...body].join('\n')],{type:'text/csv'});
    const file=new File([blob],'lista-organizada-ia.csv',{type:'text/csv'});
    const dt=new DataTransfer(); dt.items.add(file);
    const input=$('#importFile'); input.files=dt.files; input.dispatchEvent(new Event('change',{bubbles:true}));
  }

  async function runAi(){
    if(!selectedFile) return toast('Selecione primeiro a lista de funcionários.');
    const ext=(selectedFile.name.split('.').pop()||'').toLowerCase();
    if(ext!=='pdf') return toast('A IA é necessária principalmente para PDF. Excel e CSV já são lidos diretamente.');
    const syncKey=clean(localStorage.getItem(KEY_STORE)||'');
    if(!syncKey){
      $('#aiWorkersConfig').style.display='block';
      setStatus('Para proteger a IA, informe a chave de sincronização uma única vez neste aparelho.');
      return;
    }
    const btn=$('#btnAiWorkers'); btn.disabled=true; btn.textContent='✨ Lendo com IA…';
    setStatus('A IA está lendo e organizando a lista…');
    try{
      const documentData=await toDataUrl(selectedFile);
      if(!documentData.startsWith('data:application/pdf;base64,')) throw new Error('Selecione um PDF válido.');
      if(documentData.length>18000000) throw new Error('O PDF é muito grande para análise por IA.');
      const response=await fetch(ENDPOINT,{
        method:'POST',
        headers:{'Content-Type':'text/plain;charset=utf-8'},
        body:JSON.stringify({
          action:'ai_assistant',
          syncKey,
          payload:{mode:'employee_pdf_import',document:documentData}
        })
      });
      const data=await response.json();
      if(!data.ok) throw new Error(data.message||'A IA não conseguiu ler a lista.');
      const employees=Array.isArray(data.result?.employees)?data.result.employees:[];
      if(!employees.length) throw new Error('A IA não identificou funcionários nesse PDF.');
      const lines=await extractPdfLines(selectedFile);
      const rows=employees
        .map(e=>({name:clean(e.name),role:clean(e.role),sector:clean(e.sector)}))
        .filter(e=>e.name)
        .map(e=>enrichFromLines(e,lines));
      sendRowsToImporter(rows);
      setStatus(`IA organizou ${rows.length} trabalhador(es). Confira a prévia e toque em “Cadastrar funcionários”.`);
      toast('Lista organizada com IA.');
    }catch(err){
      const msg=String(err?.message||err||'Falha ao usar a IA.');
      setStatus(msg,true); toast(msg);
      if(/chave|sincroniza/i.test(msg)) $('#aiWorkersConfig').style.display='block';
    }finally{
      btn.disabled=false; btn.textContent='✨ Organizar com IA';
    }
  }

  document.addEventListener('DOMContentLoaded',()=>{
    injectUi();
    $('#importFile')?.addEventListener('change',e=>{
      selectedFile=e.target.files?.[0]||null;
      if(selectedFile){
        const ext=(selectedFile.name.split('.').pop()||'').toLowerCase();
        setStatus(ext==='pdf'?'Se a leitura normal não ficar boa, use “Organizar com IA”.':'Este formato será lido diretamente; normalmente não precisa de IA.');
      }
    });
    document.addEventListener('click',e=>{ if(e.target.closest('[data-go="importWorkers"]')) setTimeout(injectUi,0); });
  });
})();
