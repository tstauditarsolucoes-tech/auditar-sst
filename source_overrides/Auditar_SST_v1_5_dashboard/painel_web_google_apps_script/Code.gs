const PANEL_SHEET = 'PainelDados';
const CIPA_ELECTIONS_SHEET = 'CipaEleicoes';
const CIPA_VOTERS_SHEET = 'CipaEleitores';
const CIPA_VOTES_SHEET = 'CipaVotos';
const EMAIL_LOG_SHEET = 'EmailEnvios';
const GEMINI_API_BASE_URL = 'https://generativelanguage.googleapis.com/v1beta/models/';
const DRIVE_ROOT_FOLDER = 'Auditar SST';
const DRIVE_MAX_REPORT_BYTES = 20 * 1024 * 1024;

function setupAuditar() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  if (!ss) throw new Error('Abra este script a partir de uma Planilha Google.');

  ensureSheet_(ss, PANEL_SHEET, [
    'token', 'company_id', 'company_name', 'active', 'updated_at', 'payload_json'
  ]);
  ensureSheet_(ss, CIPA_ELECTIONS_SHEET, [
    'token', 'election_id', 'company_id', 'company_name', 'title',
    'management_period', 'status', 'total_voters', 'updated_at', 'candidates_json', 'company_cnpj'
  ]);
  ensureSheet_(ss, CIPA_VOTERS_SHEET, [
    'election_token', 'voter_hash', 'used', 'identity_hash',
    'voter_id', 'name', 'role', 'sector'
  ]);
  ensureSheet_(ss, CIPA_VOTES_SHEET, [
    'election_token', 'ballot_id', 'candidate_id'
  ]);
  ensureSheet_(ss, EMAIL_LOG_SHEET, [
    'event_key', 'company_id', 'type', 'sent_at', 'recipients'
  ]);
  ensureDriveRootFolder_();

  const props = PropertiesService.getScriptProperties();
  props.setProperty('AUDITAR_SPREADSHEET_ID', ss.getId());
  let key = props.getProperty('AUDITAR_SYNC_KEY');
  if (!key) {
    key = Utilities.getUuid().replace(/-/g, '') + Utilities.getUuid().replace(/-/g, '');
    props.setProperty('AUDITAR_SYNC_KEY', key);
  }
  installAutomaticTrigger_();

  Logger.log('CHAVE DE SINCRONIZACAO: ' + key);
  return key;
}

function configurarGoogleDrive() {
  const folder = ensureDriveRootFolder_();
  Logger.log('PASTA DO GOOGLE DRIVE: ' + folder.getUrl());
  return folder.getId();
}

function configurarAssistenteIA(chaveApi, modelo) {
  const key = String(chaveApi || '').trim();
  if (!key) throw new Error('Informe uma chave válida da Gemini API.');
  const props = PropertiesService.getScriptProperties();
  props.setProperty('GEMINI_API_KEY', key);
  props.setProperty('AUDITAR_AI_MODEL', String(modelo || 'gemini-3.5-flash-lite').trim());
  Logger.log('Assistente IA configurado com segurança no Apps Script.');
  return true;
}

function removerConfiguracaoAssistenteIA() {
  const props = PropertiesService.getScriptProperties();
  props.deleteProperty('GEMINI_API_KEY');
  props.deleteProperty('AUDITAR_AI_MODEL');
  return true;
}

function verificarAssistenteIA() {
  const props = PropertiesService.getScriptProperties();
  const configured = String(props.getProperty('GEMINI_API_KEY') || '').trim() !== '';
  const model = String(props.getProperty('AUDITAR_AI_MODEL') || 'gemini-3.5-flash-lite');
  Logger.log(configured
    ? 'Assistente IA configurado. Modelo: ' + model
    : 'Assistente IA ainda não configurado.');
  return {configured: configured, model: model};
}

function testarAssistenteIA() {
  const status = verificarAssistenteIA();
  if (!status.configured) {
    throw new Error('Configure GEMINI_API_KEY nas propriedades do script antes do teste.');
  }

  const result = runAiAssistant_({
    mode: 'company_priorities',
    companyData: {
      empresa: 'Empresa de teste',
      conformidade: 78,
      naoConformidadesAbertas: 4,
      acoesVencidas: 1,
      treinamentosVencidos: 2
    }
  });

  if (!result.ok) {
    throw new Error(result.message || 'A IA não respondeu ao teste.');
  }
  Logger.log('TESTE DA IA CONCLUÍDO. Modelo: ' + result.model);
  Logger.log(JSON.stringify(result.result));
  return result;
}

function doPost(e) {
  try {
    const request = JSON.parse((e.postData && e.postData.contents) || '{}');
    const expectedKey = PropertiesService.getScriptProperties().getProperty('AUDITAR_SYNC_KEY');
    if (!expectedKey) return jsonResponse_({ok: false, message: 'Execute setupAuditar() primeiro.'});

    if (request.action === 'drive_connect') {
      if (request.syncKey !== expectedKey) return jsonResponse_({ok: false, message: 'Chave de sincronização inválida.'});
      return jsonResponse_(connectGoogleDrive_());
    }

    if (request.action === 'drive_upload') {
      if (request.syncKey !== expectedKey) return jsonResponse_({ok: false, message: 'Chave de sincronização inválida.'});
      return jsonResponse_(uploadReportToDrive_(request));
    }

    if (request.action === 'sync') {
      if (request.syncKey !== expectedKey) return jsonResponse_({ok: false, message: 'Chave de sincronização inválida.'});
      if (!request.payload) return jsonResponse_({ok: false, message: 'Payload ausente.'});
      savePanelPayload_(request.payload);
      try {
        sendCompanyAlerts_(request.payload);
        sendMonthlyReportIfDue_(request.payload);
      } catch (alertError) {
        console.error('Falha ao verificar alertas: ' + alertError);
      }
      return jsonResponse_({ok: true, message: 'Painel atualizado.'});
    }

    if (request.action === 'ai_assistant') {
      if (request.syncKey !== expectedKey) return jsonResponse_({ok: false, message: 'Chave de sincronização inválida.'});
      return jsonResponse_(runAiAssistant_(request.payload || {}));
    }

    if (request.action === 'test_notifications') {
      if (request.syncKey !== expectedKey) return jsonResponse_({ok: false, message: 'Chave de sincronização inválida.'});
      return jsonResponse_(sendTestNotification_(request.payload || {}));
    }

    if (request.action === 'cipa_publish') {
      if (request.syncKey !== expectedKey) return jsonResponse_({ok: false, message: 'Chave de sincronização inválida.'});
      return jsonResponse_(publishCipaElection_(request.payload || {}));
    }

    if (request.action === 'cipa_close') {
      if (request.syncKey !== expectedKey) return jsonResponse_({ok: false, message: 'Chave de sincronização inválida.'});
      return jsonResponse_(closeCipaElection_(String(request.electionToken || '')));
    }

    if (request.action === 'cipa_participation') {
      if (request.syncKey !== expectedKey) return jsonResponse_({ok: false, message: 'Chave de sincronização inválida.'});
      return jsonResponse_(getCipaParticipation_(String(request.electionToken || '')));
    }

    return jsonResponse_({ok: false, message: 'Requisição inválida.'});
  } catch (err) {
    return jsonResponse_({ok: false, message: String(err)});
  }
}

function connectGoogleDrive_() {
  const folder = ensureDriveRootFolder_();
  let accountLabel = '';
  try {
    accountLabel = String(Session.getEffectiveUser().getEmail() || '').trim();
  } catch (_) {}
  return {
    ok: true,
    folderId: folder.getId(),
    accountLabel: accountLabel || 'Drive da Central Online',
    message: 'Google Drive conectado.'
  };
}

