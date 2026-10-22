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
      #workerPortalActions382{position:fixed;inset:0;z-index:32000;background:rgba(4,35,31,.7);display:none;align-items:center;justify-content:center;padding:17px}
      #workerPortalActions382.open{display:flex}
      .wp382-card{position:relative;width:min(100%,430px);background:#fff;border-radius:20px;padding:24px;box-shadow:0 12px 36px rgba(0,0,0,.2)}
      .wp382-card h2{font-size:21px;color:#173d39}.wp382-card p{color:#4d736d;font-size:14px;line-height:1.5}
      .wp382-btn{display:block;width:100%;min-height:51px;margin:10px 0;border:1px solid #cfe3de;border-radius:12px;background:#eaf6f3;color:#0c6f60;font-weight:850;font-size:15px}
      .wp382-btn.primary{background:#0e9074;color:#fff}
      .wp382-close{position:absolute;top:12px;right:12px;border:0;background:#eff7f5;border-radius:10px;width:42px;height:42px;font-size:23px}
      #wp382Error{min-height:21px;color:#8a5220}
    `;document.head.appendChild(s);
  }

  let portalUrl='',portalWorker=null;
  function portalPlugin(){
    try{if(window.Capacitor?.registerPlugin)return window.Capacitor.registerPlugin('ExternalLink')}catch(_){}
    return window.Capacitor?.Plugins?.ExternalLink||null;
  }
  function isValidPortalUrl(value){
    try{const url=new URL(String(value||''));return url.protocol==='https:'&&!!url.hostname}catch(_){return false}
  }
  function portalModal(){
    let modal=$('#workerPortalActions382');if(modal)return modal;
    modal=document.createElement('div');modal.id='workerPortalActions382';
    modal.innerHTML='<div class="wp382-card" role="dialog" aria-modal="true" aria-label="Portal do Trabalhador"><button id="wp382Close" class="wp382-close" type="button">×</button><h2>Portal do Trabalhador</h2><p id="wp382Name"></p><p>Escolha o que deseja fazer com o link individual deste trabalhador.</p><button type="button" class="wp382-btn primary" data-wp382-action="open">🌐 Abrir Portal no navegador</button><button type="button" class="wp382-btn" data-wp382-action="share">↗ Compartilhar link</button><button type="button" class="wp382-btn" data-wp382-action="copy">📋 Copiar link</button><p id="wp382Error" role="status"></p></div>';
    document.body.appendChild(modal);
    $('#wp382Close').onclick=()=>{modal.classList.remove('open');portalUrl='';portalWorker=null};
    modal.addEventListener('click',e=>{if(e.target===modal)$('#wp382Close').click()});
    modal.addEventListener('click',async e=>{
      const button=e.target.closest('[data-wp382-action]');if(!button||!portalUrl)return;
      const action=button.dataset.wp382Action,url=portalUrl,msg='Olá, '+(portalWorker?.name||'trabalhador')+'. Acesse o Portal do Trabalhador Gestão EPI:';
      const error=$('#wp382Error');error.textContent='';button.disabled=true;
      try{
        if(action==='copy'){const ok=await copyText(url);if(!ok)throw Error('Não foi possível copiar.');error.textContent='Link copiado para enviar ao trabalhador.';return}
        const native=portalPlugin();
        if(action==='open'){
          if(window.Capacitor?.isNativePlatform?.()&&native?.openUrl){await native.openUrl({url});return}
          const tab=window.open(url,'_blank','noopener,noreferrer');if(!tab)throw Error('Navegador não abriu. Use Copiar link.');
          return;
        }
        if(action==='share'){
          if(window.Capacitor?.isNativePlatform?.()&&native?.shareLink){await native.shareLink({url,message:msg});return}
          if(navigator.share){await navigator.share({title:'Portal do Trabalhador • Gestão EPI',text:msg,url});return}
          throw Error('Compartilhamento não disponível. Use Copiar link.');
        }
      }catch(ex){
        if(ex?.name!=='AbortError')error.textContent=String(ex?.message||ex||'Não foi possível completar a ação.');
      }finally{button.disabled=false}
    });
    return modal;
  }
  async function sharePortal(btn,id){
    if(!canShare())return toast('Seu perfil não pode gerar acesso ao Portal do Trabalhador.');
    const w=workerById(id);if(!w)return toast('Trabalhador não encontrado.');
    btn.disabled=true;const old=btn.textContent;btn.textContent='Abrindo…';
    try{
      const res=await auth().api('tenant_worker_portal_link',{workerId:id,days:90});
      if(!res?.ok||!isValidPortalUrl(res.url))throw new Error(res?.message||'Não foi possível gerar link HTTPS do Portal.');
      portalUrl=res.url;portalWorker=w;
      const modal=portalModal();$('#wp382Name').textContent=w.name||'Trabalhador';
      $('#wp382Error').textContent='';
      modal.classList.add('open');
    }catch(err){toast(err?.message||'Falha ao acessar Portal do Trabalhador.');}
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