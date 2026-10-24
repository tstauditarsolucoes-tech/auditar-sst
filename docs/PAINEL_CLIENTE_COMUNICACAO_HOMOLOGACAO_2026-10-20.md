# Painel do Cliente — Comunicação SST, linha do tempo e solicitar apoio

Estado: CANDIDATO; **não publicado**. PR #15 deve ficar DRAFT; não fazer merge, deploy, nem alterar Code.gs, MultiUser.gs, autenticação ou sincronização sem autorização.

## Diagnóstico

A interface da comunicação e o arquivo `ClientPortalTreatments.gs` estão em `feature_sources/`; são integrados à Central montada pelo script `tools/patch_client_treatment_timeline_v1.py`. A existência da interface no repositório **não demonstra** que o Apps Script atualmente publicado esteja usando essa montagem.

O sistema usa `google.script.run` para chamar `clientPortalTreatmentList`, `clientPortalTreatmentPost`, `clientPortalTreatmentTopics` e `clientPortalTreatmentInbox`. Se a implantação não contiver as funções, ou a permissão `tratativas` não estiver habilitada para a conta, o botão não consegue registrar pedidos. Não confundir mudança na fonte com correção efetiva do site publicado.

## Pré-voo, sem executar em produção

1. Fazer backup das versões ativas de `ClientPortal.gs`, `ClientPortal.html`, do projeto Apps Script e da planilha de dados.
2. Comparar arquivos instalados com a **montagem final** do branch, não substituir trechos isoladamente às cegas. Verificar presença do módulo `ClientPortalTreatments.gs` e das quatro funções indicadas.
3. Verificar `tratativas` entre as chaves das permissões internas em `ClientPortal.gs`, no formulário de contas da Central e nas permissões **efetivamente salvas** do usuário cliente.
4. Verificar o vínculo usuário/empresa, publicação de snapshot da empresa e `naoConformidades` para conversas associadas a NC; a conversa GERAL deve depender apenas de `tratativas` e acesso à empresa.
5. Somente com autorização explícita, publicar uma versão de **homologação** isolada do Apps Script e do Painel. Não alterar produção automaticamente.
6. Cliente de teste → Comunicação → Solicitar apoio → escrever assunto real → Enviar → exigir protocolo `treat_...` e mensagem presente ao reabrir.
7. Conta Auditar de teste → Caixa de entrada → verificar recebimento do pedido → responder → cliente recarrega linha do tempo e confirma a resposta.
8. Publicar um snapshot de NC em aberto e outro encerrado **em ambiente de teste**; confirmar que ambas aparecem nas seções certas, que a empresa pode `informar_correcao` na ocorrência e que isso **não encerra** a NC.
9. Testar sessões sem permissão, empresa não vinculada, reenvio, falha de rede, Android e Windows; verificar que nenhum dado de empresa diferente aparece.
10. Registrar evidências e hashes; somente depois decidir publicação final e promover a versão, com plano de reversão.

## Critérios

- Pedido de apoio só disponível ao cliente, e sucesso apenas com confirmação e protocolo do servidor.
- Respostas e correções aparecem no histórico da **mesma empresa e ocorrência**.
- Registros de evento são aditivos; histórico original, NC, planos, fotos, sincronização e PDFs permanecem intactos.
- A Auditar é quem realiza a verificação técnica da eficácia; informar correção não dá baixa automática.
- Ausência de novos registros e contadores zero, isoladamente, não são falha de sincronização.

## Fontes de montagem

- `feature_sources/client_treatment_portal_ui_v1.js`
- `feature_sources/client_treatment_portal_ui_v1.css`
- `feature_sources/ClientPortalTreatments_v1.gs`
- `tools/patch_client_treatment_timeline_v1.py`
- `tools/test_client_treatments_v1.js`

**Pendente:** confirmação do Apps Script ativo e homologação real de ida e volta. Não afirmar que está funcionando no portal publicado antes disso.
