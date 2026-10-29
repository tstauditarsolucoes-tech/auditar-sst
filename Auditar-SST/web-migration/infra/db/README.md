# Banco PostgreSQL próprio — migrações isoladas de homologação

Este módulo é o **primeiro esquema real de dados para o NOVO servidor**. **Não migra dados antigos e não modifica Apps Script, Drive, Android ou Windows.** O banco de staging continua sem empresas reais.

## O que foi implementado

`migrations/001_initial.sql` cria tabelas para empresas, identidades de referência, vínculos/perfis, vistorias, NCs, tratativas, evidências (somente metadados), tarefas e eventos de auditoria. IDs UUID, chaves estrangeiras compostas (empresa + entidade) e índices por empresa são usados para impedir associações indevidas.

RLS (segurança por linhas) limita o role separado **`sst_app_runtime`** ao `app.company_id` da transação. O role não tem login, senha nem acesso à tabela global de usuários. **Isto NÃO implementa autenticação.** A futura API, depois de validar a sessão e o vínculo de cada usuário, deve definir `SET LOCAL app.company_id` num contexto transacional usando role de banco de privilégios mínimos; clientes não escolhem tenant por conta própria.

Os eventos de tratativa/auditoria são somente inseríveis pelo role runtime (sem UPDATE ou DELETE). Fluxos de trabalho e transições de estados ainda exigem lógica e testes de API.

**Importante:** o usuário configurado em `POSTGRES_USER` pelo Compose é superusuário destinado a inicialização e migração. **Jamais usar essas credenciais na API de produção** — criar conta de aplicação NÃO SUPERUSER, restrita por grants e política RLS e com segredo separado. É necessário revisar hardening, backup e migrações antes da produção.

## Como testar em homologação sem dados reais

Os testes automatizados da GitHub Actions iniciam um PostgreSQL novo e isolado, executam migrações 001 e 002, criam dados fictícios e validam:
- Sem empresa definida: nenhuma vistoria fica visível;
- Empresa A: não vê registros da B;
- Empresa A: não consegue inserir vistoria B;
- FKs compostas rejeitam NC associada a vistoria de outra empresa;
- Role de runtime não lê contas globais de usuários;
- ROLLBACK elimina todos os dados fictícios do teste.

Em uma **nova** instância de homologação explicitamente autorizada, na pasta `infra`, após os contêineres estarem saudáveis:

```bash
docker compose -p auditar-sst-web-hml -f compose.staging.yml exec -T db \
  psql -U auditar_web_hml -d auditar_web_hml -v ON_ERROR_STOP=1 -f /db-init/migrations/001_initial.sql

docker compose -p auditar-sst-web-hml -f compose.staging.yml exec -T db \
  psql -U auditar_web_hml -d auditar_web_hml -v ON_ERROR_STOP=1 -f /db-init/tests/tenant_isolation.sql
```

**A migração só pode ser aplicada uma vez por banco** e contém guarda de versão. Nunca executá-la num volume que já contenha informações da Auditar sem backup, revisão e autorização; não usar `down --volumes` para “limpar” tentativas.

## Ainda falta

- Ativação segura do NOVO login web (módulo e teste CI criados, mas sem contas reais/entrypoint), provisionamento de contas, rate limiting e auditoria de autenticação; ampliar API SST.
- Conta runtime não superuser e separação operacional entre migrador e API.
- Armazenamento privado de bytes de foto/assinatura/PDF, antivírus/validação, backups criptografados fora da VPS.
- Migração verificada de dados legados, endereçamento dos arquivos offline, idempotência/conflitos e testes dos três clientes.
- Revisão de segurança independente e ensaio de restauração antes de publicar o sistema.


## Migração 002 — login WEB isolado (não é migração de senhas antigas)

`migrations/002_web_auth.sql` adiciona `sst.auth_credential` (verificador scrypt, nunca senha em claro), `sst.auth_session` (apenas hash SHA-256 de token, revogação/expiração) e `sst_auth_runtime`. Este role NÃO consulta NCs/vistorias. O role SST existente NÃO tem concessão de leitura a credenciais/sessões. A autenticação de homologação usa `SET LOCAL ROLE sst_auth_runtime` em transação e conexão distinta da API de NC.

**Apenas num banco novo de homologação**, após aplicar 001 e antes de testes fictícios, aplicar 002 com usuário de MIGRAÇÃO autorizado. NÃO executar `seed_auth_integration_ci.sql` na VPS: contém identidades e senha sintéticas públicas para teste automático descartável. Não criar usuários reais sem um processo auditado de provisionamento e recuperação. Sem autenticação habilitada em produção nem migração da Central Online.


## Migração 003 — proteção básica de login

`migrations/003_auth_login_limit.sql` cria `sst.auth_login_counter` (hash SHA-256 do email normalizado, contagem/janela/atualização) e grants restritos ao role de autenticação. O serviço recusa a 11ª tentativa da mesma identidade em 15 minutos e limpa o contador após login correto. Não é defesa completa contra ataques distribuídos: manter controle de acesso privado no proxy e revisar segurança antes de produção.

