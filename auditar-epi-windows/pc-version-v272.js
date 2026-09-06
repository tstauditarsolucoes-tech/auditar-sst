(() => {
  const CURRENT='2.7.2';
  const RELEASE_API='https://api.github.com/repos/tstauditarsolucoes-tech/auditar-sst/releases/latest';
  const nativeFetch=window.fetch.bind(window);

  // Compatibilidade com o verificador original da v2.7.0. Quando a versão
  // publicada é a própria 2.7.2, ela não deve ser oferecida como atualização.
  // Versões posteriores continuam sendo detectadas normalmente.
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
    let text=String(el.textContent||'');
    text=text.replace('Versão atual: 2.7.0','Versão atual: 2.7.2').replace('Versão atual: 2.7.1','Versão atual: 2.7.2');
    if(el.textContent!==text)el.textContent=text;
  }

  function boot(){
    fixText();
    const root=document.body;if(!root)return;
    new MutationObserver(fixText).observe(root,{childList:true,subtree:true,characterData:true});
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});
  else boot();
})();
