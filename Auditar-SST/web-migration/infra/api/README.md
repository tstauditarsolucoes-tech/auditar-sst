# Primeiro serviço de NCs da nova API (isolado, sem login real)

O arquivo `api/ncService.mjs` implementa regras de negócio da futura API do Auditar SST:
- Listar e criar não conformidades por empresa.
- Registrar evento inicial e histórico cronológico.
- Cliente pode informar correção com comentário.
- Apenas técnico/gestor/ADM pode validar ou rejeitar; rejeição exige motivo.
- Transições protegidas por lock `FOR UPDATE`, transação única e eventos preservados.
- Consultas parametrizadas e `SET LOCAL ROLE sst_app_runtime` + `app.company_id` em cada transação.

`api/server.mjs` define endpoints `/api/v1/nonconformities`, `/:id/events`, `/:id/correction`, `/:id/decision`. **Sem um verificador de sessão real injetado no servidor, todas essas rotas retornam 401 e NÃO acessam informações.** Headers como `x-role` e `x-company-id` são ignorados: não é possível fingir uma identidade pelo navegador.

Os testes `api/ncService.test.mjs` e `api/server.test.mjs` exercitam a lógica com banco simulado. **A CI agora também executa `api/integration.ci.test.mjs` contra PostgreSQL 17 REAL, efêmero e sem dados de clientes**, usando o usuário de teste sem SUPERUSER nem BYPASSRLS e duas empresas fictícias: criação, listagem, correção, rejeição, validação, histórico e isolamento. A seed `db/tests/seed_nc_integration_ci.sql` tem bloqueios para não ser aplicada em banco real/persistente. **Ainda não existe conexão de produção, login, token ou sessão.**

## Como será integrado com segurança

1. Implementar autenticação nova revisada para a web e adaptadores autenticados Android/Windows, sem substituir a Central Online antes dos testes.
2. Resolver a sessão em objeto interno verificado `{companyId,userId,role}` a partir de identidade real e vínculos no banco; nunca dos campos enviados pelo cliente.
3. Configurar `pg.Pool` usando conta PostgreSQL NÃO superuser, secret separado, TLS conforme ambiente e concessão mínima de `sst_app_runtime`.
4. Injetar ambos no startup do servidor: `createApp({pool, resolvePrincipal})`. **Isto ainda não foi implementado no entrypoint de hospedagem**.
5. Expandir os testes API×PostgreSQL CI já existentes para identidade real, sessões, auditoria, concorrência, evidências e autenticação, sem usar a seed fictícia em dados persistentes.
6. Homologar comportamento offline, fotos/assinaturas, backups e migração de dados antes do domínio final.

O que está no GitHub é uma base de negócio e um contrato HTTP protegido por padrão. **Não afirmar que o CRUD real está acessível na VPS ou que o sistema está pronto para produção.**


## Nova autenticação web — migração 002 (SOMENTE homologação)

`infra/db/migrations/002_web_auth.sql` cria credenciais com scrypt e sessões contendo apenas hash SHA-256 do token. O novo `api/authService.mjs` valida e-mail/senha, vínculo ativo por empresa e revogação; usa cookie `__Host-` com `HttpOnly`, `Secure`, `SameSite=Lax`, `Path=/` e expiração de 8 horas, mais checagem de `Origin` HTTPS fixo e token CSRF nas mutações. A seleção de empresa consulta o vínculo real na nova base a cada troca. O role `sst_auth_runtime` recebe acesso às tabelas de autenticação **mas não a vistorias e NCs**, enquanto `sst_app_runtime` não lê senhas/sessões. São conexões separadas.

**CI:** `api/integration.auth.ci.test.mjs` testa o login apenas com usuário/senha de exemplo (`example.invalid`) em PostgreSQL efêmero, autorizações, CSRF, isolamento entre empresas, troca de vínculo e logout. A seed `db/tests/seed_auth_integration_ci.sql` não deve ser usada na VPS.

