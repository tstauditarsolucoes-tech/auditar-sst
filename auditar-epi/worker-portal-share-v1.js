(()=>{
  'use strict';
  const $=(s,r=document)=>r.querySelector(s);
  const $$=(s,r=document)=>[...r.querySelectorAll(s)];
  let timer=0,observer=null;

  function auth(){return window.GestaoEpiAuth;}
  function canShare(){const role=String(auth()?.user?.()?.role||'');return role==='admin'||role==='campo';}
  function workerById(id){try{const root=JSON.parse(localStorage.getItem('auditarEpiV1')||'{}');return (root.workers||[]).find(w=>w.id===id)||null;}catch(_){return null;}}
  function toast(msg){const e=$('#toast');if(!e)return alert(msg);e.textContent=msg;e.classList.add('show');setTimeout(()=>e.classList.remove('show'),3000);}
  async function copyText(text){try{await navigator.clipboard.writeText(text);return true;}catch(_){try{const t=document.createElement('textarea');t.value=text;t.style.position='fixed';t.style.opacity='0';document.body.appendChild(t);t.select();document.execCommand('copy');t.remove();return true;}catch(__){return false;}}}

  function styles(){
    if($('#workerPortalShareStyle'))return;
    const s=document.createElement('style');s.id='workerPortalShareStyle';s.textContent=`
      .worker-portal-share{border:1px solid #b8d8d2;background:#e9f7f4;color:#0f766e;border-radius:8px;padding:6px 8px;font-size:10px;font-weight:900;cursor:pointer}
      .worker-portal-share:disabled{opacity:.55;cursor:wait}
    `;document.head.appendChild(s);
  }

  async function sharePortal(btn,id){
    if(!canShare())return toast('Seu perfil não pode gerar acesso ao Portal do Trabalhador.');
    const w=workerById(id);if(!w)return toast('Trabalhador não encontrado.');
    btn.disabled=true;const old=btn.textContent;btn.textContent='Gerando…';
    try{
      const r=await auth().api('tenant_worker_portal_link',{workerId:id,days:90});
      if(!r?.ok||!r.url)throw new Error(r?.message||'Não foi possível gerar o portal.');
      const payload={
        title:'Portal do Trabalhador • Gestão EPI',
        text:`Olá, ${w.name||'trabalhador'}. Acesse seu Portal de EPI para consultar entregas, CAs, próximas trocas e comprovantes.`,
        url:r.url
      };
      if(navigator.share){
        try{await navigator.share(payload);toast('Novo link do Portal gerado e compartilhado.');return;}
        catch(err){if(err?.name==='AbortError')return;}
      }
      const ok=await copyText(r.url);
      toast(ok?'Link do Portal copiado. Envie ao trabalhador.':'Portal gerado. Não foi possível copiar o link automaticamente.');
    }catch(err){toast(err?.message||'Falha ao gerar o Portal do Trabalhador.');}
    finally{btn.disabled=false;btn.textContent=old;}
  }

  function decorate(){
    timer=0;
    if(!canShare()){$$('[data-worker-portal-share]').forEach(b=>b.remove());return;}
    const list=$('#workerList');if(!list)return;
    list.querySelectorAll('.list-item').forEach(item=>{
      const delivery=item.querySelector('[data-del-worker]'),id=delivery?.dataset.delWorker;
      if(!id||item.querySelector('[data-worker-portal-share]'))return;
      const actions=item.querySelector('.list-actions')||item;
      const b=document.createElement('button');b.type='button';b.className='tiny worker-portal-share';b.dataset.workerPortalShare=id;b.textContent='🌐 Portal';
      b.addEventListener('click',e=>{e.preventDefault();e.stopPropagation();sharePortal(b,id);});
      actions.appendChild(b);
    });
  }
  function queue(){if(timer)return;timer=setTimeout(decorate,80);}
  function boot(){
    styles();queue();
    const list=$('#workerList');if(list){observer=new MutationObserver(queue);observer.observe(list,{childList:true,subtree:true});}
    document.addEventListener('gestao-epi-auth-ready',()=>setTimeout(queue,80));
    document.addEventListener('click',e=>{if(e.target.closest('[data-go="workers"],.nav[data-view="workers"]'))setTimeout(queue,150);},true);
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();