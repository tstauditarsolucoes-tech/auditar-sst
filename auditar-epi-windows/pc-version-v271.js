(() => {
  const CURRENT='2.7.1';
  const RELEASE_API='https://api.github.com/repos/tstauditarsolucoes-tech/auditar-sst/releases/latest';
  const nativeFetch=window.fetch.bind(window);

  // Compatibilidade com o verificador da v2.7.0: quando a versão publicada é a
  // própria 2.7.1, apresentamos como equivalente para evitar que o app ofereça
  // atualização para ele mesmo. Versões futuras continuam sendo detectadas.
  window.fetch=async function(input,init){
    const url=typeof input==='string'?input:String(input?.url||'');
    const res=await nativeFetch(input,init);
    if(url!==RELEASE_API)return res;
    try{
      const clone=res.clone();
      const data=await clone.json();
      const tag=String(data?.tag_name||'');
      if(tag==='gestao-epi-v'+CURRENT||tag==='v'+CURRENT||tag===CURRENT){
        data.tag_name='gestao-epi-v2.7.0';
        return new Response(JSON.stringify(data),{
          status:res.status,
          statusText:res.statusText,
          headers:{'Content-Type':'application/json'}
        });
      }
    }catch(_){ }
    return res;
  };

  function fixText(){
    const el=document.getElementById('v270UpdateText');
    if(!el)return;
    const text=String(el.textContent||'');
    if(text.includes('Versão atual: 2.7.0'))el.textContent=text.replace('Versão atual: 2.7.0','Versão atual: 2.7.1');
  }

  function boot(){
    fixText();
    const root=document.body;
    if(!root)return;
    const obs=new MutationObserver(fixText);
    obs.observe(root,{childList:true,subtree:true,characterData:true});
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});
  else boot();
})();
