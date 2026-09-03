(() => {
  const OLD_KEY='auditarEpiSyncKey';
  const NEW_KEY='auditarEpiCentralKey';
  const OLD_ENDPOINT='https://script.google.com/macros/s/AKfycbxNG-wU-jZMKMR2cb1nR9OUd31GSUpGM0FIEagZEUP7sAHxkahLDuJ6T3wZvEe9rm6WrQ/exec';
  const NEW_ENDPOINT='https://script.google.com/macros/s/AKfycbxqMnKiTlAJTFv3-odS2dB1NRcSD8wwvtNxxa-zCFhTM6GeNZszib_1N6eT9wSnOnOyjg/exec';

  const nativeGet=Storage.prototype.getItem;
  const nativeSet=Storage.prototype.setItem;
  const nativeRemove=Storage.prototype.removeItem;

  Storage.prototype.getItem=function(key){
    return nativeGet.call(this,key===OLD_KEY?NEW_KEY:key);
  };
  Storage.prototype.setItem=function(key,value){
    return nativeSet.call(this,key===OLD_KEY?NEW_KEY:key,value);
  };
  Storage.prototype.removeItem=function(key){
    return nativeRemove.call(this,key===OLD_KEY?NEW_KEY:key);
  };

  const nativeFetch=window.fetch.bind(window);
  window.fetch=function(input,init){
    if(typeof input==='string' && input===OLD_ENDPOINT) input=NEW_ENDPOINT;
    return nativeFetch(input,init);
  };

  document.addEventListener('DOMContentLoaded',()=>{
    const input=document.getElementById('connectKey');
    if(input) input.placeholder='Cole a chave do Auditar EPI';
  });
})();
