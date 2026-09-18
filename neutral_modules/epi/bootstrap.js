window.SST_EPI_ENDPOINT=__SST_EPI_ENDPOINT_JSON__;
window.SST_EPI_SYNC_KEY=__SST_EPI_SYNC_KEY_JSON__;
window.SST_EPI_BOOTSTRAP=__SST_EPI_BOOTSTRAP_JSON__;

(function(){
  const endpoint=String(window.SST_EPI_ENDPOINT||'');
  const key=String(window.SST_EPI_SYNC_KEY||'');
  const boot=window.SST_EPI_BOOTSTRAP||{};

  function mergeRows(a,b){
    const map=new Map();
    (Array.isArray(a)?a:[]).concat(Array.isArray(b)?b:[]).forEach(function(x){
      if(!x||!x.id)return;
      const id=String(x.id);
      map.set(id,Object.assign({},map.get(id)||{},x));
    });
    return Array.from(map.values());
  }

  function company(x){
    return {
      id:String(x.id||''),
      name:String(x.name||''),
      cnpj:String(x.cnpj||''),
      active:x.active!==false,
      updatedAt:String(x.updatedAt||new Date().toISOString())
    };
  }

  function worker(x){
    return {
      id:String(x.id||''),
      companyId:String(x.companyId||x.company_id||''),
      name:String(x.name||''),
      cpf:String(x.cpf||''),
      reg:String(x.reg||''),
      role:String(x.role||''),
      sector:String(x.sector||''),
      active:x.active!==false,
      updatedAt:String(x.updatedAt||new Date().toISOString())
    };
  }

  const companies=(boot.companies||[]).map(company).filter(function(x){return x.id&&x.name;});
  const workers=(boot.workers||[]).map(worker).filter(function(x){return x.id&&x.name&&x.companyId;});

  try{
    const appKey='sstGestaoEpiV1';
    const current=JSON.parse(localStorage.getItem(appKey)||'{}');
    const next={
      companies:mergeRows(current.companies,companies),
      workers:mergeRows(current.workers,workers),
      epis:Array.isArray(current.epis)?current.epis:[],
      deliveries:Array.isArray(current.deliveries)?current.deliveries:[],
      purchases:Array.isArray(current.purchases)?current.purchases:[],
      batches:Array.isArray(current.batches)?current.batches:[],
      auditLog:Array.isArray(current.auditLog)?current.auditLog:[]
    };
    localStorage.setItem(appKey,JSON.stringify(next));
  }catch(_){}

  try{
    const cacheKey='sstGestaoEpiGestaoCacheV1';
    const current=JSON.parse(localStorage.getItem(cacheKey)||'{}');
    const app=current.app&&typeof current.app==='object'?current.app:{};
    current.version=Number(current.version||2);
    current.app=Object.assign({},app,{
      companies:mergeRows(app.companies,companies),
      workers:mergeRows(app.workers,workers),
      epis:Array.isArray(app.epis)?app.epis:[],
      deliveries:Array.isArray(app.deliveries)?app.deliveries:[],
      purchases:Array.isArray(app.purchases)?app.purchases:[],
      batches:Array.isArray(app.batches)?app.batches:[],
      auditLog:Array.isArray(app.auditLog)?app.auditLog:[]
    });
    current.stock=current.stock&&typeof current.stock==='object'
      ? current.stock
      : {startedAt:'',processedDeliveryIds:[],movements:[],minimums:{}};
    localStorage.setItem(cacheKey,JSON.stringify(current));
  }catch(_){}

  ['sstGestaoEpiSyncKey','sstGestaoEpiCentralKey'].forEach(function(k){
    try{localStorage.setItem(k,key);}catch(_){}
  });

  window.GestaoEpiAuth={
    token:function(){return key;},
    deviceId:function(){
      const k='sstGestaoEpiModuleDeviceId';
      let id=localStorage.getItem(k);
      if(!id){
        id='sst_epi_'+Date.now()+'_'+Math.random().toString(36).slice(2,9);
        localStorage.setItem(k,id);
      }
      return id;
    },
    isReady:function(){return true;},
    user:function(){return boot.user||null;},
    tenant:function(){return {id:'sst-gestao',code:'SST-GESTAO',name:'SST Gestão'};}
  };

  window.__SST_EPI_CONFIG_OK=!!endpoint&&!!key;
})();