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
  var mode = String(payload.mode || '');
  var props = PropertiesService.getScriptProperties();
  var geminiKey = String(props.getProperty('GEMINI_API_KEY') || props.getProperty('GOOGLE_AI_API_KEY') || '').trim();

  if (mode === 'invoice_pdf_import') {
    var invoiceDoc = String(payload.document || '');
    if (!/^data:application\/pdf;base64,/i.test(invoiceDoc)) return {ok:false,message:'Envie um PDF válido da nota fiscal.'};
    if (invoiceDoc.length > 18000000) return {ok:false,message:'O PDF é muito grande para análise por IA.'};
    if (!geminiKey) return {ok:false,code:'AI_SERVER_NOT_CONFIGURED',message:'A IA do servidor ainda não está configurada para ler a nota fiscal.'};
    return commercialGeminiInvoicePdfExt_(invoiceDoc,geminiKey,props);
  }

  if (mode === 'ca_validate') {
    var caItems = Array.isArray(payload.items) ? payload.items.slice(0,20) : [];
    if (!caItems.length) return {ok:true,result:{checks:[]},provider:'gemini-search'};
    if (!geminiKey) return {ok:false,code:'AI_SERVER_NOT_CONFIGURED',message:'A IA do servidor ainda não está configurada para consultar CA.'};
    return commercialGeminiCaValidateExt_(caItems,geminiKey,props);
  }

  if (mode !== 'employee_pdf_import') {
    return {ok:false,message:'Modo de IA não suportado.'};
  }

  var documentData = String(payload.document || '');
  if (!/^data:application\/pdf;base64,/i.test(documentData)) {
    return {ok:false,message:'Envie um PDF válido para a IA.'};
  }
  if (documentData.length > 18000000) {
    return {ok:false,message:'O PDF é muito grande para análise por IA.'};
  }

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

