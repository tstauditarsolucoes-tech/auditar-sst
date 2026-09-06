(() => {
  const CURRENT='2.7.3';
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

  function fixText(){const el=document.getElementById('v270UpdateText');if(!el)return;let t=String(el.textContent||'');t=t.replace('Versão atual: 2.7.0','Versão atual: 2.7.3').replace('Versão atual: 2.7.1','Versão atual: 2.7.3').replace('Versão atual: 2.7.2','Versão atual: 2.7.3');if(el.textContent!==t)el.textContent=t;}
  function boot(){fixText();if(document.body)new MutationObserver(fixText).observe(document.body,{childList:true,subtree:true,characterData:true});}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
