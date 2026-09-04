(() => {
  if(window.__gestaoPcStabilityInstalled)return;
  window.__gestaoPcStabilityInstalled=true;

  const NativeObserver=window.MutationObserver;
  if(!NativeObserver)return;

  // O módulo de entrega cria um observer que chama fillSelects enquanto a
  // própria fillSelects altera os selects. Isso gera um ciclo contínuo e
  // congela a tela. Interceptamos somente esse observer específico.
  window.MutationObserver=class GestaoSafeMutationObserver extends NativeObserver{
    constructor(callback){
      let isDeliveryLoop=false;
      try{
        const src=Function.prototype.toString.call(callback);
        isDeliveryLoop=src.includes('pcDelivery')&&src.includes('fillSelects');
      }catch(_){}
      super(isDeliveryLoop?()=>{}:callback);
      this.__gestaoDeliveryLoopBlocked=isDeliveryLoop;
    }
  };

  // Depois que o módulo Campo do PC termina de inicializar, restauramos o
  // construtor nativo para não interferir em futuros componentes.
  setTimeout(()=>{
    if(window.MutationObserver!==NativeObserver)window.MutationObserver=NativeObserver;
  },1500);
})();