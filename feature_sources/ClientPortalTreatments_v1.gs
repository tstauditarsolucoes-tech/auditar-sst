/**
 * Auditar SST — Linha do tempo de tratativas V1.
 * Armazenamento ADITIVO: eventos imutaveis, separados de NCs, acoes, evidencias,
 * PDF, autenticação, sincronizacao e historico de vistoria.
 * O acesso é exclusivamente via sessao do Painel do Cliente.
 */
const CLIENT_TREATMENT_SHEET_V1='AUDITAR_TRATATIVAS_V1';

function clientTreatmentAuthorized_(token,companyId,topicId) {
  const actor=clientTreatmentActorV2_(token);
  const company=String(companyId||'').trim();
  const topic=String(topicId||'').trim();
  if(!actor)return {ok:false,code:'SESSION_INVALID',message:'Entre novamente.'};
  if(!company||company.length>200||!topic||topic.length>120||
      !userCanAccessCompany_(actor,company))
    return {ok:false,code:'ACCESS_DENIED',message:'Empresa ou assunto não autorizado.'};
  if(actor.role==='cliente'&&!clientPortalPermissions_(actor.clientPermissions).tratativas)
    return {ok:false,code:'ACCESS_DENIED',message:'Tratativas não habilitadas para esta conta.'};
  const snapshot=clientPortalFindSnapshot_(company);
  if(!snapshot)return {ok:false,code:'NO_PUBLISHED_COMPANY',message:'Empresa sem painel publicado.'};
  if(topic!=='GERAL') {
    const rows=clientPortalRows_(snapshot.payload,
      ['openNonConformities','nonConformities','ncs','ncRecords','nonConformityRows']);
    if(!rows.some(function(item){return item.id===topic;}))
      return {ok:false,code:'TOPIC_UNAVAILABLE',
        message:'Ocorrência não está publicada para esta empresa.'};
    if(actor.role==='cliente'&&!clientPortalPermissions_(actor.clientPermissions).naoConformidades)
      return {ok:false,code:'ACCESS_DENIED',message:'Ocorrência não liberada.'};
  }
  return {ok:true,actor:actor,companyId:company,topicId:topic};
}

function clientTreatmentSheetV1_() {
  const ss=ensureAuthStorage_();
  let sheet=ss.getSheetByName(CLIENT_TREATMENT_SHEET_V1);
  if(!sheet){
    sheet=ss.insertSheet(CLIENT_TREATMENT_SHEET_V1);
    sheet.appendRow(['company_id','topic_id','event_id','created_at',
      'user_id','role','event_json']);
  }
  return sheet;
}

function clientPortalTreatmentList(token,companyId,topicId) {
  const auth=clientTreatmentAuthorized_(token,companyId,topicId);
  if(!auth.ok)return auth;
  const sheet=clientTreatmentSheetV1_();
  const last=sheet.getLastRow();
  const rows=last<2?[]:sheet.getRange(2,1,last-1,7).getValues();
  const matching=rows.filter(function(row){
    return String(row[0])===auth.companyId&&String(row[1])===auth.topicId;
  });
  // Paginas mais recentes, mantendo sequencia de eventos e autores.
  const events=matching.slice(-150).map(function(row){
    let body={};
    try{body=JSON.parse(String(row[6]||'{}'));}catch(_){}
    return {
      id:String(row[2]||''),at:String(row[3]||''),
      author:body.author||'Participante',role:String(row[5]||''),
      type:body.type||'mensagem',message:body.message||'',
      responsible:body.responsible||'',dueDate:body.dueDate||'',
      decision:body.decision||'',actionId:body.actionId||''
    };
  });
  return {ok:true,companyId:auth.companyId,topicId:auth.topicId,
    events:events,total:matching.length,hasEarlier:matching.length>150,
    // Um parecer tecnicamente validado nao altera o PDF/NC de origem.
    sourcePreserved:true};
}

