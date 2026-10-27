# Auditar SST — Tratativas e Linha do Tempo V2

**Status:** código no PR #15, que deve permanecer DRAFT. Não fazer merge nem deploy automático. A confirmação de CI NÃO substitui teste Android/Windows físico nem homologação do Google Apps Script.

## O que entrou

1. **Painel do Cliente**: caixa de entrada de tratativas e linha do tempo por empresa + por ocorrência publicada.
2. **Android/Windows**: atalho "Caixa de entrada Auditar" na Home e "Comunicação e tratativas" na empresa.
3. **Respostas rápidas**: esclarecimento, proposta de prazo, pedido de verificação, parecer, reunião. Eventos append-only, com autor e horário.
4. **Indicadores**: aguardando Auditar, aguardando cliente, aguardando verificação, em atraso. São **indicadores atualizados ao consultar**, NÃO notificações push.
5. **Fotos**: no Painel do Cliente, o link "Enviar foto da correção" reutiliza a rotina existente de evidências **somente para NC com permissão de envio**. Não há envio de foto no canal textual geral.
6. **Ações**: botão abre Plano de Ação existente; técnico pode registrar na conversa o ID de uma ação já cadastrada. **Não cria nem edita ação automaticamente**. Data de prazo e responsável são registrados na tratativa, sem alterar o plano preexistente.
7. **Reunião e eficácia**: modelo rápido de reunião; confirmação de eficácia restrita à Auditar e exige método (vistoria presencial, teste funcional, análise de evidência ou documental) e relato técnico detalhado. **A conclusão da conversa NÃO fecha a NC original**.

## Segurança e preservação

- `ClientPortalTreatments.gs`: módulo independente no Apps Script, guarda eventos em aba isolada `AUDITAR_TRATATIVAS_V1`.
- Cada leitura, postagem e resumo exigem sessão autenticada e acesso à empresa. Cliente usa apenas sessão do Painel do Cliente; o app usa autenticação existente e só aceita técnico/admin.
- Usuário cliente NÃO pode aprovar revisão técnica ou marcar eficácia sozinho.
- Somente assuntos publicados naquela empresa são apresentados; `GERAL` é canal geral.
- Eventos são somente adicionados; histórico não é apagado ao responder.
- Não mudou `database.dart`, `models.dart`, serviços existentes de sincronização, autenticação, fotos, Drive ou IA.
- Sem upload de documento na linha do tempo neste bloco; fotos vinculadas continuam no módulo de Evidências existente.

## Módulos e inserções necessárias na Central de homologação

**Não substitua seu Code.gs atual por uma versão antiga do GitHub.** Seu Code.gs original enviado anteriormente contém funções e rotas que precisam ser preservadas.

Em cópia da Central:

1. Acrescente um novo arquivo Apps Script **`ClientPortalTreatments.gs`**, com o conteúdo `feature_sources/ClientPortalTreatments_v1.gs` do repositório.
2. Dentro da cadeia atual que atende `doPost(e)`, insira apenas o ramo de ação, uma vez, antes de `worksite_followup_sync_v1`:

```javascript
if (request.action === 'client_treatment_v2') {
  return jsonResponse_(clientTreatmentAppV2_(request));
}
```

3. No `ClientPortal.gs` de homologação, acrescentar `tratativas` às `CLIENT_PORTAL_PERMISSION_KEYS` e à política de permissões de equipe, sem retirar as atuais.
4. Integrar o JS e o CSS aditivos em `ClientPortal.html` com o script `tools/patch_client_treatment_timeline_v1.py` (base build) e os arquivos `feature_sources/client_treatment_portal_ui_v1.js` e `.css`. Confirme equivalência com a versão atualmente implantada antes de copiar.
5. Habilitar a permissão **Comunicação e tratativas por ocorrência** na conta do cliente via ADM. Para contas anteriores, a permissão permanece desabilitada até liberação do administrador.
6. Não executar rotinas que recriem usuários, apaguem planilhas ou modifiquem a sincronização.

## Roteiro de testes (recomendado)

- Criar duas ocorrências em empresa A e uma em empresa B com usuários diferentes.
- Cliente A envia esclarecimento para ocorrência A1; Auditar vê na caixa de entrada; cliente B não vê o dado de A.
- Técnico responde, registra reunião com participantes e encaminhamentos; cliente A vê resposta na ordem correta.
- Testar filtro de pendentes, atrasados e resposta pela Home do aplicativo.
- Cliente tenta confirmar eficácia: deve ser recusado; TST só confirma com método e relato suficiente.
- Comparar relatórios PDF, fotos, não conformidades, histórico e sincronização antes/depois.
- Testar internet indisponível: **a mensagem não é enviada nem enfileirada**; app deve preservar dados SST e exibir erro de Central.
- Verificar ausência de novas permissões concedidas automaticamente a contas clientes existentes.
- Executar `node tools/test_client_treatments_v1.js`; `python tools/test_client_treatment_portal_patch_v1.py <APP_DIR>`; format/analyze/test Flutter; Android/Windows release builds.

## Limitações desta etapa

Sem push notifications, sem anexos genéricos/áudio na linha do tempo, sem criação automática de Plano de Ação e sem sincronização offline de mensagens. O objetivo é não tocar na sincronização estável, mantendo um canal separado e rastreável.

**Versões em validação:** Android `3.29.182+324`, Windows `3.30.105+292`. Repositório branch `feature/client-panel-permissions-v329106`, PR #15 DRAFT.
