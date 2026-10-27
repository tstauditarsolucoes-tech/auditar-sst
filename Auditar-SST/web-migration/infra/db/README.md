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
