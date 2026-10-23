/** SUPERVISÃO DOS TÉCNICOS V1 — somente leitura e exclusivamente ADM.
 * "Ativo recentemente" = comunicação autenticada com a Central nos últimos 15 minutos.
 * NÃO comprova aplicativo aberto em primeiro plano; sincronização pode ocorrer ao fundo.
 * Não grava login, sync, foto, atividades ou localização.
 */
function technicianSupervisionV1_(request) {
  const actor = authUserFromToken_(String(request.authToken||''),false);
  if(!actor || actor.role!=='admin' || actor.active!==true)
    return {ok:false,code:'ACCESS_DENIED',message:'Acesso exclusivo da conta ADM.'};
  const days=Number(request.days||7),limit=Number(request.limit||120);
  if(!Number.isInteger(days)||days<1||days>90||!Number.isInteger(limit)||limit<1||limit>200)
    return {ok:false,code:'INVALID_FILTER'};
  const ss=ensureAuthStorage_(),now=Date.now(),minimum=now-days*86400000;
  const when=(value)=>{
    if(!value)return '';
    const d=value instanceof Date?value:new Date(value);
    return Number.isFinite(d.getTime())?d.toISOString():'';
  };
  const users=readAuthUsers_(ss).filter(u=>u.role==='tecnico');
  const lookup=Object.create(null),seen=Object.create(null),platforms=Object.create(null);
  users.forEach(u=>lookup[u.id]=u);
  const sessions=ss.getSheetByName(AUTH_SESSIONS_SHEET);
  if(sessions&&sessions.getLastRow()>1){
    sessions.getRange(2,1,sessions.getLastRow()-1,8).getValues().forEach(r=>{
      const id=String(r[1]||''),expiry=when(r[6]),at=when(r[5]);
      if(!Object.prototype.hasOwnProperty.call(lookup,id)||
         r[7]===true||String(r[7]).toLowerCase()==='true'||
         !expiry||Date.parse(expiry)<=now||!at||Date.parse(at)>now+60000)return;
      if(!seen[id]||seen[id]<at)seen[id]=at;
      const platform=String(r[3]||'').toLowerCase();
      if(platform==='android'||platform==='windows'){
        if(!platforms[id])platforms[id]=Object.create(null);
        platforms[id][platform]=true;
      }
    });
  }
  const techs=users.map(u=>{
    const lastSeen=seen[u.id]||'',lastLogin=when(u.lastLoginAt);
    const last=lastSeen||lastLogin;
    const minutes=last?Math.max(0,Math.floor((now-Date.parse(last))/60000)):null;
    const recent=u.active===true&&lastSeen&&now-Date.parse(lastSeen)<=900000;
    return {id:u.id,name:String(u.name||'Técnico').slice(0,120),
      email:String(u.email||'').slice(0,150),active:u.active===true,
      lastSeenAt:lastSeen,lastLoginAt:lastLogin,lastActivityAt:last,
      minutesSinceActivity:minutes,status:!u.active?'Conta inativa':
       recent?'Ativo recentemente':last?'Ausente':'Sem registro',
      platforms:platforms[u.id]?Object.keys(platforms[u.id]):[]};
  }).sort((a,b)=>String(b.lastActivityAt).localeCompare(String(a.lastActivityAt)));
  const logs=ss.getSheetByName(AUTH_AUDIT_SHEET),events=[];
  if(logs&&logs.getLastRow()>1){
    const last=logs.getLastRow(),start=Math.max(2,last-9999);
    const rows=logs.getRange(start,1,last-start+1,10).getValues();
    const permitted=['login','logout','record_sync','record_delete'];
    const types=['inspections','non_conformities','action_plans','sst_records',
      'evidence_photos','completion_photos','training_controls','workers','sectors','worksites'];
    for(let i=rows.length-1;i>=0&&events.length<limit;i--){
      const r=rows[i],id=String(r[1]||''),at=when(r[0]),action=String(r[3]||'');
      if(!Object.prototype.hasOwnProperty.call(lookup,id)||!at||
         Date.parse(at)<minimum||Date.parse(at)>now+60000||
         permitted.indexOf(action)<0)continue;
      const entity=String(r[4]||'');
      if((action==='record_sync'||action==='record_delete')&&types.indexOf(entity)<0)continue;
      events.push({at:at,userId:id,userName:String(lookup[id].name||'Técnico').slice(0,120),
        action:action,entityType:entity,companyId:String(r[6]||'').slice(0,150),
        platform:String(r[8]||'').slice(0,25)});
    }
  }
  return {ok:true,generatedAt:new Date(now).toISOString(),technicians:techs,events:events,
    summary:{technicians:techs.length,recent:techs.filter(x=>x.status==='Ativo recentemente').length},
    info:'Status aproximado pela última chamada autenticada. Histórico somente de registros sincronizados.'};
}
/** A rota technician_supervision_v1 no Code.gs deve ser homologada separadamente. */