function clientPortalTreatmentPost(token,companyId,topicId,input) {
  const auth=clientTreatmentAuthorized_(token,companyId,topicId);
  if(!auth.ok)return auth;
  const item=input&&typeof input==='object'&&!Array.isArray(input)?input:{};
  const type=String(item.type||'mensagem').trim();
  const clientTypes=['mensagem','esclarecimento','proposta_prazo'];
  const staffTypes=['mensagem','resposta_tecnica','solicitar_verificacao',
    'revisao_tecnica','encaminhamento','reuniao','eficacia_confirmada','vinculo_acao'];
  const allowed=auth.actor.role==='cliente'?clientTypes:staffTypes;
  if(allowed.indexOf(type)<0)return {ok:false,code:'TYPE_NOT_ALLOWED',
    message:'Essa decisão exige avaliação técnica da Auditar.'};
  const message=String(item.message||'').trim();
  if(!message||message.length>1600||/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/.test(message))
    return {ok:false,code:'MESSAGE_INVALID',message:'Escreva uma mensagem de até 1600 caracteres.'};
  const responsible=String(item.responsible||'').trim();
  const dueDate=String(item.dueDate||'').trim();
  if(responsible.length>120||dueDate.length>10||
      (dueDate&&!/^\d{4}-\d{2}-\d{2}$/.test(dueDate)))
    return {ok:false,code:'INVALID_FIELDS',message:'Responsável ou prazo inválido.'};
  if(auth.actor.role==='cliente'&&responsible)
    return {ok:false,code:'TYPE_NOT_ALLOWED',message:'Responsável é definido pela equipe Auditar.'};
  if(auth.actor.role==='cliente'&&type!=='proposta_prazo'&&dueDate)
    return {ok:false,code:'TYPE_NOT_ALLOWED',message:'Prazo formal é definido na tratativa técnica.'};
  const decision=String(item.decision||'').trim();
  if(decision.length>80||(decision&&auth.actor.role==='cliente'))
    return {ok:false,code:'TYPE_NOT_ALLOWED'};
  const actionId=String(item.actionId||'').trim();
  if(actionId&&(type!=='vinculo_acao'||auth.actor.role==='cliente'||
      actionId.length>120||!/^[a-zA-Z0-9_-]+$/.test(actionId)))
    return {ok:false,code:'INVALID_ACTION_LINK',message:'Identificador de ação inválido.'};
  if(type==='vinculo_acao'&&!actionId)
    return {ok:false,code:'ACTION_REQUIRED',message:'Informe a referência da ação existente.'};
  const event={
    actionId:actionId,type:type,message:message,
    author:String(auth.actor.name||'Participante').slice(0,120),
    responsible:responsible,dueDate:dueDate,decision:decision
  };
  const lock=LockService.getScriptLock();
  lock.waitLock(20000);
  try{
    const sheet=clientTreatmentSheetV1_();
    // Idempotencia opcional para cliques repetidos/requisicoes com retry.
    const requestId=String(item.requestId||'').trim();
    if(!/^[a-zA-Z0-9_-]{8,100}$/.test(requestId))
      return {ok:false,code:'INVALID_REQUEST_ID',message:'Identificador da mensagem inválido.'};
    const id='treat_'+requestId;
    const last=sheet.getLastRow();
    const prior=last<2?[]:sheet.getRange(2,1,last-1,7).getValues();
    const existed=prior.find(function(row){return String(row[2])===id;});
    if(existed) {
      if(String(existed[0])!==auth.companyId||String(existed[1])!==auth.topicId||
         String(existed[4])!==String(auth.actor.id||'')){
        return {ok:false,code:'REQUEST_COLLISION'};
      }
      return {ok:true,id:id,duplicate:true};
    }
    // Limite de eventos por topico para evitar abuso e excesso de dados.
    if(prior.filter(function(row){return String(row[0])===auth.companyId&&
      String(row[1])===auth.topicId;}).length>=1500)
      return {ok:false,code:'TOPIC_LIMIT',message:'O histórico atingiu o limite de mensagens.'};
    const date=new Date().toISOString();
    sheet.appendRow([auth.companyId,auth.topicId,id,date,
      String(auth.actor.id||''),auth.actor.role,JSON.stringify(event)]);
    return {ok:true,id:id,at:date};
  } finally {lock.releaseLock();}
}

/** Permite TST no aplicativo com token nativo; cliente somente no portal. */
function clientTreatmentActorV2_(token) {
  const value=String(token||'').trim();
  if(!value)return null;
  const portal=clientPortalAuthorizedUser_(value);
  if(portal)return portal;
  const staff=authUserFromToken_(value,false);
  if(!staff||staff.active!==true||['admin','tecnico'].indexOf(staff.role)<0||
     staff.sessionPlatform==='client_portal')return null;
  return staff;
}

/**
 * Caixa de entrada: indicador de "aguardando resposta" pelo ultimo autor.
 * Nao representa leitura confirmada nem envia notificacoes push.
 */
