// Extensões comerciais do Gestão EPI.
// Este arquivo complementa Code.gs sem alterar o núcleo já estável.

var GESTAO_EPI_AI_WORKER_DEFAULT_URL = 'https://script.google.com/macros/s/AKfycbxNG-wU-jZMKMR2cb1nR9OUd31GSUpGM0FIEagZEUP7sAHxkahLDuJ6T3wZvEe9rm6WrQ/exec';
var __gestaoEpiBaseDoPost = doPost;

doPost = function(e) {
  try {
    var request = JSON.parse((e.postData && e.postData.contents) || '{}');
    var action = String(request.action || '');

    if (action === 'tenant_ai_assistant') {
      return jsonResponse_(commercialTenantAiAssistantExt_(request));
    }
    if (action === 'master_list_companies') {
      return jsonResponse_(commercialMasterListCompaniesExt_(request));
    }
    if (action === 'master_create_company') {
      return jsonResponse_(commercialMasterCreateCompanyExt_(request));
    }
    if (action === 'master_create_tenant') {
      var created = masterCreateTenant_(request);
      if (created && created.ok && created.tenant && created.tenant.id) {
        try {
          commercialEnsurePrimaryCompanyExt_(created.tenant.id, request.name, request.cnpj);
        } catch (_) {}
      }
      return jsonResponse_(created);
    }
  } catch (error) {
    return jsonResponse_({ok:false,message:String(error)});
  }
  return __gestaoEpiBaseDoPost(e);
};

function commercialMasterListCompaniesExt_(request) {
  var session = commercialValidateToken_(request.authToken,'master');
  if (!session.ok) return session;
  var tenant = commercialTenantById_(request.tenantId);
  if (!tenant) return {ok:false,message:'Cliente não encontrado.'};
  var snapshot = commercialReadTenantSnapshot_(tenant);
  return {ok:true,companies:snapshot.app.companies || []};
}

function commercialMasterCreateCompanyExt_(request) {
  var session = commercialValidateToken_(request.authToken,'master');
  if (!session.ok) return session;
  var tenant = commercialTenantById_(request.tenantId);
  if (!tenant) return {ok:false,message:'Cliente não encontrado.'};
  var name = String(request.name || '').trim();
  var cnpj = String(request.cnpj || '').trim();
  if (!name) return {ok:false,message:'Informe o nome da empresa.'};

  var lock = LockService.getScriptLock();
  lock.waitLock(12000);
  try {
    var snapshot = commercialReadTenantSnapshot_(tenant);
    var companies = snapshot.app.companies || [];
    var normalizedName = commercialCompanyNormExt_(name);
    var cnpjDigits = cnpj.replace(/\D/g,'');
    var duplicate = companies.find(function(c) {
      var sameCnpj = cnpjDigits && String(c.cnpj || '').replace(/\D/g,'') === cnpjDigits;
      var sameName = commercialCompanyNormExt_(c.name) === normalizedName;
      return sameCnpj || sameName;
    });
    if (duplicate) return {ok:true,company:duplicate,companies:companies,message:'Essa empresa já está cadastrada.'};

    var now = new Date().toISOString();
    var company = {
      id:'c_' + Utilities.getUuid(),
      name:name,
      cnpj:cnpj,
      createdAt:now,
      updatedAt:now,
      source:'painel-mestre'
    };
    companies.push(company);
    snapshot.app.companies = companies;
    snapshot.revision = Number(snapshot.revision || 0) + 1;
    snapshot.updatedAt = now;
    commercialWriteTenantSnapshot_(tenant,snapshot);
    return {ok:true,company:company,companies:companies,message:'Empresa cadastrada no Gestão EPI.'};
  } catch (error) {
    return {ok:false,message:'Falha ao cadastrar empresa: ' + String(error)};
  } finally {
    lock.releaseLock();
  }
}

function commercialEnsurePrimaryCompanyExt_(tenantId,name,cnpj) {
  var tenant = commercialTenantById_(tenantId);
  if (!tenant) return null;
  var snapshot = commercialReadTenantSnapshot_(tenant);
  if ((snapshot.app.companies || []).length) return snapshot.app.companies[0];
  var now = new Date().toISOString();
  var company = {
    id:'c_' + Utilities.getUuid(),
    name:String(name || tenant.name || '').trim() || tenant.name,
    cnpj:String(cnpj || tenant.cnpj || '').trim(),
    createdAt:now,
    updatedAt:now,
    source:'painel-mestre'
  };
  snapshot.app.companies = [company];
  snapshot.revision = Number(snapshot.revision || 0) + 1;
  snapshot.updatedAt = now;
  commercialWriteTenantSnapshot_(tenant,snapshot);
  return company;
}

function commercialCompanyNormExt_(value) {
  return String(value || '').trim().toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/\s+/g,' ');
}

