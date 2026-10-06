const EXTERNAL_CACHE='gestao-epi-v324-external';

// No Android nativo, index.html, JS, CSS, SVG e demais arquivos do app
// já estão empacotados no APK. Este Service Worker NÃO intercepta nada
// do mesmo origin para impedir que uma versão antiga do shell substitua
// os arquivos instalados após um reload.
self.addEventListener('install',event=>{
  event.waitUntil(self.skipWaiting());
});

self.addEventListener('activate',event=>{
  event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch',event=>{
  const request=event.request;
  if(request.method!=='GET')return;

  let url;
  try{url=new URL(request.url);}catch(_){return;}

  // Arquivos locais do APK devem sempre vir diretamente do servidor local
  // do Capacitor. Não usar respondWith para same-origin.
  if(url.origin===self.location.origin)return;

  // Bibliotecas externas podem continuar disponíveis offline depois de
  // terem sido carregadas uma vez.
  event.respondWith((async()=>{
    const cached=await caches.match(request);
    if(cached)return cached;

    const response=await fetch(request);
    try{
      if(response&&response.ok){
        const cache=await caches.open(EXTERNAL_CACHE);
        await cache.put(request,response.clone());
      }
    }catch(_){}
    return response;
  })());
});
