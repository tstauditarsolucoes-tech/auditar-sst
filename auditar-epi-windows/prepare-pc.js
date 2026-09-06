const fs = require('fs');
const path = require('path');

const appDir = path.join(__dirname, 'app');

function read(name) {
  return fs.readFileSync(path.join(appDir, name), 'utf8');
}

function write(name, text) {
  fs.writeFileSync(path.join(appDir, name), text, 'utf8');
}

function replaceExact(text, from, to, label) {
  if (!text.includes(from)) {
    throw new Error(`Preparação PC falhou: trecho não encontrado (${label}).`);
  }
  return text.replace(from, to);
}

// -----------------------------------------------------------------------------
// app.js: remove a dependência da chave antiga e usa diretamente a sessão
// autenticada do login comercial para sincronizar.
// -----------------------------------------------------------------------------
let app = read('app.js');

const oldSync = `  async function sync({silent=false}={}){
    const key=(localStorage.getItem(KEY_STORE)||'').trim();
    if(!key){showConnect();return false;}
    if(syncing)return false;
    if(!navigator.onLine){setSync('error','Sem internet');return false;}
    syncing=true;setSync('busy','Sincronizando…');
    try{
      const res=await fetch(ENDPOINT,{method:'POST',headers:{'Content-Type':'text/plain;charset=utf-8'},body:JSON.stringify({action:'epi_sync_merge',syncKey:key,deviceId:deviceId(),client:'gestao',payload:data})});
      const json=await res.json();
      if(!json?.ok)throw new Error(json?.message||'Falha na sincronização.');
      data=normalize(json.payload||{});saveCache();setSync('ok','Sincronizado');renderAll();hideConnect();if(!silent)toast('Dados sincronizados.');return true;
    }catch(err){setSync('error','Falha na sync');if(!silent)toast(err.message||'Falha na sincronização.');return false;}
    finally{syncing=false;}
  }`;

const newSync = `  async function sync({silent=false}={}){
    const auth=window.GestaoEpiAuth;
    const authToken=String(auth?.token?.()||'').trim();
    if(!auth||!auth.api||!authToken){setSync('','Aguardando login');return false;}
    if(syncing)return false;
    if(!navigator.onLine){setSync('error','Sem internet');return false;}
    syncing=true;setSync('busy','Sincronizando…');
    try{
      const json=await auth.api('epi_sync_merge',{deviceId:deviceId(),client:'gestao',payload:data});
      if(!json?.ok)throw new Error(json?.message||'Falha na sincronização.');
      data=normalize(json.payload||{});saveCache();setSync('ok','Sincronizado');renderAll();hideConnect();if(!silent)toast('Dados sincronizados.');return true;
    }catch(err){setSync('error','Falha na sync');if(!silent)toast(err?.message||'Falha na sincronização.');return false;}
    finally{syncing=false;}
  }`;

app = replaceExact(app, oldSync, newSync, 'sync autenticada');

const oldBoot = `  document.addEventListener('DOMContentLoaded',()=>{
    data=loadCache();bind();renderAll();
    const key=(localStorage.getItem(KEY_STORE)||'').trim();
    if(key){hideConnect();sync({silent:true});}else showConnect();
    setInterval(()=>{if(!document.hidden&&navigator.onLine&&(localStorage.getItem(KEY_STORE)||'').trim())sync({silent:true});},20000);
  });`;

const newBoot = `  async function afterLogin(){
    // Recarrega o cache depois que o tenant foi definido pelo login. Isso impede
    // que dados em memória de outra empresa sejam enviados para o tenant atual.
    data=loadCache();
    renderAll();
    hideConnect();
    return sync({silent:true});
  }

  function waitingLogin(){
    hideConnect();
    setSync('','Aguardando login');
  }

  window.GestaoEpiApp={sync,afterLogin,waitingLogin};

  document.addEventListener('DOMContentLoaded',()=>{
    data=loadCache();bind();renderAll();hideConnect();
    if(String(window.GestaoEpiAuth?.token?.()||'').trim()) afterLogin();
    else waitingLogin();
    setInterval(()=>{
      if(!document.hidden&&navigator.onLine&&String(window.GestaoEpiAuth?.token?.()||'').trim()){
        sync({silent:true});
      }
    },20000);
  });`;

app = replaceExact(app, oldBoot, newBoot, 'inicialização da sincronização');
write('app.js', app);

// -----------------------------------------------------------------------------
// auth-gestao.js: código da empresa não fica salvo e, após o login, o próprio
// aplicativo recarrega o cache do tenant e sincroniza pela API autenticada.
// -----------------------------------------------------------------------------
let auth = read('auth-gestao.js');

auth = replaceExact(
  auth,
  "function save(t,u,tenant){prepareTenantStorage(tenant?.id||'');localStorage.setItem(TOKEN_KEY,t);localStorage.setItem(USER_KEY,JSON.stringify(u));localStorage.setItem(TENANT_KEY,JSON.stringify(tenant));localStorage.setItem(TENANT_CODE_KEY,tenant?.code||'');currentUser=u;currentTenant=tenant;}",
  "function save(t,u,tenant){prepareTenantStorage(tenant?.id||'');localStorage.setItem(TOKEN_KEY,t);localStorage.setItem(USER_KEY,JSON.stringify(u));localStorage.setItem(TENANT_KEY,JSON.stringify(tenant));localStorage.removeItem(TENANT_CODE_KEY);currentUser=u;currentTenant=tenant;}",
  'não salvar código da empresa'
);

auth = replaceExact(
  auth,
  "function clear(){localStorage.removeItem(TOKEN_KEY);localStorage.removeItem(USER_KEY);localStorage.removeItem(TENANT_KEY);currentUser=null;currentTenant=null;}",
  "function clear(){localStorage.removeItem(TOKEN_KEY);localStorage.removeItem(USER_KEY);localStorage.removeItem(TENANT_KEY);localStorage.removeItem(TENANT_CODE_KEY);currentUser=null;currentTenant=null;window.GestaoEpiApp?.waitingLogin?.();}",
  'limpeza da sessão'
);

auth = replaceExact(
  auth,
  "$('#gestaoTenantCode').value=localStorage.getItem(TENANT_CODE_KEY)||'';",
  "$('#gestaoTenantCode').value='';",
  'campo empresa vazio'
);

const refreshOld = "setTimeout(()=>$('#btnRefresh')?.click(),250);";
const refreshNew = "setTimeout(()=>window.GestaoEpiApp?.afterLogin?.(),120);";
if (!auth.includes(refreshOld)) {
  throw new Error('Preparação PC falhou: gatilho de atualização pós-login não encontrado.');
}
auth = auth.split(refreshOld).join(refreshNew);
write('auth-gestao.js', auth);

console.log('Preparação PC concluída: sincronização usa somente login autenticado; chave antiga removida do fluxo.');