function commercialTenantAiAssistantExt_(request) {
  var session = commercialRequireTenantRole_(request.authToken,['admin','campo']);
  if (!session.ok) return session;

  var payload = request.payload && typeof request.payload === 'object' ? request.payload : {};
  if (String(payload.mode || '') !== 'employee_pdf_import') {
    return {ok:false,message:'Modo de IA não suportado.'};
  }

  var documentData = String(payload.document || '');
  if (!/^data:application\/pdf;base64,/i.test(documentData)) {
    return {ok:false,message:'Envie um PDF válido para a IA.'};
  }
  if (documentData.length > 18000000) {
    return {ok:false,message:'O PDF é muito grande para análise por IA.'};
  }

  var props = PropertiesService.getScriptProperties();
  var workerKey = String(props.getProperty('GESTAO_EPI_AI_WORKER_KEY') || props.getProperty('AUDITAR_SYNC_KEY') || '').trim();
  var workerUrl = String(props.getProperty('GESTAO_EPI_AI_WORKER_URL') || GESTAO_EPI_AI_WORKER_DEFAULT_URL).trim();
  var workerFailure = null;

  if (workerKey && workerUrl) {
    try {
      var proxied = commercialProxyAiWorkerExt_(workerUrl,workerKey,payload);
      if (proxied && proxied.ok) return proxied;
      workerFailure = {
        ok:false,
        code:String(proxied && proxied.code || 'AI_WORKER_REJECTED'),
        workerConfigured:true,
        message:'A chave da IA foi encontrada na Central, mas o serviço de IA respondeu: ' + String(proxied && proxied.message || 'não foi possível concluir a análise do PDF.')
      };
    } catch (workerError) {
      workerFailure = {
        ok:false,
        code:'AI_WORKER_UNREACHABLE',
        workerConfigured:true,
        message:'A chave da IA foi encontrada na Central, mas não foi possível acessar o serviço de IA: ' + String(workerError)
      };
    }
  }

  var geminiKey = String(props.getProperty('GEMINI_API_KEY') || props.getProperty('GOOGLE_AI_API_KEY') || '').trim();
  if (geminiKey) {
    var geminiResult = commercialGeminiEmployeePdfExt_(documentData,geminiKey,props);
    if (geminiResult && geminiResult.ok) return geminiResult;
    if (!workerFailure) return geminiResult;
  }

  if (workerFailure) return workerFailure;

  return {
    ok:false,
    code:'AI_SERVER_NOT_CONFIGURED',
    workerConfigured:false,
    message:'A Central não encontrou a configuração da IA. Verifique somente se a propriedade GESTAO_EPI_AI_WORKER_KEY existe neste projeto do Apps Script.'
  };
}

function commercialProxyAiWorkerExt_(url,key,payload) {
  var response = UrlFetchApp.fetch(url,{
    method:'post',
    contentType:'text/plain;charset=utf-8',
    payload:JSON.stringify({action:'ai_assistant',syncKey:key,payload:payload}),
    muteHttpExceptions:true,
    followRedirects:true
  });

  var status = Number(response.getResponseCode() || 0);
  var text = response.getContentText('UTF-8');
  var data;

  try {
    data = JSON.parse(text || '{}');
  } catch (_) {
    throw new Error('O serviço de IA retornou resposta inválida' + (status ? ' (HTTP ' + status + ')' : '') + '.');
  }

  if (status < 200 || status >= 300) {
    return {
      ok:false,
      code:'AI_WORKER_HTTP_' + status,
      message:String(data && data.message || ('HTTP ' + status))
    };
  }

  return data;
}

function commercialGeminiEmployeePdfExt_(documentData,key,props) {
  try {
    var base64 = documentData.substring(documentData.indexOf(',') + 1);
    var model = String(props.getProperty('GESTAO_EPI_GEMINI_MODEL') || 'gemini-2.5-flash').trim();
    var prompt = [
      'Analise este PDF de funcionários de uma empresa.',
      'Extraia somente pessoas/colaboradores reais da listagem.',
      'Para cada colaborador retorne: name, cpf, reg (matrícula/registro), role (cargo/função) e sector (setor).',
      'Não invente dados. Quando um campo não existir, use string vazia.',
      'Ignore cabeçalhos, códigos de lotação, nomes de setores isolados e linhas que não sejam pessoas.',
      'Retorne SOMENTE JSON válido neste formato:',
      '{"employees":[{"name":"","cpf":"","reg":"","role":"","sector":""}]}'
    ].join('\n');
    var body = {
      contents:[{role:'user',parts:[
        {text:prompt},
        {inlineData:{mimeType:'application/pdf',data:base64}}
      ]}],
      generationConfig:{temperature:0.1,responseMimeType:'application/json'}
    };
    var url = 'https://generativelanguage.googleapis.com/v1beta/models/' + encodeURIComponent(model) + ':generateContent?key=' + encodeURIComponent(key);
    var response = UrlFetchApp.fetch(url,{
      method:'post',
      contentType:'application/json',
      payload:JSON.stringify(body),
      muteHttpExceptions:true
    });
    var status = response.getResponseCode();
    var raw = response.getContentText('UTF-8');
    if (status < 200 || status >= 300) {
      var apiError = '';
      try { apiError = JSON.parse(raw).error.message || ''; } catch (_) {}
      throw new Error(apiError || ('Serviço de IA retornou HTTP ' + status));
    }
    var parsed = JSON.parse(raw || '{}');
    var text = String(parsed.candidates && parsed.candidates[0] && parsed.candidates[0].content && parsed.candidates[0].content.parts && parsed.candidates[0].content.parts[0] && parsed.candidates[0].content.parts[0].text || '').trim();
    text = text.replace(/^```(?:json)?\s*/i,'').replace(/\s*```$/,'').trim();
    var result = JSON.parse(text || '{}');
    var employees = Array.isArray(result.employees) ? result.employees : [];
    employees = employees.map(function(e) {
      return {
        name:String(e && e.name || '').trim(),
        cpf:String(e && e.cpf || '').trim(),
        reg:String(e && (e.reg || e.registration || e.matricula) || '').trim(),
        role:String(e && (e.role || e.cargo || e.funcao) || '').trim(),
        sector:String(e && (e.sector || e.setor) || '').trim()
      };
    }).filter(function(e){return e.name;});
    return {ok:true,result:{employees:employees},provider:'gemini'};
  } catch (error) {
    return {ok:false,message:'A IA não conseguiu ler o PDF: ' + String(error)};
  }
}
