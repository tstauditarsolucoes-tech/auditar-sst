(() => {
  function apply(){
    // Mantém a identificação da versão fora do MutationObserver para evitar
    // o ciclo de mutações que já havia causado travamento da interface.
    document.querySelectorAll('.pc-version').forEach(el=>el.remove());

    if(!document.getElementById('pcRuntimeFixStyle')){
      const s=document.createElement('style');
      s.id='pcRuntimeFixStyle';
      s.textContent=`
        .sidebar-foot{position:relative;padding-bottom:28px!important}
        .sidebar-foot::after{
          content:'PC v2.2.2';
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