**Não habilitado no contêiner entregue:** o `server.mjs` continua chamando `createApp()` sem pools nem `authService`; assim, endpoints de login/NC retornam 401 por padrão. O overlay opt-in de homologação já configura as duas contas DB segregadas, URL HTTPS de teste e proteção por Origin/CSRF; foi incluído limite inicial de 10 tentativas de login por identidade/15min. Ainda faltam medidas de produção: auditoria independente, proteção de borda NPM Access List, recuperação de senhas, MFA/controles de contas, logs de segurança, manutenção de sessões, backups e testes físicos. Nenhuma conta legada foi importada. **Isto não é login de produção.**


O frontend React inclui `web/src/WebAuthPilot.tsx`, aba **Acesso de homologação**, preparada para consumir estas rotas com cookie HttpOnly, token CSRF e troca de empresa. Como o entrypoint não habilita auth, a aba exibe uma orientação de configuração e não aceita contas reais. Ações nessa aba só terão efeito no banco NOVO de homologação quando o backend for ativado intencionalmente, diferentemente dos demais exemplos do protótipo.


## Ativação privada opcional para Júlio

`api/server.bootstrap.mjs` é um segundo entrypoint **opt-in** que só inicia com `AUDITAR_ENABLE_PRIVATE_AUTH=PRIVATE_STAGING_CONFIRMED`, HTTPS de homologação distinto do domínio final, dois secrets Docker de banco (copiados de forma efêmera a tmpfs por `private-entrypoint.sh`, seguido de redução de privilégios para `node`), conexões não-superuser separadas e `sst_auth_runtime`/`sst_app_runtime` validados. O padrão `server.mjs` segue sem auth/banco. A migração `003_auth_login_limit.sql` registra tentativas por hash da identidade, janela de 15 minutos e máximo de 10. `db/scripts/create_private_roles.sh` cria roles sem expor senhas em linha de comando, `scripts/provision-first-admin.sh` cria só conta fictícia inicial e `scripts/preflight-private.sh` faz validação sem deploy. Instruções completas: [GUIA_PRIVADO_JULIO.md](../GUIA_PRIVADO_JULIO.md). Não ativar sem NPM Access List e TLS.


## Vistorias/Ronda Expressa — piloto web (migração 004)

`api/inspectionService.mjs` expõe listagem, detalhes com achados/histórico, abertura de rascunho, edição com `expectedRevision` para impedir sobrescrita, inclusão de achado com título amigável de NC, e conclusão. As rotas são `GET/POST /api/v1/inspections`, `GET/PATCH /api/v1/inspections/:id`, `POST /api/v1/inspections/:id/findings`, `POST /api/v1/inspections/:id/complete`. Criação de vistoria e achados exigem `clientRequestId` UUID estável para repetição segura de envio. Clientes não veem rascunhos; apenas técnico/gestor/ADM grava ou conclui. Auditoria de eventos e revisão ficam no banco novo; RLS e autenticação/cookies/CSRF seguem obrigatórios. **Sem integração offline real dos apps Flutter, sem envio de fotos, IA e sem migração de dados legados.** O teste `integration.inspections.ci.test.mjs` usa somente CI efêmera.


## Agenda SST — piloto isolado (migração 005)

`api/taskService.mjs` gerencia tarefas por empresa com título, prioridade, prazo, técnico designado, revisões, histórico e transições abertas→em andamento→concluída/cancelada (cancelamento exige motivo). Gestor/ADM pode atribuir a membros ativos **da mesma empresa**; técnico pode criar para si, ver suas tarefas e alterar andamento quando designado; cliente não acessa a agenda interna. RLS das identidades visíveis à API foi adicionado sem liberar credenciais, e `clientRequestId` evita duplicações. Rotas `GET/POST /api/v1/tasks`, `GET /api/v1/tasks/assignees`, `GET/PATCH /api/v1/tasks/:id`, `POST /api/v1/tasks/:id/status`. Apenas homologação, sem importação de agenda legada e sem notificação/tempo online real.


## Portal do Cliente e Central ADM web — piloto (migração 006)

