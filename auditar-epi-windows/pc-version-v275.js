(() => {
  const CURRENT='2.7.5';
  const RELEASE_API='https://api.github.com/repos/tstauditarsolucoes-tech/auditar-sst/releases/latest';
  const nativeFetch=window.fetch.bind(window);

  window.fetch=async function(input,init){
    const url=typeof input==='string'?input:String(input?.url||'');
    const res=await nativeFetch(input,init);
    if(url!==RELEASE_API)return res;
    try{
      const data=await res.clone().json();
      const tag=String(data?.tag_name||'');
      if(tag==='gestao-epi-v'+CURRENT||tag==='v'+CURRENT||tag===CURRENT){
        data.tag_name='gestao-epi-v2.7.0';
        return new Response(JSON.stringify(data),{status:res.status,statusText:res.statusText,headers:{'Content-Type':'application/json'}});
      }
    }catch(_){ }
    return res;
  };

  function fixText(){
    const el=document.getElementById('v270UpdateText');if(!el)return;
    let t=String(el.textContent||'');
    t=t.replace(/Versão atual: 2\.7\.[0-4]/g,'Versão atual: 2.7.5');
    if(el.textContent!==t)el.textContent=t;
  }

  function positionBatch(){
    const nav=document.querySelector('.sidebar nav');
    const batch=nav?.querySelector('.nav[data-view="batchDeliveryPc"]');
    const normal=nav?.querySelector('.nav[data-view="newDeliveryPc"]');
    if(batch&&normal&&batch.nextElementSibling!==normal)nav.insertBefore(batch,normal);
  }

  function cleanFaceText(){
    const p=document.querySelector('#pcFaceOverlay .pc-face-head p');
    if(p&&!document.getElementById('v274FaceName'))p.textContent='Olhe normalmente para a câmera.';
  }

  function boot(){
    fixText();cleanFaceText();
    if(document.body)new MutationObserver(()=>{fixText();cleanFaceText();}).observe(document.body,{childList:true,subtree:true,characterData:true});
    setTimeout(positionBatch,8200);
    setTimeout(positionBatch,10000);
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
