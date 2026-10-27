# Banco PostgreSQL próprio — primeira migração de homologação

Este módulo é o **primeiro esquema real de dados para o NOVO servidor**. **Não migra dados antigos e não modifica Apps Script, Drive, Android ou Windows.** O banco de staging continua sem empresas reais.

## O que foi implementado

`migrations/001_initial.sql` cria tabelas para empresas, identidades de referência, vínculos/perfis, vistorias, NCs, tratativas, evidências (somente metadados), tarefas e eventos de auditoria. IDs UUID, chaves estrangeiras compostas (empresa + entidade) e índices por empresa são usados para impedir associações indevidas.

RLS (segurança por linhas) limita o role separado **`sst_app_runtime`** ao `app.company_id` da transação. O role não tem login, senha nem acesso à tabela global de usuários. **Isto NÃO implementa autenticação.** A futura API, depois de validar a sessão e o vínculo de cada usuário, deve definir `SET LOCAL app.company_id` num contexto transacional usando role de banco de privilégios mínimos; clientes não escolhem tenant por conta própria.

Os eventos de tratativa/auditoria são somente inseríveis pelo role runtime (sem UPDATE ou DELETE). Fluxos de trabalho e transições de estados ainda exigem lógica e testes de API.

**Importante:** o usuário configurado em `POSTGRES_USER` pelo Compose é superusuário destinado a inicialização e migração. **Jamais usar essas credenciais na API de produção** — criar conta de aplicação NÃO SUPERUSER, restrita por grants e política RLS e com segredo separado. É necessário revisar hardening, backup e migrações antes da produção.

## Como testar em homologação sem dados reais

Os testes automatizados da GitHub Actions iniciam um PostgreSQL novo e isolado, executam a migração 001, criam dados fictícios dentro de uma transação e validam:
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

- API Node com login/autorização real, regras de mudança de status, transações, validação e auditoria.
- Conta runtime não superuser e separação operacional entre migrador e API.
- Armazenamento privado de bytes de foto/assinatura/PDF, antivírus/validação, backups criptografados fora da VPS.
- Migração verificada de dados legados, endereçamento dos arquivos offline, idempotência/conflitos e testes dos três clientes.
- Revisão de segurança independente e ensaio de restauração antes de publicar o sistema.
