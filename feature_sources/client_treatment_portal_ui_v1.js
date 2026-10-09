
/* Client treatment timeline. All displayed content uses textContent. */
function treatmentTimelineV1(company,topicId,title){
 const block=document.createElement('details');
 block.className='auditar-tratativa';
 block.dataset.portalKey=company.id+':tratativas:'+topicId;
 block.append(text('summary',title));
 const content=text('div','','tratativa-content');
 const status=text('p','Abra para consultar a conversa.','muted');
 const history=text('div','','tratativa-events');
 const form=document.createElement('form');form.className='tratativa-form';
 const typeLabel=text('label','Tipo de registro');const type=document.createElement('select');
 const client=current.user.role==='cliente';
 const options=client?
  [['mensagem','Mensagem'],['esclarecimento','Esclarecimento da empresa'],
   ['proposta_prazo','Propor prazo']]:
  [['mensagem','Mensagem'],['resposta_tecnica','Parecer da Auditar'],
   ['solicitar_verificacao','Solicitar verificação'],['revisao_tecnica','Revisão técnica'],
   ['encaminhamento','Encaminhamento/Plano de ação'],['reuniao','Registro de reunião'],
   ['eficacia_confirmada','Eficácia verificada'],
   ['vinculo_acao','Vincular ação existente']];
 options.forEach(option=>{const item=document.createElement('option');
   item.value=option[0];item.textContent=option[1];type.append(item);});
 const noteLabel=text('label','Mensagem ou esclarecimento');
 const note=document.createElement('textarea');note.required=true;note.maxLength=1600;
 note.rows=3;note.placeholder=client?
  'Explique o contexto ou proponha uma verificação...':
  'Registre a resposta técnica, decisão ou encaminhamento...';
 const extra=text('div','','tratativa-extras');
 const responsible=document.createElement('input');responsible.maxLength=120;
 responsible.placeholder='Responsável pelo encaminhamento (opcional)';
 const due=document.createElement('input');due.type='date';
 const actionId=document.createElement('input');actionId.maxLength=120;
 actionId.placeholder='ID da ação já cadastrada';
 const actionLabel=text('label','Referência da ação existente');
 const verification=document.createElement('select');
 [['vistoria_in_loco','Visita presencial'],['teste_funcional','Teste funcional'],
 ['evidencia_analisada','Evidência revisada'],['documental','Documentos analisados']].forEach(x=>{
  const o=document.createElement('option');o.value=x[0];o.textContent=x[1];verification.append(o);
 });
 const verifyLabel=text('label','Como foi verificada a eficácia?');
 const responsibleLabel=text('label','Responsável');
 const dueLabel=text('label',client?'Prazo proposto':'Prazo da ação');
 if(!client){extra.append(responsibleLabel,responsible);}
 extra.append(dueLabel,due);
 if(!client)extra.append(actionLabel,actionId,verifyLabel,verification);
 const send=text('button','Registrar na linha do tempo');send.type='submit';
 const notice=text('p','','muted');notice.setAttribute('role','status');
 form.append(typeLabel,type,noteLabel,note,extra,send,notice);
 type.onchange=()=>{
  due.disabled=client&&type.value!=='proposta_prazo';
  actionId.hidden=actionLabel.hidden=type.value!=='vinculo_acao';
  verifyLabel.hidden=verification.hidden=type.value!=='eficacia_confirmada';
 };
 type.onchange();
 const quick=text('div','','tratativa-quick');
 const templates=client?
  [['esclarecimento','Esclarecer','Sobre a constatação, informamos que: '],
   ['proposta_prazo','Propor prazo','Propomos o prazo indicado para esta providência.'],
   ['mensagem','Solicitar reunião','Solicitamos reunião para alinhamento do assunto.']]:
  [['solicitar_verificacao','Pedir conferência','Solicitamos verificar o funcionamento no local e encaminhar o resultado.'],
   ['reuniao','Registrar reunião','Participantes: \nDecisões: \nResponsáveis: \nPrazos: '],
   ['resposta_tecnica','Parecer técnico','Após analisar o esclarecimento, registramos: ']];
 templates.forEach(x=>{
  const b=text('button',x[1],'secondary');b.type='button';
  b.onclick=()=>{type.value=x[0];type.onchange();note.value=x[2];note.focus();};
  quick.append(b);
 });
 content.append(status,history,quick,form);
 if(topicId!=='GERAL'){
  const nav=text('div','','tratativa-quick');
  if(client&&company.permissions.enviarEvidencia){
    const attach=text('button','Enviar foto da correção','secondary');attach.type='button';
    attach.onclick=()=>showEvidenceForm(content,company.id,topicId,attach);
    nav.append(attach);
  }
  const plan=text('button','Consultar plano de ação','secondary');plan.type='button';
  plan.onclick=()=>{
    const target=document.querySelector('details[data-portal-key="'+company.id+':plan"]');
    if(target){target.open=true;target.scrollIntoView({behavior:'smooth',block:'start'});}
    else status.textContent='Nenhum plano de ação publicado para esta empresa.';
  };
  nav.append(plan);content.append(nav);
 }
 block.append(content);
 let loading=false,loaded=false;
 function refresh(){
  if(loading)return;
  loading=true;status.textContent='Consultando linha do tempo...';
  const session=token;
  call('clientPortalTreatmentList',[session,company.id,topicId],res=>{
   loading=false;if(session!==token)return;
   history.replaceChildren();
   if(!res||!res.ok){status.textContent=res&&res.message||'Não foi possível consultar.';return;}
   loaded=true;
   const events=res.events||[];
   status.textContent=events.length?
     (events.length+' registros'+(res.hasEarlier?' — exibindo os 150 últimos':'')):
     'Ainda não há mensagens. Inicie a conversa abaixo.';
   events.forEach(ev=>{
    const row=text('article','','tratativa-event');
    const heading=text('div','','tratativa-event-head');
    heading.append(text('b',ev.author||'Participante'),
      text('small',(ev.role==='cliente'?'Empresa':'Auditar')+' · '+formatPortalDate(ev.at)),
      text('span',(ev.type||'mensagem').replaceAll('_',' '),'tratativa-tag'));
    row.append(heading,text('p',ev.message||''));
    if(ev.actionId)row.append(text('small','Ação vinculada: '+ev.actionId,'muted'));
    if(ev.responsible||ev.dueDate)row.append(text('small',
      [ev.responsible?'Responsável: '+ev.responsible:'',
       ev.dueDate?'Prazo: '+ev.dueDate:''].filter(Boolean).join(' · '),'muted'));
    history.append(row);
   });
  },err=>{loading=false;status.textContent=err;});
 }
 block.addEventListener('toggle',()=>{if(block.open&&!loaded)refresh();});
 form.onsubmit=event=>{
  event.preventDefault();
  if(send.disabled||!note.value.trim())return;
  send.disabled=true;notice.textContent='Registrando...';
  const requestId='portal_'+Date.now().toString(36)+'_'+Math.random().toString(36).slice(2,13);
  const payload={type:type.value,message:note.value.trim(),requestId,
    dueDate:due.disabled?'':due.value,
    responsible:client?'':responsible.value.trim(),
    actionId:client?'':actionId.value.trim(),
    verificationMethod:client?'':verification.value};
  const session=token;
  call('clientPortalTreatmentPost',[session,company.id,topicId,payload],res=>{
   send.disabled=false;if(session!==token)return;
   if(!res||!res.ok){notice.textContent=res&&res.message||'Registro não confirmado.';return;}
   note.value='';due.value='';responsible.value='';actionId.value='';
   notice.textContent='Registro incluído no histórico da empresa.';
   refresh();
  },err=>{send.disabled=false;notice.textContent=err;});
 };
 return block;
}
function renderTreatmentHubV1(company) {
 if(!company.permissions||!company.permissions.tratativas)return null;
 const hub=text('section','','tratativa-hub');
 hub.append(text('div','COMUNICAÇÃO E TRATATIVAS','section-eyebrow'),
   text('h3','Linha do tempo com a Auditar'),
   text('p','Converse sobre cada ocorrência sem perder as decisões e os prazos. '
     +'O relatório original permanece intacto; situações de risco exigem atenção imediata.',
     'muted'));
 hub.append(treatmentTimelineV1(company,'GERAL','Comunicação geral da empresa'));
 if(company.permissions.naoConformidades) {
   const cases=(company.nonConformities||[]).filter(row=>row.id);
   const seen=new Set();
   cases.forEach(row=>{
     if(seen.has(row.id))return;seen.add(row.id);
     hub.append(treatmentTimelineV1(company,row.id,
       (row.title||row.description||'Não conformidade').slice(0,140)));
   });
 }
 return hub;
}

