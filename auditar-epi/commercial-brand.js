(() => {
  function applyBrand(){
    document.title='Gestão EPI';
    const meta=document.querySelector('meta[name="description"]');if(meta)meta.content='Gestão EPI - controle, entrega e gestão de equipamentos de proteção individual.';
    document.querySelectorAll('.brand').forEach(el=>el.innerHTML='GESTÃO <span>EPI</span>');
    const eyebrow=document.querySelector('.eyebrow');if(eyebrow)eyebrow.textContent='GESTÃO EPI • CAMPO';
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',applyBrand);else applyBrand();
  setTimeout(applyBrand,300);
})();