portalService.mjs cria solicitações de apoio, mensagens com histórico imutável e encerramento/reabertura; valida sempre empresa e vínculo da sessão. Clientes consultam somente tickets que criaram; equipe técnica consulta tickets da empresa ativa. GET /api/v1/portal/dashboard destaca NCs não validadas por pontuação de risco e últimas tratativas. Rotas /api/v1/portal/threads suportam listagem/criação/detalhes/mensagens/encerramento e reabertura. Opera com idempotência UUID nas criações. Escritas exigem sessão, Origin e CSRF. GET /api/v1/admin/overview e /team são só para gestor/ADM da empresa selecionada. POST /api/v1/activity/ping registra atividade apenas desta web nova, jamais detecta app Flutter. Migration 006 inclui RLS forçado e FKs multiempresa. Testes: integration.portal.ci.test.mjs. Sem fotos, chat legado, notificações ou criação de contas reais nesta etapa.


## Fotos no volume privado (piloto 007)

api/evidenceService.mjs grava somente JPEG/PNG/WebP fictícios de até 2 MB no volume novo configurado no bootstrap HTTPS privado; arquivo tem nome aleatório, verificação básica do formato, SHA-256 e chave de idempotência. Os metadados ficam em sst.evidence, cujo tenant RLS está ativo desde 001. Endpoints GET /api/v1/evidence?inspectionId=UUID (ou nonConformityId), POST /api/v1/evidence e GET /api/v1/evidence/:id/content. Sem configuração de volume, a API nega o acesso. Não há mídia pública, uso do Drive, migração de fotos/assinaturas antigas ou assinatura digital nesta fase. Atenção a possíveis arquivos órfãos por falha após gravação: reconciliar e testar backup/restauração antes de produção.


## PDF em memória de vistoria concluída (piloto)

api/reportService.mjs usa a nova base PostgreSQL/Node, sem fontes legadas. GET /api/v1/reports/inspections/:id/pdf exige sessão, tenant e vistoria concluída; gera relatório resumido em PDF com página de capa, até dois achados/página e foto JPEG/PNG opcional vinda do volume privado. Download direto pelo navegador, sem window.print. Arquivo não persiste em disco, sem Drive, assinatura digital, log de envio ou nome/logo oficial. Não confundir com Padrão Auditar 3 homologado. Limite 30 NCs e 24 MiB para reduzir risco de consumo excessivo; requer revisar paginação, fontes e layout em aparelhos reais.


## Plano de Ação Web (migração 008)

`actionPlanService.mjs` implementa lista, detalhe, criação idempotente, edição por revisão e mudança de status com histórico. A API exige sessão Web NOVA e CSRF para mutações; cliente não acessa plano interno; técnico só atua como responsável ou criador, gestor/ADM atribui e edita. Filtragem e FK `company_id` protegem a separação de empresas. `GET/POST /api/v1/action-plans`, `GET/PATCH /api/v1/action-plans/:id`, `POST /api/v1/action-plans/:id/status`. Página `ActionPlanPilot.tsx` aparece dentro do acesso autenticado de homologação. A integração `integration.action-plans.ci.test.mjs` cria exclusivamente NCs e planos fictícios e verifica RLS, papéis, idempotência e eventos. **Ainda não substitui os Planos de Ação Flutter/Apps Script nem é homologação funcional final.**


## Treinamentos e DDS Web (migração 009)

`trainingService.mjs` suporta `GET/POST /api/v1/training-sessions`, `GET/PATCH /api/v1/training-sessions/:id` e `POST /api/v1/training-sessions/:id/status`. A área `TrainingPilot.tsx` só aparece para perfis internos autenticados; cliente recebe 403 também na API. Gestor/ADM e criador técnico podem alterar registros planejados e informar realização ou cancelamento com motivo. Todo acesso usa tenant de sessão verificado, com RLS e chave idempotente. Para marcar realizado, o usuário deve informar duração e número de participantes; essa informação é **autodeclarada e não comprova presença nem certificação**. Sem participantes identificáveis, upload de certificados, e-mail, importação legado ou comprovação de requisitos legais nesta etapa. Teste efêmero: `integration.training.ci.test.mjs`.


## CIPA Web — piloto 010

