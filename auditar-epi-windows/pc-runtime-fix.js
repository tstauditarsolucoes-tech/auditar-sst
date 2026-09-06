(() => {
  function apply(){
    // A v2.2.0 atualizava o texto deste elemento dentro de um MutationObserver
    // que também observava childList. Isso criava um ciclo infinito de mutações
    // e congelava a interface. Removemos o nó observado e mostramos a versão
    // por CSS, sem gerar novas mutações no DOM.
    document.querySelectorAll('.pc-version').forEach(el=>el.remove());

    if(!document.getElementById('pcRuntimeFixStyle')){
      const s=document.createElement('style');
      s.id='pcRuntimeFixStyle';
      s.textContent=`
        .sidebar-foot{position:relative;padding-bottom:28px!important}
        .sidebar-foot::after{
          content:'PC v2.2.1';
          position:absolute;
          left:28px;
          bottom:8px;
          font-size:9px;
          font-weight:850;
          color:#8fa6a2;
        }
      `;
      document.head.appendChild(s);
    }
  }

  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',apply,{once:true});
  else apply();
})();
