const CACHE='gestao-epi-v301-shell';
const ASSETS=[
  './','./index.html',
  './styles.css','./import-workers.css','./stock.css',
  './app.js','./import-workers.js','./ai-workers.js','./stock.js',
  './signature-assist.js','./biometric-crypto-v1.js','./biometric-face.js','./liveness-face.js',
  './company-branding.js','./auth.js','./brand-login-v300.js',
  './worker-portal-share-v1.js','./ux-v300.js','./cloud-sync.js',
  './manifest.webmanifest','./icon.svg','./brand-icon-v300.svg','./brand-logo-v300.svg'
];

async function putSafe(request,response){
  try{
    if(!response)return;
    const cache=await caches.open(CACHE);
    await cache.put(request,response.clone());
  }catch(_){}
}

self.addEventListener('install',event=>{
  event.waitUntil(
    caches.open(CACHE)
      .then(cache=>cache.addAll(ASSETS))
      .then(()=>self.skipWaiting())
  );
});

self.addEventListener('activate',event=>{
  event.waitUntil((async()=>{
    const keys=await caches.keys();
    await Promise.all(
      keys
        .filter(key=>key!==CACHE && /^gestao-epi-/i.test(key))
        .map(key=>caches.delete(key))
    );

    await self.clients.claim();

    // Hotfix v3.0.1: quem estiver preso em uma página antiga é recarregado uma
    // única vez após o novo Service Worker assumir o controle.
    const clients=await self.clients.matchAll({type:'window',includeUncontrolled:true});
    await Promise.all(clients.map(async client=>{
      try{
        if(client.navigate && String(client.url||'').startsWith(self.location.origin)){
          await client.navigate(client.url);
        }
      }catch(_){}
    }));
  })());
});

self.addEventListener('fetch',event=>{
  const request=event.request;
  if(request.method!=='GET')return;

  const url=new URL(request.url);
  const sameOrigin=url.origin===self.location.origin;

  if(!sameOrigin){
    // Mantém bibliotecas CDN disponíveis depois do primeiro carregamento,
    // mas nunca devolve index.html no lugar de JavaScript externo.
    event.respondWith(
      caches.match(request).then(cached=>{
        if(cached)return cached;
        return fetch(request).then(response=>{
          putSafe(request,response);
          return response;
        });
      })
    );
    return;
  }

  // No app Android o "network" é o servidor local do próprio APK. Portanto
  // network-first lê sempre os arquivos da versão instalada, mesmo sem internet.
  event.respondWith((async()=>{
    try{
      const response=await fetch(request);
      if(response && response.ok)putSafe(request,response);
      return response;
    }catch(_){
      const cached=await caches.match(request);
      if(cached)return cached;

      if(request.mode==='navigate' || request.destination==='document'){
        const fallback=await caches.match('./index.html');
        if(fallback)return fallback;
      }

      throw _;
    }
  })());
});