/* Caixa de entrada e indicadores de respostas, por conta autenticada. */
function renderTreatmentInboxV2(){
 if(!current)return;
 let dest=$('treatmentInboxV2');
 if(!dest){dest=text('section','','panel');dest.id='treatmentInboxV2';
  $('companies').parentNode.insertBefore(dest,$('companies'));}
 dest.replaceChildren(text('h2','Caixa de entrada · Tratativas'));
 const info=text('p','Consultando atualizações...','muted');dest.append(info);
 const holder=text('div','','tratativa-inbox-list');dest.append(holder);
 const session=token;
 call('clientPortalTreatmentInbox',[session,''],res=>{
  if(token!==session)return;
  if(!res||!res.ok){info.textContent=res&&res.message||'Não foi possível consultar as tratativas.';return;}
  const sum=res.summary||{};
  info.textContent='Aguardando Auditar: '+(sum.awaitingAuditar||0)+
   ' · Aguardando cliente: '+(sum.awaitingClient||0)+
   ' · Verificação: '+(sum.awaitingVerification||0)+
   ' · Em atraso: '+(sum.overdue||0);
  holder.replaceChildren();
  const list=(res.threads||[]).slice(0,30);
  if(!list.length){holder.append(text('p','Nenhuma conversa iniciada.','muted'));return;}
  list.forEach(item=>{
   const row=text('button','','secondary tratativa-inbox-entry');row.type='button';
   row.append(text('b',(item.companyName||'Empresa')+' · '+(item.title||'Conversa')),
     text('small',(item.status||'')+(item.overdue?' • PRAZO VENCIDO':'')+
       (item.lastMessage?' — '+item.lastMessage:'')));
   row.onclick=()=>{
    const key=item.companyId+':tratativas:'+item.topicId;
    const target=[...document.querySelectorAll('details[data-portal-key]')]
      .find(x=>x.dataset.portalKey===key);
    if(target){target.open=true;target.scrollIntoView({behavior:'smooth',block:'start'});}
    else info.textContent='Conversa não liberada neste painel. Atualize a empresa.';
   };holder.append(row);
  });
 },err=>{info.textContent=err;});
}
