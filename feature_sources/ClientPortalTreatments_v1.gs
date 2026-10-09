/**
 * Auditar SST — Linha do tempo de tratativas V1.
 * Armazenamento ADITIVO: eventos imutaveis, separados de NCs, acoes, evidencias,
 * PDF, autenticação, sincronizacao e historico de vistoria.
 * O acesso é exclusivamente via sessao do Painel do Cliente.
 */
const CLIENT_TREATMENT_SHEET_V1='AUDITAR_TRATATIVAS_V1';

function clientTreatmentAuthorized_(token,companyId,topicId) {
  const actor=clientPortalAuthorizedUser_(token);
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
      decision:body.decision||''
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
    'revisao_tecnica','encaminhamento','reuniao','eficacia_confirmada'];
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
  const event={
    type:type,message:message,
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