function uploadReportToDrive_(request) {
  const mimeType = String(request.mimeType || '').trim().toLowerCase();
  const encoded = String(request.contentBase64 || '').trim();
  const fileName = safeDriveName_(request.fileName, 'Relatorio SST.pdf');
  const companyId = String(request.companyId || '').trim();
  const companyName = safeDriveName_(request.companyName, 'Sem empresa');
  const companyCnpj = normalizeDigits_(request.companyCnpj);

  if (mimeType !== 'application/pdf' || !/\.pdf$/i.test(fileName)) {
    return {ok: false, message: 'Somente relatórios PDF podem ser enviados.'};
  }
  if (!encoded) {
    return {ok: false, message: 'O arquivo do relatório não foi recebido.'};
  }

  let bytes;
  try {
    bytes = Utilities.base64Decode(encoded);
  } catch (_) {
    return {ok: false, message: 'O arquivo do relatório está inválido.'};
  }
  if (!bytes.length) {
    return {ok: false, message: 'O arquivo do relatório está vazio.'};
  }
  if (bytes.length > DRIVE_MAX_REPORT_BYTES) {
    return {ok: false, message: 'O relatório ultrapassa o limite de 20 MB.'};
  }

  const root = ensureDriveRootFolder_();
  const companyFolder = findOrCreateCompanyDriveFolder_(
    root,
    companyName,
    companyCnpj,
    companyId
  );
  const existing = companyFolder.getFilesByName(fileName);
  if (existing.hasNext()) {
    const file = existing.next();
    return {
      ok: true,
      fileId: file.getId(),
      duplicate: true,
      message: 'Relatório já estava salvo no Google Drive.'
    };
  }

  const blob = Utilities.newBlob(bytes, 'application/pdf', fileName);
  const file = companyFolder.createFile(blob);
  return {
    ok: true,
    fileId: file.getId(),
    duplicate: false,
    message: 'Relatório salvo no Google Drive.'
  };
}

function ensureDriveRootFolder_() {
  return findOrCreateDriveFolder_(DriveApp.getRootFolder(), DRIVE_ROOT_FOLDER);
}

function findOrCreateDriveFolder_(parent, name) {
  const folders = parent.getFoldersByName(name);
  return folders.hasNext() ? folders.next() : parent.createFolder(name);
}

function findOrCreateCompanyDriveFolder_(root, companyName, companyCnpj, companyId) {
  const cnpj = normalizeDigits_(companyCnpj);
  const identity = cnpj.length === 14
    ? 'cnpj:' + cnpj
    : companyId
      ? 'id:' + companyId
      : 'name:' + String(companyName || '').toLowerCase();
  const marker = 'Auditar SST | ' + identity;
  const expectedName = cnpj.length === 14
    ? safeDriveName_(companyName + ' - CNPJ ' + formatCnpj_(cnpj), 'Empresa')
    : safeDriveName_(companyName, 'Sem empresa');
  const folders = root.getFolders();
  let legacyFolder = null;

  while (folders.hasNext()) {
    const folder = folders.next();
    const folderName = String(folder.getName() || '');
    let description = '';
    try {
      description = String(folder.getDescription() || '');
    } catch (_) {}

    if (description.indexOf(marker) >= 0) {
      return prepareCompanyDriveFolder_(folder, expectedName, marker);
    }

    if (cnpj.length === 14 && normalizeDigits_(folderName).indexOf(cnpj) >= 0) {
      return prepareCompanyDriveFolder_(folder, expectedName, marker);
    }

    if (!legacyFolder && folderName === companyName && description.indexOf('Auditar SST |') < 0) {
      legacyFolder = folder;
    }
  }

  if (legacyFolder) {
    return prepareCompanyDriveFolder_(legacyFolder, expectedName, marker);
  }

  return prepareCompanyDriveFolder_(root.createFolder(expectedName), expectedName, marker);
}

function prepareCompanyDriveFolder_(folder, expectedName, marker) {
  if (folder.getName() !== expectedName) folder.setName(expectedName);
  let description = '';
  try {
    description = String(folder.getDescription() || '').trim();
  } catch (_) {}
  if (description.indexOf(marker) < 0) {
    folder.setDescription((description ? description + '\n' : '') + marker);
  }
  return folder;
}

function formatCnpj_(cnpj) {
  const digits = normalizeDigits_(cnpj);
  if (digits.length !== 14) return digits;
  return digits.substring(0, 2) + '.' +
    digits.substring(2, 5) + '.' +
    digits.substring(5, 8) + '-' +
    digits.substring(8, 12) + '-' +
    digits.substring(12, 14);
}

