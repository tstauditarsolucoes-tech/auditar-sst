/**
 * Administração segura da IA do SST Gestão.
 * A chave é recebida apenas pelo app Chave Mestre e armazenada em ScriptProperties.
 * A chave nunca é devolvida ao cliente.
 */
function sstGestaoAiStatus_() {
  const props = PropertiesService.getScriptProperties();
  const configured = String(props.getProperty('GEMINI_API_KEY') || '').trim() !== '';
  const model = String(props.getProperty('SST_GESTAO_AI_MODEL') || 'gemini-2.5-flash').trim();
  return {ok:true, configured:configured, model:model};
}

function sstGestaoAiConfigure_(request) {
  const props = PropertiesService.getScriptProperties();
  const apiKey = String(request && request.apiKey || '').trim();
  const model = String(request && request.model || 'gemini-2.5-flash').trim() || 'gemini-2.5-flash';

  if (!apiKey && !String(props.getProperty('GEMINI_API_KEY') || '').trim()) {
    return {ok:false, message:'Informe a chave da Gemini API.'};
  }
  if (apiKey) {
    if (apiKey.length < 20) return {ok:false, message:'A chave informada parece inválida.'};
    props.setProperty('GEMINI_API_KEY', apiKey);
  }
  props.setProperty('SST_GESTAO_AI_MODEL', model);
  return sstGestaoAiStatus_();
}

function sstGestaoAiTest_() {
  const status = sstGestaoAiStatus_();
  if (!status.configured) {
    return {ok:false, code:'AI_NOT_CONFIGURED', message:'Configure a chave Gemini no app Chave Mestre.'};
  }
  if (typeof runAiAssistant_ !== 'function') {
    return {ok:false, message:'Assistente IA não está disponível nesta Central.'};
  }
  const result = runAiAssistant_({
    mode:'company_priorities',
    companyData:{
      empresa:'Teste SST Gestão',
      conformidade:90,
      naoConformidadesAbertas:1,
      acoesVencidas:0,
      treinamentosVencidos:0
    }
  });
  if (!result || result.ok !== true) return result || {ok:false,message:'Teste de IA sem resposta.'};
  return {ok:true, configured:true, model:status.model, message:'Assistente IA respondeu corretamente.'};
}