function commercialGeminiApiJsonExt_(body,key,model) {
  var url = 'https://generativelanguage.googleapis.com/v1beta/models/' + encodeURIComponent(model) + ':generateContent?key=' + encodeURIComponent(key);
  var response = UrlFetchApp.fetch(url,{
    method:'post',
    contentType:'application/json',
    payload:JSON.stringify(body),
    muteHttpExceptions:true
  });
  var status = Number(response.getResponseCode() || 0);
  var raw = response.getContentText('UTF-8');
  if (status < 200 || status >= 300) {
    var apiError = '';
    try { apiError = JSON.parse(raw).error.message || ''; } catch (_) {}
    throw new Error(apiError || ('Serviço de IA retornou HTTP ' + status));
  }
  var parsed = JSON.parse(raw || '{}');
  var text = String(parsed.candidates && parsed.candidates[0] && parsed.candidates[0].content && parsed.candidates[0].content.parts && parsed.candidates[0].content.parts[0] && parsed.candidates[0].content.parts[0].text || '').trim();
  text = text.replace(/^```(?:json)?\s*/i,'').replace(/\s*```$/,'').trim();
  return {json:JSON.parse(text || '{}'),rawResponse:parsed};
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
    var result = commercialGeminiApiJsonExt_(body,key,model).json;
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

function commercialGeminiInvoicePdfExt_(documentData,key,props) {
  try {
    var base64 = documentData.substring(documentData.indexOf(',') + 1);
    var model = String(props.getProperty('GESTAO_EPI_GEMINI_MODEL') || 'gemini-2.5-flash').trim();
    var prompt = [
      'Analise este DANFE/NF-e de compra e extraia SOMENTE itens que sejam EPI (Equipamento de Proteção Individual).',
      'Ignore ferramentas, escovas, pincéis, materiais e outros produtos que não sejam EPI.',
      'Regra crítica: o código do produto NÃO é a quantidade. Leia a coluna QUANT para qty e a coluna UNID para unit.',
      'Mantenha o código do produto separado do nome.',
      'Extraia o número do CA exatamente como aparece na descrição. NUNCA invente um CA. Se não estiver impresso, use string vazia.',
      'Extraia tamanho/numeração quando existir, por exemplo M 8-9 ou NR.40.',
      'Extraia fabricante/marca apenas quando estiver claro no documento.',
      'Também extraia number, series, key, date, supplier e supplierCnpj da nota.',
      'Para cada item retorne code, name, ca, size, unit, qty, unitValue, total, manufacturer, isEpi e confidence de 0 a 1.',
      'Retorne SOMENTE JSON válido no formato:',
      '{"invoice":{"number":"","series":"","key":"","date":"","supplier":"","supplierCnpj":"","items":[{"code":"","name":"","ca":"","size":"","unit":"","qty":1,"unitValue":0,"total":0,"manufacturer":"","isEpi":true,"confidence":0.9}]}}'
    ].join('\n');
    var body = {
      contents:[{role:'user',parts:[{text:prompt},{inlineData:{mimeType:'application/pdf',data:base64}}]}],
      generationConfig:{temperature:0.05,responseMimeType:'application/json'}
    };
    var result = commercialGeminiApiJsonExt_(body,key,model).json;
    var invoice = result.invoice && typeof result.invoice === 'object' ? result.invoice : result;
    var items = Array.isArray(invoice.items) ? invoice.items : [];
    items = items.map(function(i) {
      return {
        code:String(i && i.code || '').trim(),
        name:String(i && i.name || '').trim(),
        ca:String(i && i.ca || '').replace(/\D/g,''),
        size:String(i && i.size || '').trim(),
        unit:String(i && i.unit || '').trim(),
        qty:Math.max(0,Number(i && i.qty || 0)),
        unitValue:Number(i && i.unitValue || 0),
        total:Number(i && i.total || 0),
        manufacturer:String(i && i.manufacturer || '').trim(),
        isEpi:i && i.isEpi !== false,
        confidence:Number(i && i.confidence || 0)
      };
    }).filter(function(i){return i.name && i.isEpi && i.qty > 0;});
    return {ok:true,result:{invoice:{number:String(invoice.number||'').trim(),series:String(invoice.series||'').trim(),key:String(invoice.key||'').replace(/\D/g,''),date:String(invoice.date||'').trim(),supplier:String(invoice.supplier||'').trim(),supplierCnpj:String(invoice.supplierCnpj||'').trim(),items:items}},provider:'gemini'};
  } catch (error) {
    return {ok:false,message:'A IA não conseguiu organizar a nota fiscal: ' + String(error)};
  }
}

function commercialGeminiCaValidateExt_(items,key,props) {
  try {
    var model = String(props.getProperty('GESTAO_EPI_GEMINI_MODEL') || 'gemini-2.5-flash').trim();
    var compact = items.map(function(i){return {ca:String(i && i.ca || '').replace(/\D/g,''),name:String(i && i.name || '').trim(),manufacturer:String(i && i.manufacturer || '').trim()};}).filter(function(i){return i.ca;});
    if (!compact.length) return {ok:true,result:{checks:[]},provider:'gemini-search'};
    var prompt = [
      'Consulte na internet os Certificados de Aprovação (CA) abaixo.',
      'Use como evidência SOMENTE fontes oficiais do Ministério do Trabalho e Emprego, especialmente caepi.trabalho.gov.br e gov.br/trabalho-e-emprego.',
      'Para found=true, o número do CA precisa estar confirmado em fonte oficial. Não use sites de fabricantes, lojas ou blogs como confirmação.',
      'Informe status como válido, vencido, cancelado ou desconhecido somente quando a fonte oficial permitir concluir.',
      'Retorne equipment, manufacturer e validity somente se estiverem confirmados. Não invente.',
      'Se não conseguir confirmar em fonte oficial, use found=false e status="não confirmado".',
      'Itens para consultar: ' + JSON.stringify(compact),
      'Retorne SOMENTE JSON válido:',
      '{"checks":[{"ca":"","found":true,"status":"válido","equipment":"","manufacturer":"","validity":"","sourceUrl":"https://caepi.trabalho.gov.br/..."}]}'
    ].join('\n');
    var body = {
      contents:[{role:'user',parts:[{text:prompt}]}],
      tools:[{google_search:{}}],
      generationConfig:{temperature:0}
    };
    var result = commercialGeminiApiJsonExt_(body,key,model).json;
    var checks = Array.isArray(result.checks) ? result.checks : [];
    checks = checks.map(function(c){
      var source = String(c && c.sourceUrl || '').trim();
      var official = /(^|\.)caepi\.trabalho\.gov\.br\b|(^|\.)gov\.br\b/i.test(source.replace(/^https?:\/\//i,'').split('/')[0]);
      return {
        ca:String(c && c.ca || '').replace(/\D/g,''),
        found:Boolean(c && c.found) && official,
        status:official ? String(c && c.status || 'confirmado').trim() : 'não confirmado',
        equipment:official ? String(c && c.equipment || '').trim() : '',
        manufacturer:official ? String(c && c.manufacturer || '').trim() : '',
        validity:official ? String(c && c.validity || '').trim() : '',
        sourceUrl:official ? source : 'https://caepi.trabalho.gov.br/internet/ConsultaCAInternet.aspx'
      };
    });
    return {ok:true,result:{checks:checks},provider:'gemini-search'};
  } catch (error) {
    return {ok:false,message:'Não foi possível confirmar os CA automaticamente: ' + String(error)};
  }
}