function safeDriveName_(value, fallback) {
  const cleaned = String(value || '')
    .replace(/[\\/:*?"<>|\u0000-\u001f]/g, '_')
    .replace(/\s+/g, ' ')
    .trim();
  return (cleaned || fallback).substring(0, 160);
}

function runAiAssistant_(payload) {
  const props = PropertiesService.getScriptProperties();
  const apiKey = String(props.getProperty('GEMINI_API_KEY') || '').trim();
  if (!apiKey) {
    return {
      ok: false,
      code: 'AI_NOT_CONFIGURED',
      message: 'O Assistente IA ainda não foi configurado no Google Apps Script.'
    };
  }

  const mode = String(payload.mode || '').trim();
  if (['checklist_photo', 'safety_observation_photo', 'report_conclusion', 'company_priorities', 'training_management', 'employee_pdf_import', 'medical_pdf_import'].indexOf(mode) < 0) {
    return {ok: false, message: 'Tipo de análise de IA inválido.'};
  }

  const images = Array.isArray(payload.images) ? payload.images.slice(0, 4) : [];
  const imageBytes = images.reduce((total, image) => total + String(image || '').length, 0);
  if (imageBytes > 14000000) {
    return {ok: false, message: 'As fotos ultrapassaram o limite da análise. Use menos fotos ou imagens menores.'};
  }
  if ((mode === 'checklist_photo' || mode === 'safety_observation_photo') && !images.length) {
    return {ok: false, message: 'Adicione pelo menos uma foto antes de analisar.'};
  }

  const document = String(payload.document || '');
  if (mode === 'employee_pdf_import' || mode === 'medical_pdf_import') {
    if (document.indexOf('data:application/pdf;base64,') !== 0) {
      return {ok: false, message: mode === 'medical_pdf_import'
        ? 'Selecione um PDF válido com o controle de periódicos.'
        : 'Selecione um PDF válido com a lista de funcionários.'};
    }
    if (document.length > 18000000) {
      return {ok: false, message: 'O PDF ultrapassou o limite da importação.'};
    }
  }

  const model = String(props.getProperty('AUDITAR_AI_MODEL') || 'gemini-3.5-flash-lite').trim();
  const parts = [{
    text: aiSafetyInstructions_() + '\n\n' + aiUserPrompt_(mode, payload)
  }];
  images.forEach(image => {
    const value = String(image || '');
    const match = value.match(/^data:(image\/[a-zA-Z0-9.+-]+);base64,(.+)$/);
    if (match) {
      parts.push({inlineData: {mimeType: match[1], data: match[2]}});
    }
  });
  if (mode === 'employee_pdf_import' || mode === 'medical_pdf_import') {
    const match = document.match(/^data:(application\/pdf);base64,(.+)$/);
    if (match) {
      parts.push({inlineData: {mimeType: match[1], data: match[2]}});
    }
  }

  const body = {
    contents: [{role: 'user', parts: parts}],
    generationConfig: {
      maxOutputTokens: mode === 'employee_pdf_import' || mode === 'medical_pdf_import'
        ? 12000
        : mode === 'training_management' ? 3200
        : mode === 'report_conclusion' ? 1400 : 1700,
      responseMimeType: 'application/json',
      responseSchema: aiOutputSchema_(mode)
    }
  };

  try {
    const endpoint = GEMINI_API_BASE_URL + encodeURIComponent(model) + ':generateContent';
    const response = UrlFetchApp.fetch(endpoint, {
      method: 'post',
      contentType: 'application/json',
      headers: {'x-goog-api-key': apiKey},
      payload: JSON.stringify(body),
      muteHttpExceptions: true
    });
    const status = response.getResponseCode();
    const raw = response.getContentText();
    let parsed;
    try {
      parsed = JSON.parse(raw);
    } catch (_) {
      parsed = {};
    }
    if (status < 200 || status >= 300) {
      const apiMessage = parsed && parsed.error ? parsed.error.message : '';
      if (status === 429) {
        return {ok: false, message: 'A cota gratuita da IA foi atingida. Tente novamente mais tarde.'};
      }
      return {ok: false, message: apiMessage || ('A IA respondeu com erro ' + status + '.')};
    }
    const outputText = extractGeminiText_(parsed);
    if (!outputText) return {ok: false, message: 'A IA não retornou uma análise utilizável.'};
    let result;
    try {
      result = JSON.parse(outputText);
    } catch (_) {
      return {ok: false, message: 'Não foi possível interpretar a análise da IA.'};
    }
    return {ok: true, result: result, model: model};
  } catch (error) {
    return {ok: false, message: 'Falha ao consultar a IA: ' + String(error)};
  }
}

function aiSafetyInstructions_() {
  return [
    'Você auxilia um Técnico de Segurança do Trabalho brasileiro durante vistorias.',
    'Responda sempre em português do Brasil, com linguagem técnica clara e objetiva.',
    'A análise é um rascunho de apoio e nunca substitui inspeção presencial, medição, laudo, responsável legal ou decisão do técnico.',
    'Use somente os dados e evidências recebidos. Não invente medidas, materiais, proteções, atividades, agentes, pessoas ou fatos que não estejam visíveis ou informados.',
    'Quando algo não puder ser confirmado pela foto, registre isso em checksRequired ou nas limitações previstas para o tipo de análise.',
    'Não declare conformidade legal definitiva. Cite NRs apenas como referências prováveis a conferir na versão vigente.',
    'Priorize risco grave e iminente, necessidade de interrupção segura e isolamento quando a evidência justificar, sem exagerar.',
    'Nunca inclua CPF, diagnóstico médico ou dado pessoal sensível na resposta.'
  ].join(' ');
}

function aiUserPrompt_(mode, payload) {
  if (mode === 'checklist_photo') {
    return [
      'Analise as fotos e o item do checklist abaixo.',
      'Empresa: ' + String(payload.companyName || 'não informada') + '.',
      'Setor ou área: ' + String(payload.area || 'não informado') + '.',
      'Item: ' + String(payload.question || '') + '.',
      'Categoria: ' + String(payload.category || '') + '.',
      'Referência cadastrada: ' + String(payload.reference || '') + '.',
      'Observação do técnico: ' + String(payload.technicianContext || 'nenhuma') + '.',
      'Gere uma sugestão curta para preencher a não conformidade, o risco identificado, a recomendação, a prioridade e um plano de ação inicial.'
    ].join('\n');
  }
  if (mode === 'safety_observation_photo') {
    return [
      'Analise a foto como apoio ao registro de uma condição insegura ou ato inseguro em SST.',
      'Empresa: ' + String(payload.companyName || 'não informada') + '.',
      'Tipo selecionado pelo técnico: ' + String(payload.observationKind || 'não informado') + '.',
      'Setor: ' + String(payload.sectorName || 'não informado') + '.',
      'Local exato: ' + String(payload.location || 'não informado') + '.',
      'Contexto já informado pelo técnico: ' + String(payload.technicianContext || 'nenhum') + '.',
      'Descreva somente fatos observáveis na imagem ou informados pelo técnico. Não identifique pessoas e não atribua culpa ou intenção.',
      'Sugira título curto, descrição objetiva, risco identificado, possível consequência, ação imediata segura quando aplicável, recomendação ou medida corretiva, prioridade e um plano de tratativa inicial.',
      'Quando a foto não for suficiente para confirmar algo, coloque a dúvida em checksRequired em vez de afirmar.'
    ].join('\n');
  }
  if (mode === 'training_management') {
    const objective = String(payload.objective || 'prioritize');
    const objectiveText = objective === 'groups'
      ? 'Sugira turmas práticas agrupando somente colaboradores que possuem a mesma necessidade de treinamento.'
      : objective === 'plan'
        ? 'Monte uma ordem prática para os próximos treinamentos, considerando urgência, vencimentos, novos colaboradores e possibilidade de agrupamento.'
        : 'Priorize as pendências de treinamento e explique de forma curta o que deve ser tratado primeiro.';
    return [
      'Atue como assistente de gestão de treinamentos em SST.',
      'A matriz de treinamentos recebida é a única fonte para definir quais treinamentos são obrigatórios por cargo. Não invente NR, obrigação, validade ou exigência que não esteja na matriz.',
      'Use apenas colaboradores, IDs, cargos, setores, pendências e treinamentos presentes nos dados recebidos.',
      'Nunca inclua CPF ou qualquer dado médico.',
      objectiveText,
      'Em suggestedGroups, use apenas participantIds que existam nas pendências recebidas e que realmente precisem do treinamento sugerido.',
      'Quando faltar matriz para algum cargo, informe em dataGaps e não conclua que determinado treinamento é obrigatório para esse cargo.',
      'Dados JSON:',
      JSON.stringify(payload.trainingData || {})
    ].join('\n');
  }
  if (mode === 'report_conclusion') {
    return [
      'Prepare observações gerais e uma conclusão profissional para um relatório de vistoria SST.',
      'Não invente achados. Use somente o resumo JSON abaixo.',
      JSON.stringify(payload.inspectionData || {})
    ].join('\n');
  }
  if (mode === 'employee_pdf_import') {
    return [
      'Leia a lista de funcionários deste PDF.',
      'Extraia somente as pessoas que fazem parte da lista atual de empregados.',
      'Para cada pessoa, informe nome completo, cargo ou função e setor quando estiver claramente indicado.',
      'Transcreva o nome e o cargo exatamente como aparecem no documento, sem resumir, corrigir ou trocar a nomenclatura.',
      'Ignore títulos, cabeçalhos, rodapés, assinaturas, responsáveis, totais e textos administrativos.',
      'Não invente pessoas nem complete nomes ou cargos ilegíveis.',
      'Não inclua CPF, matrícula, telefone, endereço, salário, dados médicos ou qualquer outro dado pessoal.'
    ].join('\n');
  }
  if (mode === 'medical_pdf_import') {
    return [
      'Leia este PDF de controle de exames ocupacionais.',
      'Extraia somente nome do trabalhador, cargo quando houver, data do último exame e data do próximo periódico.',
      'Transcreva o nome e o cargo exatamente como aparecem no documento.',
      'Converta datas válidas para AAAA-MM-DD. Use texto vazio quando uma data não estiver claramente informada.',
      'Não invente datas e não calcule vencimentos.',
      'Ignore diagnósticos, resultados clínicos, aptidão, CPF, matrícula, endereço, telefone e demais informações.'
    ].join('\n');
  }
  return [
    'Analise os indicadores agregados da empresa e aponte prioridades práticas para o técnico.',
    'Não invente causas e não inclua pessoas. Dados JSON:',
    JSON.stringify(payload.companyData || {})
  ].join('\n');
}

function aiOutputSchema_(mode) {
  if (mode === 'checklist_photo') {
    return {
        type: 'object',
        properties: {
          description: {type: 'string'},
          risk: {type: 'string'},
          recommendation: {type: 'string'},
          immediateAction: {type: 'string'},
          correctiveAction: {type: 'string'},
          responsibleProfile: {type: 'string'},
          suggestedDeadlineDays: {type: 'integer', minimum: 0, maximum: 365},
          priority: {type: 'string', enum: ['Baixa', 'Média', 'Alta', 'Crítica']},
          likelyReferences: {type: 'array', items: {type: 'string'}},
          checksRequired: {type: 'array', items: {type: 'string'}},
          confidence: {type: 'string', enum: ['Baixa', 'Média', 'Alta']}
        },
        required: ['description', 'risk', 'recommendation', 'immediateAction', 'correctiveAction', 'responsibleProfile', 'suggestedDeadlineDays', 'priority', 'likelyReferences', 'checksRequired', 'confidence']
    };
  }
  if (mode === 'safety_observation_photo') {
    return {
      type: 'object',
      properties: {
        title: {type: 'string'},
        description: {type: 'string'},
        risk: {type: 'string'},
        possibleConsequence: {type: 'string'},
        recommendation: {type: 'string'},
        immediateAction: {type: 'string'},
        correctiveAction: {type: 'string'},
        responsibleProfile: {type: 'string'},
        suggestedDeadlineDays: {type: 'integer', minimum: 0, maximum: 365},
        priority: {type: 'string', enum: ['Baixa', 'Média', 'Alta', 'Crítica']},
        likelyReferences: {type: 'array', items: {type: 'string'}},
        checksRequired: {type: 'array', items: {type: 'string'}},
        confidence: {type: 'string', enum: ['Baixa', 'Média', 'Alta']}
      },
      required: ['title', 'description', 'risk', 'possibleConsequence', 'recommendation', 'immediateAction', 'correctiveAction', 'responsibleProfile', 'suggestedDeadlineDays', 'priority', 'likelyReferences', 'checksRequired', 'confidence']
    };
  }
  if (mode === 'training_management') {
    return {
      type: 'object',
      properties: {
        summary: {type: 'string'},
        priorities: {
          type: 'array',
          items: {
            type: 'object',
            properties: {
              title: {type: 'string'},
              detail: {type: 'string'},
              urgency: {type: 'string', enum: ['Baixa', 'Média', 'Alta']}
            },
            required: ['title', 'detail', 'urgency']
          }
        },
        suggestedGroups: {
          type: 'array',
          items: {
            type: 'object',
            properties: {
              trainingCode: {type: 'string'},
              trainingTitle: {type: 'string'},
              participantIds: {type: 'array', items: {type: 'string'}},
              reason: {type: 'string'}
            },
            required: ['trainingCode', 'trainingTitle', 'participantIds', 'reason']
          }
        },
        plan: {
          type: 'array',
          items: {
            type: 'object',
            properties: {
              order: {type: 'integer', minimum: 1, maximum: 20},
              action: {type: 'string'},
              training: {type: 'string'},
              reason: {type: 'string'}
            },
            required: ['order', 'action', 'training', 'reason']
          }
        },
        dataGaps: {type: 'array', items: {type: 'string'}},
        warning: {type: 'string'}
      },
      required: ['summary', 'priorities', 'suggestedGroups', 'plan', 'dataGaps', 'warning']
    };
  }
  if (mode === 'report_conclusion') {
    return {
        type: 'object',
        properties: {
          generalNotes: {type: 'string'},
          conclusion: {type: 'string'},
          criticalSummary: {type: 'string'},
          limitations: {type: 'array', items: {type: 'string'}}
        },
        required: ['generalNotes', 'conclusion', 'criticalSummary', 'limitations']
    };
  }
  if (mode === 'employee_pdf_import') {
    return {
      type: 'object',
      properties: {
        employees: {
          type: 'array',
          items: {
            type: 'object',
                properties: {
              name: {type: 'string'},
              role: {type: 'string'},
              sector: {type: 'string'}
            },
            required: ['name', 'role', 'sector']
          }
        }
      },
      required: ['employees']
    };
  }
  if (mode === 'medical_pdf_import') {
    return {
      type: 'object',
      properties: {
        records: {
          type: 'array',
          items: {
            type: 'object',
                properties: {
              name: {type: 'string'},
              role: {type: 'string'},
              lastExamDate: {type: 'string'},
              nextExamDate: {type: 'string'}
            },
            required: ['name', 'role', 'lastExamDate', 'nextExamDate']
          }
        }
      },
      required: ['records']
    };
  }
  return {
      type: 'object',
      properties: {
        situation: {type: 'string'},
        priorities: {type: 'array', items: {type: 'string'}},
        nextActions: {type: 'array', items: {type: 'string'}},
        dataGaps: {type: 'array', items: {type: 'string'}}
      },
      required: ['situation', 'priorities', 'nextActions', 'dataGaps']
  };
}

function extractGeminiText_(response) {
  const candidates = response && Array.isArray(response.candidates) ? response.candidates : [];
  if (!candidates.length) return '';
  const parts = candidates[0].content && Array.isArray(candidates[0].content.parts)
    ? candidates[0].content.parts
    : [];
  const texts = [];
  for (let i = 0; i < parts.length; i++) {
    if (typeof parts[i].text === 'string') texts.push(parts[i].text);
  }
  return texts.join('');
}

function doGet(e) {
  const params = (e && e.parameter) || {};

  if (String(params.api || '') === 'cipa_status') {
    return jsonResponse_(getCipaStatus_(String(params.cipa || '').trim()));
  }

  const cipaToken = String(params.cipa || '').trim();
  if (cipaToken) {
    const election = findCipaElection_(cipaToken);
    if (!election) return unavailablePage_('Eleição não encontrada.');
    if (election.status !== 'Aberta') {
      return unavailablePage_(election.status === 'Encerrada' ? 'Esta votação já foi encerrada.' : 'Esta votação ainda não está aberta.');
    }
    const template = HtmlService.createTemplateFromFile('Votacao');
    template.electionJson = safeJsonForHtml_({
      token: election.token,
      companyName: election.companyName,
      title: election.title,
      managementPeriod: election.managementPeriod,
      candidates: election.candidates,
    });
    return template.evaluate()
      .setTitle('Votação CIPA • Auditar SST')
      .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
  }

  const companyToken = String(params.empresa || '').trim();
  if (!companyToken) return unavailablePage_('Link inválido.');
  const record = findPanelPayload_(companyToken);
  if (!record) return unavailablePage_('Painel não encontrado.');
  if (!record.active) return unavailablePage_('Este acesso está desativado.');

  const template = HtmlService.createTemplateFromFile('Index');
  template.payloadJson = safeJsonForHtml_(record.payload);
  return template.evaluate()
    .setTitle('Painel Gerencial SST')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

function registrarVoto(electionToken, voterCode, voterCpf, candidateId) {
  const token = String(electionToken || '').trim();
  const code = String(voterCode || '').trim().toUpperCase();
  const cpf = normalizeDigits_(voterCpf);
  const candidate = String(candidateId || '').trim();
  if (!token || !code || !cpf || !candidate) return {ok: false, message: 'Informe código, CPF e escolha um candidato.'};
  if (cpf.length !== 11) return {ok: false, message: 'Informe um CPF válido com 11 dígitos.'};

  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    ensureCipaStorage_();
    const election = findCipaElection_(token);
    if (!election) return {ok: false, message: 'Eleição não encontrada.'};
    if (election.status !== 'Aberta') return {ok: false, message: 'A votação não está aberta.'};
    if (!election.companyCnpj || normalizeDigits_(election.companyCnpj).length !== 14) {
      return {ok: false, message: 'Esta eleição precisa ser republicada com a validação de CNPJ habilitada.'};
    }
    if (!election.candidates.some(c => String(c.id) === candidate)) {
      return {ok: false, message: 'Candidato inválido.'};
    }

    const voters = getSheet_(CIPA_VOTERS_SHEET);
    const codeHash = hashCode_(code);
    const identityHash = hashIdentity_(election.companyCnpj, cpf);
    const lastRow = voters.getLastRow();
    if (lastRow < 2) return {ok: false, message: 'Código de votação inválido.'};
    const rows = voters.getRange(2, 1, lastRow - 1, 8).getValues();
    let targetRow = -1;
    let used = false;
    let identityMatches = false;
    for (let i = 0; i < rows.length; i++) {
      if (String(rows[i][0]) === token && String(rows[i][1]) === codeHash) {
        targetRow = i + 2;
        used = rows[i][2] === true || String(rows[i][2]).toLowerCase() === 'true';
        identityMatches = String(rows[i][3] || '') === identityHash;
        break;
      }
    }
    if (targetRow < 0) return {ok: false, message: 'Código de votação inválido.'};
    if (!identityMatches) return {ok: false, message: 'CPF e código não correspondem a um trabalhador apto desta empresa.'};
    if (used) return {ok: false, message: 'Este trabalhador já registrou participação nesta eleição.'};

    // A participação identificada e a cédula permanecem em tabelas separadas.
    voters.getRange(targetRow, 3).setValue(true);
    getSheet_(CIPA_VOTES_SHEET).appendRow([
      token,
      Utilities.getUuid().replace(/-/g, ''),
      candidate,
    ]);
    SpreadsheetApp.flush();
    return {ok: true, message: 'Voto registrado com sucesso. Obrigado por participar.'};
  } finally {
    lock.releaseLock();
  }
}

function publishCipaElection_(payload) {
  ensureCipaStorage_();
  const election = payload.election || {};
  const company = payload.company || {};
  const candidates = Array.isArray(payload.candidates) ? payload.candidates : [];
  const voters = Array.isArray(payload.voters) ? payload.voters : [];
  const token = String(election.token || '').trim();
  const companyCnpj = normalizeDigits_(company.cnpj);
  if (!token) return {ok: false, message: 'Token da eleição ausente.'};
  if (companyCnpj.length !== 14) return {ok: false, message: 'CNPJ da empresa inválido ou não cadastrado.'};
  if (!candidates.length) return {ok: false, message: 'Cadastre candidatos antes de publicar.'};
  if (!voters.length) return {ok: false, message: 'Prepare os eleitores antes de publicar.'};

  const existing = findCipaElection_(token);
  if (existing && countVotes_(token) > 0) {
    return {ok: false, message: 'A eleição já recebeu votos e não pode ser republicada.'};
  }

  const identitySet = {};
  for (let i = 0; i < voters.length; i++) {
    const voter = voters[i] || {};
    const accessCode = String(voter.accessCode || '').trim().toUpperCase();
    const identityHash = String(voter.identityHash || '').trim().toLowerCase();
    if (!accessCode || !identityHash || !String(voter.name || '').trim()) {
      return {ok: false, message: 'Há eleitor sem identificação válida. Prepare a lista novamente no aplicativo.'};
    }
    if (identitySet[identityHash]) {
      return {ok: false, message: 'Há trabalhador duplicado na lista de eleitores.'};
    }
    identitySet[identityHash] = true;
  }

  const electionSheet = getSheet_(CIPA_ELECTIONS_SHEET);
  const values = [
    token,
    String(election.id || ''),
    String(company.id || ''),
    String(company.name || ''),
    String(election.title || 'Eleição CIPA'),
    String(election.managementPeriod || ''),
    'Aberta',
    voters.length,
    new Date().toISOString(),
    JSON.stringify(candidates.map(c => ({
      id: String(c.id || ''),
      name: String(c.name || ''),
      role: String(c.role || ''),
      sector: String(c.sector || ''),
    }))),
    companyCnpj,
  ];
  upsertByToken_(electionSheet, token, values);

  const voterSheet = getSheet_(CIPA_VOTERS_SHEET);
  deleteRowsForToken_(voterSheet, token, 1);
  voters.forEach(v => {
    voterSheet.appendRow([
      token,
      hashCode_(String(v.accessCode || '').trim().toUpperCase()),
      false,
      String(v.identityHash || '').trim().toLowerCase(),
      String(v.id || ''),
      String(v.name || ''),
      String(v.role || ''),
      String(v.sector || ''),
    ]);
  });

  const voteSheet = getSheet_(CIPA_VOTES_SHEET);
  deleteRowsForToken_(voteSheet, token, 1);
  SpreadsheetApp.flush();
  return {ok: true, message: 'Eleição publicada. Somente trabalhadores ativos vinculados ao CNPJ da empresa poderão votar com código + CPF.'};
}

function closeCipaElection_(token) {
  if (!token) return {ok: false, message: 'Eleição inválida.'};
  const sheet = getSheet_(CIPA_ELECTIONS_SHEET);
  const row = findRowByToken_(sheet, token);
  if (row < 0) return {ok: false, message: 'Eleição não encontrada.'};
  sheet.getRange(row, 7).setValue('Encerrada');
  sheet.getRange(row, 9).setValue(new Date().toISOString());
  SpreadsheetApp.flush();
  const status = getCipaStatus_(token);
  status.message = 'Votação encerrada. Apuração liberada.';
  return status;
}

function getCipaStatus_(token) {
  if (!token) return {ok: false, message: 'Eleição inválida.'};
  const election = findCipaElection_(token);
  if (!election) return {ok: false, message: 'Eleição não encontrada.'};

  const voterSheet = getSheet_(CIPA_VOTERS_SHEET);
  const lastRow = voterSheet.getLastRow();
  let eligible = 0;
  let voted = 0;
  if (lastRow >= 2) {
    const rows = voterSheet.getRange(2, 1, lastRow - 1, 3).getValues();
    rows.forEach(row => {
      if (String(row[0]) === token) {
        eligible++;
        if (row[2] === true || String(row[2]).toLowerCase() === 'true') voted++;
      }
    });
  }
  const participation = eligible ? Math.round((voted * 1000) / eligible) / 10 : 0;
  const target50 = Math.ceil(eligible * 0.5);
  const missingFor50 = Math.max(0, target50 - voted);
  const quorumMessage = participation >= 50
    ? 'Participação de 50% atingida.'
    : 'Faltam ' + missingFor50 + ' voto(s) para atingir 50% de participação.';

  const response = {
    ok: true,
    status: election.status,
    eligible: eligible,
    voted: voted,
    participation: participation,
    quorumMessage: quorumMessage,
    results: [],
  };

  if (election.status === 'Encerrada') {
    const counts = {};
    election.candidates.forEach(c => counts[String(c.id)] = 0);
    const voteSheet = getSheet_(CIPA_VOTES_SHEET);
    const voteLast = voteSheet.getLastRow();
    if (voteLast >= 2) {
      voteSheet.getRange(2, 1, voteLast - 1, 3).getValues().forEach(row => {
        if (String(row[0]) === token) {
          const id = String(row[2]);
          counts[id] = (counts[id] || 0) + 1;
        }
      });
    }
    response.results = election.candidates
      .map(c => ({
        id: c.id,
        name: c.name,
        role: c.role,
        sector: c.sector,
        votes: counts[String(c.id)] || 0,
      }))
      .sort((a, b) => b.votes - a.votes || String(a.name).localeCompare(String(b.name)))
      .map((r, i) => Object.assign({position: i + 1}, r));
  }
  return response;
}

function getCipaParticipation_(token) {
  if (!token) return {ok: false, message: 'Eleição inválida.'};
  ensureCipaStorage_();
  const election = findCipaElection_(token);
  if (!election) return {ok: false, message: 'Eleição não encontrada.'};
  const voterSheet = getSheet_(CIPA_VOTERS_SHEET);
  const lastRow = voterSheet.getLastRow();
  const participants = [];
  if (lastRow >= 2) {
    voterSheet.getRange(2, 1, lastRow - 1, 8).getValues().forEach(row => {
      if (String(row[0]) !== token) return;
      participants.push({
        id: String(row[4] || ''),
        name: String(row[5] || ''),
        role: String(row[6] || ''),
        sector: String(row[7] || ''),
        voted: row[2] === true || String(row[2]).toLowerCase() === 'true',
      });
    });
  }
  participants.sort((a, b) => String(a.name).localeCompare(String(b.name)));
  const voted = participants.filter(item => item.voted).length;
  return {
    ok: true,
    companyName: election.companyName,
    companyCnpj: election.companyCnpj,
    electionTitle: election.title,
    managementPeriod: election.managementPeriod,
    eligible: participants.length,
    voted: voted,
    participation: participants.length ? Math.round((voted * 1000) / participants.length) / 10 : 0,
    participants: participants,
    privacyNote: 'A lista registra apenas participação. Não existe vínculo entre o trabalhador e o candidato escolhido.',
  };
}

function findCipaElection_(token) {
  const sheet = getSheet_(CIPA_ELECTIONS_SHEET);
  const row = findRowByToken_(sheet, token);
  if (row < 0) return null;
  const data = sheet.getRange(row, 1, 1, 11).getValues()[0];
  let candidates = [];
  try { candidates = JSON.parse(String(data[9] || '[]')); } catch (_) {}
  return {
    token: String(data[0]),
    electionId: String(data[1] || ''),
    companyId: String(data[2] || ''),
    companyName: String(data[3] || ''),
    title: String(data[4] || ''),
    managementPeriod: String(data[5] || ''),
    status: String(data[6] || ''),
    totalVoters: Number(data[7] || 0),
    updatedAt: String(data[8] || ''),
    candidates: candidates,
    companyCnpj: String(data[10] || ''),
  };
}

function countVotes_(token) {
  const sheet = getSheet_(CIPA_VOTES_SHEET);
  if (sheet.getLastRow() < 2) return 0;
  return sheet.getRange(2, 1, sheet.getLastRow() - 1, 1).getValues()
    .filter(row => String(row[0]) === token).length;
}

function savePanelPayload_(payload) {
  const token = String(payload.accessToken || '').trim();
  if (!token) throw new Error('Token da empresa não informado.');
  const company = payload.company || {};
  const values = [
    token,
    String(company.id || ''),
    String(company.name || ''),
    payload.enabled !== false,
    String(payload.updatedAt || new Date().toISOString()),
    JSON.stringify(payload),
  ];
  upsertByToken_(getSheet_(PANEL_SHEET), token, values);
}

function findPanelPayload_(token) {
  const sheet = getSheet_(PANEL_SHEET);
  const row = findRowByToken_(sheet, token);
  if (row < 0) return null;
  const data = sheet.getRange(row, 1, 1, 6).getValues()[0];
  let payload;
  try { payload = JSON.parse(String(data[5] || '{}')); } catch (_) { return null; }
  return {
    active: data[3] === true || String(data[3]).toLowerCase() === 'true',
    payload: payload,
  };
}

function ensureSheet_(ss, name, headers) {
  let sheet = ss.getSheetByName(name);
  if (!sheet) sheet = ss.insertSheet(name);
  if (sheet.getLastRow() === 0) {
    sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
    sheet.setFrozenRows(1);
    return sheet;
  }
  const current = sheet.getRange(1, 1, 1, Math.max(headers.length, sheet.getLastColumn())).getValues()[0];
  let needsHeaderUpdate = false;
  for (let i = 0; i < headers.length; i++) {
    if (String(current[i] || '') !== String(headers[i])) {
      needsHeaderUpdate = true;
      break;
    }
  }
  if (needsHeaderUpdate) sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
  sheet.setFrozenRows(1);
  return sheet;
}

function ensureCipaStorage_() {
  const spreadsheetId = PropertiesService.getScriptProperties().getProperty('AUDITAR_SPREADSHEET_ID');
  if (!spreadsheetId) throw new Error('Execute setupAuditar() primeiro.');
  const ss = SpreadsheetApp.openById(spreadsheetId);
  ensureSheet_(ss, CIPA_ELECTIONS_SHEET, [
    'token', 'election_id', 'company_id', 'company_name', 'title',
    'management_period', 'status', 'total_voters', 'updated_at', 'candidates_json', 'company_cnpj'
  ]);
  ensureSheet_(ss, CIPA_VOTERS_SHEET, [
    'election_token', 'voter_hash', 'used', 'identity_hash',
    'voter_id', 'name', 'role', 'sector'
  ]);
  ensureSheet_(ss, CIPA_VOTES_SHEET, ['election_token', 'ballot_id', 'candidate_id']);
}

function normalizeDigits_(value) {
  return String(value || '').replace(/\D/g, '');
}

function hashIdentity_(cnpj, cpf) {
  return hashCode_(normalizeDigits_(cnpj) + '|' + normalizeDigits_(cpf));
}

function getSheet_(name) {
  const spreadsheetId = PropertiesService.getScriptProperties().getProperty('AUDITAR_SPREADSHEET_ID');
  if (!spreadsheetId) throw new Error('Execute setupAuditar() primeiro.');
  const ss = SpreadsheetApp.openById(spreadsheetId);
  const sheet = ss.getSheetByName(name);
  if (!sheet) throw new Error('Aba ' + name + ' não encontrada. Execute setupAuditar() novamente.');
  return sheet;
}

function findRowByToken_(sheet, token) {
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return -1;
  const values = sheet.getRange(2, 1, lastRow - 1, 1).getValues();
  for (let i = 0; i < values.length; i++) {
    if (String(values[i][0]) === String(token)) return i + 2;
  }
  return -1;
}

function upsertByToken_(sheet, token, values) {
  const row = findRowByToken_(sheet, token);
  if (row > 0) sheet.getRange(row, 1, 1, values.length).setValues([values]);
  else sheet.appendRow(values);
}

function deleteRowsForToken_(sheet, token, tokenColumn) {
  for (let row = sheet.getLastRow(); row >= 2; row--) {
    if (String(sheet.getRange(row, tokenColumn).getValue()) === String(token)) {
      sheet.deleteRow(row);
    }
  }
}

function hashCode_(code) {
  const bytes = Utilities.computeDigest(
    Utilities.DigestAlgorithm.SHA_256,
    String(code).trim().toUpperCase(),
    Utilities.Charset.UTF_8
  );
  return bytes.map(b => ('0' + ((b + 256) % 256).toString(16)).slice(-2)).join('');
}

function installAutomaticTrigger_() {
  const handler = 'processAutomaticNotifications';
  const exists = ScriptApp.getProjectTriggers()
    .some(trigger => trigger.getHandlerFunction() === handler);
  if (!exists) {
    ScriptApp.newTrigger(handler).timeBased().everyDays(1).atHour(8).create();
  }
}

function processAutomaticNotifications() {
  const sheet = getSheet_(PANEL_SHEET);
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return;
  const rows = sheet.getRange(2, 1, lastRow - 1, 6).getValues();
  rows.forEach(row => {
    const active = row[3] === true || String(row[3]).toLowerCase() === 'true';
    if (!active) return;
    let payload;
    try { payload = JSON.parse(String(row[5] || '{}')); } catch (_) { return; }
    try {
      sendCompanyAlerts_(payload);
      sendMonthlyReportIfDue_(payload);
    } catch (err) {
      console.error('Falha nos envios de ' + String((payload.company || {}).name || '') + ': ' + err);
    }
  });
}

function sendCompanyAlerts_(payload) {
  const notifications = payload.notifications || {};
  const recipients = emailRecipients_(notifications);
  if (!recipients.to) return;
  const company = payload.company || {};
  const monthKey = formatDate_(new Date(), 'yyyy-MM');
  const alerts = [];

  if (notifications.trainingAlertsEnabled === true) {
    (payload.trainingRecords || payload.trainingAlerts || []).forEach(item => {
      const calculatedDays = daysUntilDate_(item.expiryDate);
      const days = calculatedDays === null ? Number(item.daysUntilExpiry) : calculatedDays;
      const hasDays = calculatedDays !== null ||
        (item.daysUntilExpiry !== null && item.daysUntilExpiry !== '' && !isNaN(days));
      const milestone = hasDays && ([30, 15, 7, 0].indexOf(days) >= 0 || (days < 0 && Math.abs(days) % 7 === 0));
      if (!milestone && String(item.status || '') !== 'PENDENTE') return;
      const event = String(item.status || '') === 'PENDENTE'
        ? 'training-pending-' + String(item.id || '') + '-' + monthKey
        : 'training-' + String(item.id || '') + '-' + days;
      if (emailEventSent_(event)) return;
      alerts.push({
        key: event,
        type: 'Treinamento',
        worker: String(item.worker || ''),
        item: [item.code, item.title].filter(Boolean).join(' • '),
        status: trainingStatusText_(days, item.status),
      });
    });
    (payload.missingRequiredTrainings || []).forEach(item => {
      const event = 'missing-' + String(company.id || '') + '-' +
        String(item.workerId || '') + '-' + String(item.code || item.title || '') + '-' + monthKey;
      if (emailEventSent_(event)) return;
      alerts.push({
        key: event,
        type: 'Obrigatório sem registro',
        worker: String(item.worker || ''),
        item: [item.code, item.title].filter(Boolean).join(' • '),
        status: 'Sem registro no aplicativo',
      });
    });
  }

  if (notifications.medicalAlertsEnabled === true) {
    (payload.medicalExams || payload.medicalAlerts || []).forEach(item => {
      const calculatedDays = daysUntilDate_(item.nextExamDate);
      const days = calculatedDays === null ? Number(item.daysUntilExpiry) : calculatedDays;
      const hasDays = calculatedDays !== null ||
        (item.daysUntilExpiry !== null && item.daysUntilExpiry !== '' && !isNaN(days));
      const milestone = hasDays && ([30, 15, 7, 0].indexOf(days) >= 0 || (days < 0 && Math.abs(days) % 7 === 0));
      if (!milestone && hasDays) return;
      const event = hasDays
        ? 'medical-' + String(item.workerId || '') + '-' + days
        : 'medical-nodate-' + String(item.workerId || '') + '-' + monthKey;
      if (emailEventSent_(event)) return;
      alerts.push({
        key: event,
        type: 'Exame periódico',
        worker: String(item.worker || ''),
        item: 'Exame ocupacional periódico',
        status: hasDays ? dueStatusText_(days) : 'Próximo exame sem data cadastrada',
      });
    });
  }

  if (!alerts.length) return;
  const panelUrl = companyPanelUrl_(payload);
  const html = '<div style="font-family:Arial,sans-serif;color:#20242c">' +
    '<h2 style="color:#1d2e6c">Avisos SST • ' + escapeHtml_(company.name || 'Empresa') + '</h2>' +
    '<p>Os registros abaixo precisam de atenção:</p>' +
    htmlTable_(alerts, [
      ['Tipo', 'type'], ['Trabalhador', 'worker'], ['Item', 'item'], ['Situação', 'status']
    ]) +
    (panelUrl ? '<p><a href="' + escapeHtml_(panelUrl) + '">Abrir painel gerencial da empresa</a></p>' : '') +
    '<p style="color:#667085;font-size:12px">Mensagem automática do Auditar SST.</p></div>';
  GmailApp.sendEmail(
    recipients.to,
    'Avisos SST - ' + String(company.name || 'Empresa'),
    'Existem avisos de SST que precisam de atenção. Consulte o painel gerencial.',
    {htmlBody: html, cc: recipients.cc || undefined, name: 'Auditar SST'}
  );
  alerts.forEach(alert => markEmailEvent_(
    alert.key,
    String(company.id || ''),
    alert.type,
    [recipients.to, recipients.cc].filter(Boolean).join(', ')
  ));
}

function sendMonthlyReportIfDue_(payload) {
  const notifications = payload.notifications || {};
  if (notifications.monthlyReportEnabled !== true) return;
  const recipients = emailRecipients_(notifications);
  if (!recipients.to) return;
  const now = new Date();
  const configuredDay = Number(notifications.monthlyReportDay || 5);
  if (Number(formatDate_(now, 'd')) !== configuredDay) return;
  const company = payload.company || {};
  const event = 'monthly-' + String(company.id || '') + '-' + formatDate_(now, 'yyyy-MM');
  if (emailEventSent_(event)) return;

  const pdf = createMonthlyPdf_(payload);
  const panelUrl = companyPanelUrl_(payload);
  const recipientName = String(company.contact || '').trim();
  const greeting = recipientName ? 'Olá, ' + escapeHtml_(recipientName) + '.' : 'Olá.';
  const html = '<div style="font-family:Arial,sans-serif;color:#20242c">' +
    '<h2 style="color:#1d2e6c">Relatório mensal SST</h2><p>' + greeting + '</p>' +
    '<p>Segue o relatório mensal de Segurança e Saúde no Trabalho da empresa <strong>' +
    escapeHtml_(company.name || '') + '</strong>.</p>' +
    (panelUrl ? '<p><a href="' + escapeHtml_(panelUrl) + '">Acompanhar dados atualizados no painel gerencial</a></p>' : '') +
    '<p style="color:#667085;font-size:12px">Envio automático do Auditar SST.</p></div>';
  GmailApp.sendEmail(
    recipients.to,
    'Relatório mensal SST - ' + String(company.name || 'Empresa'),
    'Segue em anexo o relatório mensal de SST.',
    {htmlBody: html, cc: recipients.cc || undefined, attachments: [pdf], name: 'Auditar SST'}
  );
  markEmailEvent_(
    event,
    String(company.id || ''),
    'Relatório mensal',
    [recipients.to, recipients.cc].filter(Boolean).join(', ')
  );
}

function sendTestNotification_(payload) {
  const notifications = payload.notifications || {};
  const recipients = emailRecipients_(notifications);
  if (!recipients.to) {
    return {ok: false, message: 'Cadastre o e-mail principal da empresa antes do teste.'};
  }
  const company = payload.company || {};
  const summary = payload.summary || {};
  const training = payload.trainingSummary || {};
  const panelUrl = companyPanelUrl_(payload);
  const html = '<div style="font-family:Arial,sans-serif;color:#20242c">' +
    '<h2 style="color:#1d2e6c">Teste de notificações • Auditar SST</h2>' +
    '<p>Este e-mail confirma que os avisos automáticos da empresa <strong>' +
    escapeHtml_(company.name || 'Empresa') + '</strong> estão conectados.</p>' +
    '<table style="border-collapse:collapse;width:100%;max-width:620px">' +
    '<tr><td style="padding:8px;border:1px solid #ddd">Conformidade</td><td style="padding:8px;border:1px solid #ddd">' + String(summary.conformity || 0) + '%</td></tr>' +
    '<tr><td style="padding:8px;border:1px solid #ddd">Treinamentos vencidos</td><td style="padding:8px;border:1px solid #ddd">' + String(training.expired || 0) + '</td></tr>' +
    '<tr><td style="padding:8px;border:1px solid #ddd">Obrigatórios sem registro</td><td style="padding:8px;border:1px solid #ddd">' + String((payload.missingRequiredTrainings || []).length) + '</td></tr>' +
    '<tr><td style="padding:8px;border:1px solid #ddd">Periódicos com alerta</td><td style="padding:8px;border:1px solid #ddd">' + String((payload.medicalAlerts || []).length) + '</td></tr>' +
    '</table>' +
    (panelUrl ? '<p><a href="' + escapeHtml_(panelUrl) + '">Abrir painel gerencial</a></p>' : '') +
    '<p style="color:#667085;font-size:12px">Mensagem de teste enviada manualmente. Ela não altera o histórico dos alertas automáticos.</p></div>';
  GmailApp.sendEmail(
    recipients.to,
    'Teste Auditar SST - ' + String(company.name || 'Empresa'),
    'Teste concluído. Os e-mails automáticos do Auditar SST estão conectados.',
    {htmlBody: html, cc: recipients.cc || undefined, name: 'Auditar SST'}
  );
  return {
    ok: true,
    message: 'E-mail de teste enviado para ' + [recipients.to, recipients.cc].filter(Boolean).join(', ') + '.'
  };
}

function createMonthlyPdf_(payload) {
  const company = payload.company || {};
  const monthly = payload.monthlyReport || {};
  const summary = monthly.summary || payload.summary || {};
  const training = payload.trainingSummary || {};
  const doc = DocumentApp.create('Relatorio mensal SST - ' + String(company.name || 'Empresa'));
  const body = doc.getBody();
  body.appendParagraph('AUDITAR SST').setHeading(DocumentApp.ParagraphHeading.HEADING1);
  body.appendParagraph('RELATÓRIO MENSAL DE SEGURANÇA E SAÚDE NO TRABALHO')
    .setHeading(DocumentApp.ParagraphHeading.HEADING2);
  body.appendParagraph(String(company.name || 'Empresa'));
  const periodStart = monthly.periodStart ? new Date(monthly.periodStart) : null;
  const periodEnd = monthly.periodEnd ? new Date(monthly.periodEnd) : null;
  body.appendParagraph(periodStart && periodEnd
    ? 'Período: ' + formatDate_(periodStart, 'dd/MM/yyyy') + ' a ' + formatDate_(periodEnd, 'dd/MM/yyyy')
    : 'Gerado em ' + formatDate_(new Date(), 'dd/MM/yyyy'));
  body.appendHorizontalRule();
  body.appendParagraph('Resumo geral').setHeading(DocumentApp.ParagraphHeading.HEADING2);
  body.appendTable([
    ['Indicador', 'Resultado'],
    ['Vistorias registradas', String(summary.inspections || 0)],
    ['Conformidade', String(summary.conformity || 0) + '%'],
    ['NCs vencidas', String(summary.ncOverdue || 0)],
    ['Ações pendentes', String(summary.pending || 0)],
    ['Ações vencidas', String(summary.overdue || 0)],
  ]);
  body.appendParagraph('Treinamentos e saúde ocupacional')
    .setHeading(DocumentApp.ParagraphHeading.HEADING2);
  body.appendTable([
    ['Indicador', 'Quantidade'],
    ['Treinamentos em dia', String(training.current || 0)],
    ['Treinamentos vencidos', String(training.expired || 0)],
    ['Treinamentos pendentes', String(training.pending || 0)],
    ['Obrigatórios sem registro', String((payload.missingRequiredTrainings || []).length)],
    ['Alertas de exames periódicos', String((payload.medicalAlerts || []).length)],
  ]);
  const inspections = monthly.inspections || payload.recentInspections || [];
  if (inspections.length) {
    body.appendParagraph('Vistorias recentes').setHeading(DocumentApp.ParagraphHeading.HEADING2);
    body.appendTable([
      ['Relatório', 'Data', 'Setor', 'Situação'],
      ...inspections.slice(0, 12).map(item => [
        String(item.reportNumber || ''), String(item.date || ''),
        String(item.sector || ''), String(item.status || '')
      ])
    ]);
  }
  body.appendParagraph('Documento gerado automaticamente pelo Auditar SST.');
  doc.saveAndClose();
  const file = DriveApp.getFileById(doc.getId());
  const pdf = file.getBlob().getAs(MimeType.PDF)
    .setName('Relatorio_Mensal_SST_' + safeFileName_(company.name || 'Empresa') + '.pdf');
  file.setTrashed(true);
  return pdf;
}

function emailRecipients_(notifications) {
  const primary = String(notifications.primaryEmail || '').trim();
  const secondary = String(notifications.secondaryEmail || '').trim();
  return {to: primary, cc: secondary && secondary !== primary ? secondary : ''};
}

function companyPanelUrl_(payload) {
  const base = ScriptApp.getService().getUrl();
  const token = String(payload.accessToken || '').trim();
  return base && token ? base + '?empresa=' + encodeURIComponent(token) : '';
}

function trainingStatusText_(days, status) {
  if (String(status || '') === 'PENDENTE') return 'Registro pendente';
  return dueStatusText_(days);
}

function dueStatusText_(days) {
  if (days < 0) return 'Vencido há ' + Math.abs(days) + ' dia(s)';
  if (days === 0) return 'Vence hoje';
  return 'Vence em ' + days + ' dia(s)';
}

function emailEventSent_(key) {
  return getSheet_(EMAIL_LOG_SHEET).createTextFinder(String(key))
    .matchEntireCell(true).findNext() !== null;
}

function markEmailEvent_(key, companyId, type, recipients) {
  if (emailEventSent_(key)) return;
  getSheet_(EMAIL_LOG_SHEET).appendRow([
    key, companyId, type, new Date().toISOString(), recipients
  ]);
}

function formatDate_(date, pattern) {
  return Utilities.formatDate(date, 'America/Fortaleza', pattern);
}

function daysUntilDate_(value) {
  const match = String(value || '').match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (!match) return null;
  const due = Date.UTC(Number(match[1]), Number(match[2]) - 1, Number(match[3]));
  const todayParts = formatDate_(new Date(), 'yyyy-MM-dd').split('-').map(Number);
  const today = Date.UTC(todayParts[0], todayParts[1] - 1, todayParts[2]);
  return Math.round((due - today) / 86400000);
}

function safeFileName_(value) {
  return String(value || '').replace(/[^A-Za-z0-9_-]+/g, '_').replace(/^_+|_+$/g, '');
}

function escapeHtml_(value) {
  return String(value == null ? '' : value)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function htmlTable_(rows, columns) {
  const header = columns.map(column => '<th style="text-align:left;padding:8px;border-bottom:1px solid #ddd">' + escapeHtml_(column[0]) + '</th>').join('');
  const body = rows.map(row => '<tr>' + columns.map(column =>
    '<td style="padding:8px;border-bottom:1px solid #eee">' + escapeHtml_(row[column[1]] || '-') + '</td>'
  ).join('') + '</tr>').join('');
  return '<table style="border-collapse:collapse;width:100%;font-size:13px"><thead><tr>' + header + '</tr></thead><tbody>' + body + '</tbody></table>';
}

function safeJsonForHtml_(value) {
  return JSON.stringify(value)
    .replace(/</g, '\\u003c')
    .replace(/>/g, '\\u003e')
    .replace(/&/g, '\\u0026');
}

function jsonResponse_(data) {
  return ContentService.createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
}

function unavailablePage_(message) {
  const safe = String(message || 'Indisponível.')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  return HtmlService.createHtmlOutput(
    '<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">' +
    '<style>body{font-family:Arial,sans-serif;background:#f7f8fa;color:#14265b;display:grid;place-items:center;min-height:90vh;margin:0}' +
    '.box{background:white;padding:28px;border-radius:18px;max-width:420px;box-shadow:0 4px 20px #0001;text-align:center}</style>' +
    '</head><body><div class="box"><h2>Auditar SST</h2><p>' + safe + '</p></div></body></html>'
  );
}
