# Minha CIPA — acesso individual seguro | homologação (Android)

Data de referência: 05/11/2026.

## Situação e decisão arquitetural

O APK operacional atual inclui uma `AUDITAR_SYNC_KEY` de sincronização que
seria indevida em um dispositivo distribuído aos integrantes. Por isso,
**o mesmo APK não pode ser entregue ao membro simplesmente escondendo telas**.
O acesso pessoal será um cliente Android **separado, pertencente ao mesmo
ecossistema Auditar SST**, consumindo a Central Online Google Apps Script
atual. **Não depende da Web/VPS do Júlio**.

O projeto de membros tem nome de pacote próprio (`auditar_cipa_membro`).
Nenhum arquivo de técnico, SQLite, fila de fotos, chave mestra, funcionalidade
de IA, exportação total ou `AuthService` entra no código do cliente.

## Recursos preparados em código

| Frente | Código / estado |
|---|---|
| Login individual | Código temporário de 8 dígitos por e-mail, sessão separada de 8h e revogação imediata no backend experimental |
| Identificação | Nome + função na comissão, cargo na empresa somente se confirmado; empresa e mandato |
| Visão Minha CIPA | Reuniões, tarefas próprias, avisos, treinamentos próprios, documentos publicados, observações e lembretes |
| Reuniões | Convocações autorizadas e registro de ciência (não certifica presença/assinatura) |
| Tarefas | Vinculação por ID do integrante; informar andamento e solicitar apoio sem alterar status técnico |
| Inspeção participativa | Observação textual com local para análise do técnico. **Foto ainda pendente** de rota de mídia própria |
| Avisos e lembretes | Lista consultável de avisos liberados e lembretes derivados de reuniões; push automático ainda pendente |
| Documentos | Só informações explicitamente liberadas, sem cópia de PDF/anexo restrito; download autenticado ainda pendente |
| Apoio ao novo membro | Orientações simples e identificação de próximos passos, sem exigir conhecimento da NR |

## Arquitetura de segurança

- `feature_sources/CipaMemberGatewayV1.gs`: backend isolado com contas,
  desafios, sessões, eventos, atribuições, grant/revoke e inbox.
- `feature_sources/cipa_member_server_policy_v1.js`: permissão com negação
  por padrão, igualdade de empresa, mandato, membro e usuário e verificação
  de status a cada requisição.
- A conta pessoal NÃO usa as abas `Usuarios/Sessoes` da autenticação técnica.
  A senha da conta de técnico não é solicitada ao integrante.
- O backend usa sessões tokenizadas de duração limitada; o Android mantém o
  token apenas na memória e não armazena os registros em SQLite.
- Não há modo offline individual nesta fase. Isso evita reaproveitar cache
  administrativo e dados sem controle de revogação.
- Membros não recebem `AUDITAR_SYNC_KEY`, não invocam sincronização geral,
  não gerenciam usuários, não assinam ata por outra pessoa, não declaram
  presença, não decidem embargo/multa, não validam NC e não encerram ações.
- Cada relato possui `requestId` para deduplicação. Admin e técnico devem
  avaliar o conteúdo; relato de andamento é meramente informativo.
- O acesso é conferido no servidor contra cadastro de membro ativo e mandato
  ativo. Troca, revogação ou encerramento deve negar as próximas requisições.
- Os dados de CIPA são coletados somente a partir do registro sincronizado
  com `company_id` explícito, recusando a falta de vínculo.
- Documentos de caráter pessoal/restrito não são liberados por padrão.
- Os endpoints experimentais são bloqueados pelo script property
  `CIPA_MEMBER_V1_ENABLED` enquanto não houver homologação.
- O instalador de GS é opt-in com `--homologacao`, e **não foi aplicado** na
  Central real.

## O que precisa ser verificado com o GS real antes de qualquer ativação

1. Fazer backup do `Code.gs`, `MultiUser.gs`, módulos, planilhas e
   versão de implantação efetivamente publicados.
2. Comparar o contrato real de `SincronizacaoDispositivos` e
   `sst_records.payload_json` com o protótipo; confirmar presença de
   `company_id` e eventos de CIPA sem dados legados ambíguos.
3. Homologar em uma CÓPIA da Central com projeto e planilha fictícios;
   configurar `CIPA_MEMBER_V1_PEPPER` como segredo aleatório de alta
   entropia, sem incluí-lo no APK nem no repositório. Nunca copiar a
   `AUDITAR_SYNC_KEY` para o APK de membros.
4. Garantir rotas expostas exclusivamente por `doPost` com autorização e
   negar chamadas diretas a funções de Apps Script com acesso a dados.
5. Testar pelo menos duas empresas e dois mandatos, diversos membros,
   membro inativo, troca de pessoa, conta revogada durante a sessão,
   código inválido, vencido e simultaneidade.
6. Verificar controles de tentativas/rate limit, concorrência de códigos,
   entrega de e-mail, histórico de eventos, exclusão de registros médicos
   e limitações de quota do Apps Script.
7. Testar vínculo de tarefas e fila de entrada entre o novo cliente, o
   admin Android e a Central sem editar NC por engano.
8. Testar Android em 360/412px e fonte ampliada, refresh, perda de rede,
   login após fechar, logout e inexistência de dados privados em cache.
9. Liberar a primeira empresa somente com autorização da Auditar, backup
   recuperável e estratégia de rollback. A versão instalada de técnicos
   permanece inalterada.

## Pendências impeditivas para afirmar “pronto para produção”

- A implantação da Central real **não foi feita nem validada**.
- O APK de membros (debug) só servirá para testes: sem endpoint configurado,
  o login permanece bloqueado.
- Ainda não há serviço de arquivos/fotos autenticado para membros,
  notificações push, download de PDFs ou fluxo robusto de troca de e-mail.
- O cadastro e os eventos da área individual precisam passar por teste real
  em aparelhos e comparação com o Apps Script publicado antes de habilitar.
- Não há assinatura certificada de ata ou presença automática.

## Fluxo esperado

1. **Admin Auditar** abre CIPA → Acessos dos membros. Cadastra e-mail do
   integrante ativo, vincula tarefas pelo ID do membro e vê relatos recebidos.
2. **Membro** instala “Minha CIPA”, informa seu e-mail e recebe código.
3. A Central revalida conta, empresa, mandato e membro e entrega apenas
   convocações, ações próprias e materiais explicitamente liberados.
4. O membro informa andamento e situações. A gestão analisa e mantém o
   controle técnico; nenhuma NC é encerrada automaticamente.

**Estado: desenvolvimento isolado no GitHub, sem mudança no aplicativo
instalado e sem alteração implantada no Apps Script de produção.**
