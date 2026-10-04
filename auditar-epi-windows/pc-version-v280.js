(()=>{
  const CURRENT='2.9.0';
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
        data.tag_name='gestao-epi-v2.7.9';
        return new Response(JSON.stringify(data),{
          status:res.status,
          statusText:res.statusText,
          headers:{'Content-Type':'application/json'}
        });
      }
    }catch(_){}
    return res;
  };

  function refreshUi(){
    const el=document.getElementById('v270UpdateText');
    if(el){
      const next=String(el.textContent||'').replace(/Versão atual: 2\.\d+\.\d+/g,'Versão atual: 2.9.0');
      if(el.textContent!==next)el.textContent=next;
    }
    const v=document.querySelector('.pc-version');
    if(v)v.textContent='PC v2.9.0';
  }

  function boot(){
    [0,300,1000,2500,5000,9000].forEach(ms=>setTimeout(refreshUi,ms));
  }

  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});
  else boot();
})();