(() => {
  const $=(s,r=document)=>r.querySelector(s);
  const clean=v=>String(v??'').replace(/\s+/g,' ').trim();
  const norm=v=>clean(v).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
  let file=null;

  function toast(msg){
    const e=$('#toast');
    if(!e)return alert(msg);
    e.textContent=msg;e.classList.add('show');setTimeout(()=>e.classList.remove('show'),3000);
  }
  function dataUrl(f){return new Promise((res,rej)=>{const r=new FileReader();r.onload=()=>res(String(r.result||''));r.onerror=()=>rej(new Error('Falha ao ler arquivo.'));r.readAsDataURL(f);});}
  async function pdfLines(f){
    if(!window.pdfjsLib)return[];
    try{
      pdfjsLib.GlobalWorkerOptions.workerSrc='https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
      const pdf=await pdfjsLib.getDocument({data:new Uint8Array(await f.arrayBuffer())}).promise,lines=[];
      for(let p=1;p<=pdf.numPages;p++){
        const pg=await pdf.getPage(p),tc=await pg.getTextContent(),g=new Map();
        tc.items.forEach(i=>{const y=Math.round(i.transform?.[5]||0),x=i.transform?.[4]||0,key=[...g.keys()].find(k=>Math.abs(k-y)<=2)??y;if(!g.has(key))g.set(key,[]);g.get(key).push({x,t:clean(i.str)});});
        [...g.entries()].sort((a,b)=>b[0]-a[0]).forEach(([,a])=>{const l=a.sort((x,y)=>x.x-y.x).map(z=>z.t).filter(Boolean).join(' ');if(l)lines.push(l);});
      }
      return lines;
    }catch(_){return[];}
  }
  function enrich(w,lines){
    const l=lines.find(x=>norm(x).includes(norm(w.name)));
    if(!l)return w;
    const cpf=(l.match(/\b\d{3}\.?\d{3}\.?\d{3}[-\s]?\d{2}\b/)||[])[0]||'',m=l.match(/(?:matr[ií]cula|registro|chapa)\s*[:#-]?\s*([A-Za-z0-9.-]+)/i);
    return{...w,cpf:w.cpf||cpf,reg:w.reg||(m?.[1]||'')};
  }
  function csv(v){const s=String(v??'');return /[;"\n]/.test(s)?`"${s.replace(/"/g,'""')}"`:s;}
  function send(rows){
    const text=['Nome;CPF;Matrícula;Cargo;Setor',...rows.map(w=>[w.name,w.cpf||'',w.reg||'',w.role||'',w.sector||''].map(csv).join(';'))].join('\n');
    const blob=new Blob([text],{type:'text/csv'}),f=new File([blob],'lista-organizada-ia.csv',{type:'text/csv'}),dt=new DataTransfer();
    dt.items.add(f);const input=$('#pcImportFile');input.files=dt.files;input.dispatchEvent(new Event('change',{bubbles:true}));
  }

  function inject(){
    const panel=$('#pcImport .panel');
    if(!panel||$('#pcAiImportBox'))return;
    const box=document.createElement('div');
    box.id='pcAiImportBox';
    box.style.cssText='margin-top:16px;padding:14px;border:1px solid #d7e7e4;border-radius:14px;background:#f7fbfa';
    box.innerHTML=`<div style="display:flex;gap:10px;justify-content:space-between;align-items:center;flex-wrap:wrap"><div><b>✨ IA para PDF difícil</b><br><small>Use quando a leitura normal do PDF ficar bagunçada ou incompleta.</small></div><button id="pcRunAiImport" class="secondary" type="button">✨ Organizar com IA</button></div><div id="pcAiStatus" class="pc-small" style="margin-top:8px">A IA usa automaticamente o acesso da empresa conectada. Nenhuma chave precisa ser informada aqui.</div>`;
    panel.appendChild(box);
    $('#pcRunAiImport').onclick=run;
    $('#pcImportFile')?.addEventListener('change',e=>{file=e.target.files?.[0]||null;});
  }

  async function run(){
    if(!file)return toast('Selecione primeiro o PDF.');
    if((file.name.split('.').pop()||'').toLowerCase()!=='pdf')return toast('A IA é indicada para PDF; Excel e CSV já são lidos diretamente.');
    if(!window.GestaoEpiAuth?.api||!window.GestaoEpiAuth?.token?.())return toast('Entre na empresa antes de usar a IA.');
    const btn=$('#pcRunAiImport');btn.disabled=true;btn.textContent='✨ Lendo com IA…';
    $('#pcAiStatus').textContent='A IA está lendo e organizando o PDF…';
    try{
      const doc=await dataUrl(file);
      if(doc.length>18000000)throw new Error('PDF muito grande para análise por IA.');
      const json=await window.GestaoEpiAuth.api('tenant_ai_assistant',{payload:{mode:'employee_pdf_import',document:doc}});
      if(!json?.ok)throw new Error(json?.message||'A IA não conseguiu ler a lista.');
      const employees=Array.isArray(json.result?.employees)?json.result.employees:[];
      if(!employees.length)throw new Error('Nenhum funcionário identificado pela IA.');
      const lines=await pdfLines(file);
      const rows=employees.map(e=>({name:clean(e.name),cpf:clean(e.cpf),reg:clean(e.reg),role:clean(e.role),sector:clean(e.sector)})).filter(e=>e.name).map(e=>enrich(e,lines));
      send(rows);
      $('#pcAiStatus').textContent=`IA organizou ${rows.length} trabalhador(es). Confira a prévia antes de cadastrar.`;
      toast('Lista organizada com IA.');
    }catch(e){
      const msg=String(e?.message||e||'Falha ao usar IA.');
      $('#pcAiStatus').textContent=msg;
      toast(msg);
    }finally{btn.disabled=false;btn.textContent='✨ Organizar com IA';}
  }

  function init(){inject();const target=$('#pcImport');if(target)new MutationObserver(()=>{if(!$('#pcAiImportBox'))inject();}).observe(target,{childList:true,subtree:true});}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(init,150),{once:true});else setTimeout(init,150);
})();