function clientPortalTreatmentInbox(token,companyFilter) {
  const actor=clientTreatmentActorV2_(token);
  if(!actor)return {ok:false,code:'SESSION_INVALID',message:'Entre novamente.'};
  const filter=String(companyFilter||'').trim();
  if(filter&&(!userCanAccessCompany_(actor,filter)||
    !clientPortalFindSnapshot_(filter)))
    return {ok:false,code:'ACCESS_DENIED'};
  if(actor.role==='cliente'&&!clientPortalPermissions_(actor.clientPermissions).tratativas)
    return {ok:false,code:'ACCESS_DENIED'};
  const sheet=clientTreatmentSheetV1_();
  const last=sheet.getLastRow();
  // Janela limitada; constatações e PDFs nunca são alterados.
  const start=Math.max(2,last-4999);
  const rows=last<2?[]:sheet.getRange(start,1,last-start+1,7).getValues();
  const byTopic={};
  rows.forEach(function(row){
    const company=String(row[0]||''),topic=String(row[1]||'');
    if(filter&&company!==filter)return;
    if(!company||!topic||!userCanAccessCompany_(actor,company))return;
    const key=company+'|'+topic;
    let body={};
    try{body=JSON.parse(String(row[6]||'{}'));}catch(_){return;}
    if(!byTopic[key])byTopic[key]={companyId:company,topicId:topic,
      total:0,events:[],updatedAt:'',lastRole:'',lastMessage:'',
      lastType:'',lastAuthor:'',dueDate:'',actionId:''};
    const rec=byTopic[key];rec.total++;
    const at=String(row[3]||'');
    rec.events.push({at:at,role:String(row[5]||''),type:String(body.type||''),
      dueDate:String(body.dueDate||''),actionId:String(body.actionId||'')});
    if(at>=rec.updatedAt){
      rec.updatedAt=at;
      rec.lastRole=String(row[5]||'');
      rec.lastType=String(body.type||'');
      rec.lastMessage=String(body.message||'').slice(0,240);
      rec.lastAuthor=String(body.author||'').slice(0,120);
    }
  });
  const cache={};
  function authorized(company,topic) {
    const key=company+'|'+topic;
    if(!cache[company]){
      const snapshot=clientPortalFindSnapshot_(company);
      if(!snapshot){cache[company]={eligible:false,names:{}};}
      else{
        const titles={GERAL:'Conversa geral'};
        const records=clientPortalRows_(snapshot.payload,
          ['openNonConformities','nonConformities','ncs','ncRecords','nonConformityRows']);
        records.forEach(function(row){if(row.id)titles[row.id]=(row.title||row.description||row.id).slice(0,180);});
        cache[company]={eligible:true,names:titles,
          companyName:String((snapshot.payload.company||{}).name||'Empresa').slice(0,140)};
      }
    }
    const data=cache[company];
    if(!data.eligible||!Object.prototype.hasOwnProperty.call(data.names,topic))return null;
    if(actor.role==='cliente'&&topic!=='GERAL'&&
      !clientPortalPermissions_(actor.clientPermissions).naoConformidades)return null;
    return {title:data.names[topic],companyName:data.companyName};
  }
  const now=new Date().toISOString().slice(0,10);
  const result=[];
  Object.keys(byTopic).forEach(function(key){
    const rec=byTopic[key],visible=authorized(rec.companyId,rec.topicId);
    if(!visible)return;
    const finished=rec.lastType==='eficacia_confirmada';
    const awaiting=finished?'Concluída':
      rec.lastRole==='cliente'?'Aguardando Auditar':
      rec.lastType==='solicitar_verificacao'?'Aguardando verificação':'Aguardando cliente';
    for(let i=rec.events.length-1;i>=0;i--){
      const ev=rec.events[i];
      if(!rec.dueDate&&ev.dueDate&&ev.role!=='cliente')rec.dueDate=ev.dueDate;
      if(!rec.actionId&&ev.actionId)rec.actionId=ev.actionId;
    }
    result.push({companyId:rec.companyId,companyName:visible.companyName,
      topicId:rec.topicId,title:visible.title,updatedAt:rec.updatedAt,
      lastType:rec.lastType,lastMessage:rec.lastMessage,lastAuthor:rec.lastAuthor,
      lastRole:rec.lastRole,status:awaiting,events:rec.total,
      dueDate:rec.dueDate,actionId:rec.actionId,
      overdue:!finished&&rec.dueDate&&rec.dueDate<now});
  });
  result.sort(function(a,b){return b.updatedAt.localeCompare(a.updatedAt);});
  const all=result.length;
  return {ok:true,threads:result.slice(0,120),total:all,
    truncated:all>120||last>5001,
    summary:{
      awaitingAuditar:result.filter(function(x){return x.status==='Aguardando Auditar';}).length,
      awaitingClient:result.filter(function(x){return x.status==='Aguardando cliente';}).length,
      awaitingVerification:result.filter(function(x){return x.status==='Aguardando verificação';}).length,
      overdue:result.filter(function(x){return x.overdue;}).length
    }};
}

/** Rota isolada para o aplicativo (Android/Windows), sem modificar device_sync. */
function clientTreatmentAppV2_(request) {
  const r=request&&typeof request==='object'?request:{};
  const token=String(r.authToken||'');
  const user=clientTreatmentActorV2_(token);
  if(!user||['admin','tecnico'].indexOf(user.role)<0)
    return {ok:false,code:'ACCESS_DENIED'};
  const mode=String(r.mode||'inbox');
  if(mode==='inbox')return clientPortalTreatmentInbox(token,r.companyId);
  if(mode==='list')return clientPortalTreatmentList(token,r.companyId,r.topicId);
  if(mode==='post')return clientPortalTreatmentPost(token,r.companyId,r.topicId,r.record);
  return {ok:false,code:'INVALID_MODE'};
}