`cipaService.mjs` e `CipaPilot.tsx` permitem cadastrar mandato fictício, composição (empregados/empregador/designado, titular/suplente), reunião, resumo de reunião e transições administrativas do mandato. Rotas protegidas: `GET/POST /api/v1/cipa/mandates`, `GET /api/v1/cipa/mandates/:id`, `POST /api/v1/cipa/mandates/:id/members`, `POST /api/v1/cipa/mandates/:id/meetings`, `POST /api/v1/cipa/meetings/:id/status`, `POST /api/v1/cipa/mandates/:id/status`. A aplicação exige sessão verificada, Origin, CSRF nas escritas e RLS multiempresa. Cliente recebe 403; mudança de status do mandato é reservada a gestor/ADM. **Não é módulo de eleição, certificação, ata assinada ou conformidade NR-5.** Teste PostgreSQL fictício em `integration.cipa.ci.test.mjs`.


## PDF ampliado e recomendação de NC — piloto 011

A criação de achado em `POST /api/v1/inspections/:id/findings` aceita `recommendation` opcional (até 1600 caracteres), com controle de idempotência. `GET /api/v1/reports/inspections/:id/pdf` apresenta até dois quadros de NC por página e anexo fotográfico ampliado, com no máximo duas imagens por página e **apenas a primeira JPEG/PNG de cada NC**. O gerador não importa fotografias do legado nem grava PDF no Drive. Ainda trunca a visualização de texto excessivamente longo em cartões e não possui modelo Padrão Auditar 3 aprovado, assinatura e checklist completo. Não utilizar em documento oficial.


## Minuta de lista de participantes — piloto 012

`POST /api/v1/training-sessions/:id/participants` registra nome fictício, `presence` como `nao_confirmada` ou `declarada`, observação curta e UUID de envio; somente criador/gestor/ADM no tenant autenticado. `GET /api/v1/training-sessions/:id` retorna `attendance` para a equipe. `GET /api/v1/reports/trainings/:id/attendance.pdf` gera minuta paginada com faixa de advertência explícita: **não comprova presença**. Nenhuma assinatura/certificado/credencial profissional é gerada, e dados legados não são importados. Ver CI `integration.training-attendance.ci.test.mjs`.


## Layout PDF sem perda de trechos visíveis (homologação)

`reportTextPagination.mjs` calcula quanto texto cabe em cada área pelo PDFKit e devolve o excedente sem descartar caracteres; `reportService.mjs` renderiza continuações do resumo e dos achados em páginas dedicadas. O PDF apresenta até 2 achados por página de resumo e até 2 fotos privadas por NC, cada uma numa página ampliada. `reportTextPagination.test.mjs` verifica a preservação de texto longo, inclusive sem espaços; `integration.reports.ci.test.mjs` usa descrição longa, recomendação longa, duas imagens sintéticas e testa isolamento entre empresas.

Não se trata de relatório oficial Padrão Auditar 3, que ainda exige revisão visual, identidade corporativa definitiva, documentos de assinatura e aprovação técnica. Não reutilizar dados do sistema antigo.


## Piloto 013 — Autenticação nativa separada e inativa por padrão

`nativeAuthService.mjs` introduz somente login nativo com credenciais NOVAS da homologação (scrypt), controle persistente de tentativas, sessão revogável com bearer de 256 bits e hash de token no PostgreSQL. `POST /api/v1/native/auth/login` aceita somente `email` e `password`; `GET /api/v1/native/auth/session` e `POST /api/v1/native/auth/logout` exigem bearer. Sem Origin/cookie. Ativação apenas por variável explícita `AUDITAR_ENABLE_NATIVE_AUTH=PRIVATE_STAGING_NATIVE_ONLY` no servidor de homologação privada. **Não implementa API de dados, sincronização, envio de fotos, login Flutter conectado nem suporte de produção.** Os demais serviços ignoram tokens nativos. Teste `integration.native-auth.ci.test.mjs` com PostgreSQL efêmero e contas fictícias.


## Consultas nativas protegidas (sem sync)

O token opt-in 013 pode consultar **somente** `GET /api/v1/native/data/nonconformities` e `GET /api/v1/native/data/inspections`; ambas chamam serviços existentes com `principal()` validado na tabela `native_session` e isolamento por empresa RLS. Não existe criação, alteração, importação, upload de mídia nem ACK de fila offline pelo token. Qualquer tentativa de escrita recebe 405. O código Flutter instalado não utiliza estas URLs.
