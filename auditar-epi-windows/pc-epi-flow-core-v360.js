(function(root,factory){
  const api=factory();
  if(typeof module==='object'&&module.exports)module.exports=api;
  root.GestaoEpiFlowCore=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';
  const remaining=item=>Math.max(0,Number(item?.qty||0)-Number(item?.deliveredQty||0));
  const effectiveEpi=item=>item?.substitution?.status==='approved'&&item.substitution.toEpiId?String(item.substitution.toEpiId):String(item?.epiId||'');
  function statusOf(a,at=Date.now()){
    if(a?.status==='cancelled'||a?.status==='delivered')return a.status;
    if(a?.expiresAt&&at>Date.parse(a.expiresAt))return 'expired';
    const rem=(a?.items||[]).reduce((s,i)=>s+remaining(i),0);
    if(rem<=0)return 'delivered';
    if((a?.items||[]).some(i=>Number(i.deliveredQty||0)>0))return 'partial';
    return 'pending';
  }
  const stockBalance=(movements,c,e)=>(movements||[]).filter(m=>m?.companyId===c&&m?.epiId===e).reduce((s,m)=>s+Number(m.delta||0),0);
  function reservedQty(authorizations,c,e,except='',at=Date.now()){
    return (authorizations||[]).filter(a=>a?.id!==except&&a?.companyId===c&&['pending','partial'].includes(statusOf(a,at))).reduce((sum,a)=>sum+(a.items||[]).reduce((q,i)=>effectiveEpi(i)===e?q+remaining(i):q,0),0);
  }
  const available=(movements,authorizations,c,e,except='',at=Date.now())=>stockBalance(movements,c,e)-reservedQty(authorizations,c,e,except,at);
  function deliveryFitsAuthorization(a,draft,at=Date.now()){
    if(!a||!draft)return {ok:false,reason:'LIBERACAO_AUSENTE'};
    const st=statusOf(a,at);
    if(!['pending','partial'].includes(st))return {ok:false,reason:'LIBERACAO_INDISPONIVEL'};
    if(a.companyId!==draft.companyId||a.workerId!==draft.workerId)return {ok:false,reason:'TRABALHADOR_EMPRESA_DIVERGENTE'};
    for(const di of (draft.items||[])){
      const ai=(a.items||[]).find(i=>effectiveEpi(i)===di.epiId&&remaining(i)>0);
      if(!ai)return {ok:false,reason:'EPI_NAO_LIBERADO',epiId:di.epiId};
      if(Number(di.qty||0)>remaining(ai))return {ok:false,reason:'QUANTIDADE_ACIMA_LIBERADA',epiId:di.epiId,remaining:remaining(ai)};
    }
    return {ok:true};
  }
  function activeClaims(claims,authorizationId,at=Date.now()){
    return (claims||[]).filter(c=>c?.type==='epi_authorization_claim'&&c?.authorizationId===authorizationId&&c?.status!=='lost'&&c?.status!=='consumed'&&(!c.expiresAt||Date.parse(c.expiresAt)>at));
  }
  function chooseClaimWinner(claims,authorizationId,at=Date.now()){
    return activeClaims(claims,authorizationId,at).slice().sort((a,b)=>{
      const ta=Date.parse(a.createdAt||0)||0,tb=Date.parse(b.createdAt||0)||0;
      return ta-tb||String(a.id||'').localeCompare(String(b.id||''));
    })[0]||null;
  }
  function reportStats(root,sinceMs=0,at=Date.now()){
    const app=root?.app||{},log=Array.isArray(app.auditLog)?app.auditLog:[],auths=log.filter(x=>x?.type==='epi_authorization'&&(!sinceMs||Date.parse(x.createdAt||0)>=sinceMs)),direct=log.filter(x=>x?.type==='epi_direct_delivery'&&(!sinceMs||Date.parse(x.createdAt||0)>=sinceMs));
    const result={authorizations:auths.length,pending:0,partial:0,delivered:0,expired:0,cancelled:0,direct:direct.length,directPendingReview:direct.filter(x=>x.reviewStatus!=='reviewed').length,authorizedUnits:0,deliveredUnits:0,avgPickupHours:null};
    let totalMs=0,count=0;
    auths.forEach(a=>{
      const st=statusOf(a,at);if(result[st]!=null)result[st]++;
      result.authorizedUnits+=(a.items||[]).reduce((s,i)=>s+Number(i.qty||0),0);
      result.deliveredUnits+=(a.items||[]).reduce((s,i)=>s+Number(i.deliveredQty||0),0);
      if(a.lastDeliveredAt&&(a.authorizedAt||a.createdAt)){const ms=Date.parse(a.lastDeliveredAt)-Date.parse(a.authorizedAt||a.createdAt);if(Number.isFinite(ms)&&ms>=0){totalMs+=ms;count++;}}
    });
    if(count)result.avgPickupHours=totalMs/count/3600000;
    return result;
  }
  return {remaining,effectiveEpi,statusOf,stockBalance,reservedQty,available,deliveryFitsAuthorization,activeClaims,chooseClaimWinner,reportStats};
});