**Provisionamento:** `db/scripts/create_private_roles.sh` só roda dentro do contêiner PostgreSQL de homologação e cria papéis separados quando as migrações 001–003 existem. Nunca passar senha como argumento de comando; segredos Docker locais `data_db_password` e `auth_db_password`. O primeiro administrador fictício é criado por `scripts/provision-first-admin.sh` apenas se a base SST estiver vazia. Ver [../GUIA_PRIVADO_JULIO.md](../GUIA_PRIVADO_JULIO.md).


## Migração 004 — vistorias da homologação

Aplicar **após** 001/002/003, somente no banco novo `auditar_web_hml`, uma vez. Acrescenta setor/local, versão de rascunho, conclusão, idempotência de envio, nome amigável da NC e linha do tempo imutável das vistorias. O `sst_app_runtime` recebe apenas operações da empresa selecionada via RLS; perfis `cliente` só leem vistorias concluídas pela API. Sem fotos, assinaturas, PDF ou dados de clientes importados nesta fase.


## Migração 005 — Agenda e validação de equipe (homologação)

Somente após 001–004 em base nova: prioridades, prazos, atribuição, revisão e idempotência de tarefas; RLS para nomes e vínculos de funcionários da empresa ativa, sem expor dados de usuários de outras empresas. O autenticador mantém role separado para credenciais, e a API de tarefas usa somente a role de dados com `SET LOCAL`. Eventos de tarefa não são substituídos. Sem sincronização real de agenda Flutter nesta etapa.


## Migração 006 — portal e supervisão web isolados

Em banco NOVO, aplicar após 005: migrations/006_client_portal_admin.sql. Cria support_thread, support_message (append-only para runtime) e web_user_activity, com FKs de tenant e RLS forçado. Backend controla cliente dono do ticket, status e gestão por empresa. Não conecta Apps Script, Drive, fotos ou usuários existentes. Não executar migração em volume com dados reais sem backup, revisão e aprovação.


## Migração 007 — metadados de arquivo privado

Somente em banco novo com 001–006 concluídas: adiciona client_request_id idempotente aos metadados de sst.evidence. Os bytes ficam no volume do Docker, não no PostgreSQL. RLS de evidências da migration 001 continua em vigor. Banco e volume precisam de backup consistente e ensaio de restauração antes de migração de dados reais.


## Migração 008 — Plano de Ação Web somente de homologação

`008_action_plan_pilot.sql` depende das migrações 001–007 no **banco novo**. Cria `sst.action_plan` vinculado por FK composta à NC da mesma empresa, responsável ativo por vínculo de empresa, prazo, status, revisão otimista, chave de envio e impressão digital de criação. O histórico em `sst.action_plan_event` registra alterações e idempotência de mudança de status. As duas tabelas têm `ENABLE/FORCE ROW LEVEL SECURITY` e recebem permissões apenas do role restrito da API. **Não cria nem migra plano de ação legado; não executar na Central atual.**


## Migração 009 — Treinamentos, DDS e Integração (somente Web de homologação)

Executar depois da migração 008 e somente em PostgreSQL NOVO de teste, uma vez. `009_training_sessions_pilot.sql` cria `sst.training_session` e `sst.training_event`, associadas à empresa, com RLS forçado e histórico somente para inclusão pela API. Os registros incluem tipo, tema, setor, NR de referência, instrutor, data, duração e contagem informada de participantes, mas **não substituem comprovantes/certificados/listas de presença** e não migram qualquer treinamento anterior. Dados reais de colaboradores não devem ser usados no piloto.


## Migração 010 — CIPA Web (somente teste privado)

`migrations/010_cipa_pilot.sql` depende de 001–009 e acrescenta `sst.cipa_mandate`, `sst.cipa_member`, `sst.cipa_meeting` e `sst.cipa_event`, com chaves (empresa, entidade), RLS obrigatório e trilha de eventos append-only. As tabelas representam **somente controles administrativos**; não processam votos, não aplicam cálculo da NR-5, não importam dados reais e não validam documentos oficiais.


## Migração 011 — Recomendação técnica separada no achado da vistoria Web

`011_nc_recommendation_pdf.sql` depende de 001–010 e acrescenta `recommendation` opcional à tabela de NC para orientar o relatório PDF de homologação. Nada é preenchido automaticamente por IA, e NCs antigas de teste permanecem com recomendação vazia. A mudança não migra dados nem edita Apps Script, Drive ou Flutter.


## Migração 012 — Participantes declarados, sem assinatura

Apenas PostgreSQL NOVO de homologação. `012_training_attendance_draft.sql` depende de 001–011. Cria `sst.training_attendance` (até 100 por evento via API) com FK composta empresa/treinamento, RLS forçado e somente inclusão para o runtime. **Não contém certificado, CPF, assinatura ou prova de comparecimento** e não importa dados de Apps Script/Drive. Não carregar nomes reais até homologação jurídica/técnica e procedimentos LGPD.


## Migração 013 — Token separado para futura autenticação Android/Windows

Executar no PostgreSQL NOVO de testes após 001–012. `013_native_auth_pilot.sql` cria `sst.native_session` com token armazenado por hash SHA-256, expiração de 30 minutos, revogação, chaves empresa/usuário e grants apenas ao `sst_auth_runtime`. Nenhum dado de autenticação Flutter/Apps Script é importado. Ainda NÃO há protocolo de sincronização nativo e o serviço está desligado por padrão, inclusive em homologação privada.
