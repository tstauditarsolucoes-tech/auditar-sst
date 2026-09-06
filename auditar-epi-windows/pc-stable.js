(() => {
  const TENANT_CODE_KEY='gestaoEpiTenantCode';

  // O código da empresa não fica gravado no computador.
  // Não altera token, sincronização, endpoint, deviceId ou cache.
  const nativeGet=Storage.prototype.getItem;
  const nativeSet=Storage.prototype.setItem;
  const nativeRemove=Storage.prototype.removeItem;

  nativeRemove.call(localStorage,TENANT_CODE_KEY);

  Storage.prototype.getItem=function(key){
    if(key===TENANT_CODE_KEY)return '';
    return nativeGet.call(this,key);
  };
  Storage.prototype.setItem=function(key,value){
    if(key===TENANT_CODE_KEY){
      nativeRemove.call(this,key);
      return;
    }
    return nativeSet.call(this,key,value);
  };
  Storage.prototype.removeItem=function(key){
    if(key===TENANT_CODE_KEY){
      nativeRemove.call(this,key);
      return;
    }
    return nativeRemove.call(this,key);
  };

  // Única mudança estrutural da tela: menu azul e conteúdo branco rolam separados.
  const style=document.createElement('style');
  style.id='gestaoEpiPcStableScroll';
  style.textContent=`
    @media (min-width:721px){
      html,body{height:100%;overflow:hidden!important}
      .layout{height:100vh!important;min-height:0!important;overflow:hidden!important}
      .sidebar{
        position:relative!important;
        top:auto!important;
        height:100vh!important;
        min-height:0!important;
        overflow-y:auto!important;
        overflow-x:hidden!important;
        overscroll-behavior:contain!important;
      }
      .main{
        height:100vh!important;
        min-height:0!important;
        overflow-y:auto!important;
        overflow-x:hidden!important;
        overscroll-behavior:contain!important;
      }
    }
  `;
  document.head.appendChild(style);
})();
