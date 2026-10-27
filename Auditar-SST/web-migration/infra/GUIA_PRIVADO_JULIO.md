# Auditar SST — Homologação PRIVADA para Júlio (sem trocar o domínio atual)

**Data:** 27/10/2026. **Somente branch** `migration/preparacao-web-20261027`, PR #23 DRAFT.  
Este é um pacote de **primeiro teste com dados inteiramente fictícios**, não a versão final do Auditar SST.

## Objetivo

Testar no navegador a nova interface React, login por cookie seguro, seleção de empresa, vistorias em rascunho, achados, NCs, correções e histórico usando API Node e PostgreSQL **do ambiente de teste**. Android, Windows, Central Online, Apps Script, Google Drive e suas fotografias/assinaturas permanecem intactos.

**Nunca substituir o Proxy Host de `tst.auditarsolucoes.com.br` agora.** O bootstrap inclusive recusa esse hostname. Escolher URL HTTPS NOVA e privada de homologação, com DNS/certificado sob responsabilidade do administrador. Não supor que um subdomínio de teste já existe.

## Pré-requisitos do Júlio

- VPS compartilhada com Docker Compose v2, capacidade de disco/memória e rede de Nginx Proxy Manager identificadas.
- Permissão para criar **apenas** os serviços `auditar-sst-web-hml`, volumes/redes exclusivos, sem modificar contêineres existentes.
- Hostname exclusivo de homologação, certificado TLS válido e **NPM Access List** restringindo a equipe de testes (IP, acesso autenticado ou VPN).
- Código auditado, segredos locais com permissão `600` e nenhum dado pessoal/real de clientes.
- Cópia de segurança e plano de rollback antes de qualquer mudança futura em produção.

## 1. Obter branch de desenvolvimento

Em diretório **novo** e separado da implantação atual:

```bash
git clone https://github.com/tstauditarsolucoes-tech/auditar-sst.git
cd auditar-sst
git switch migration/preparacao-web-20261027
cd Auditar-SST/web-migration/infra
```

Se já existir clone, contêiner ou volume com esse projeto, **parar e inventariar**, sem sobrescrever.

## 2. Criar três segredos privados fora do Git

```bash
install -d -m 0700 secrets
umask 077
openssl rand -base64 48 > secrets/postgres_password
openssl rand -base64 48 > secrets/data_db_password
openssl rand -base64 48 > secrets/auth_db_password
chmod 600 secrets/postgres_password secrets/data_db_password secrets/auth_db_password
```

O primeiro segredo pertence **somente ao migrador/superusuário de homologação**; os outros serão dados a contas não-superuser distintas, sem exposição no frontend.

Definir no terminal (valores reais verificados pelo Júlio):

```bash
export AUDITAR_ALLOWED_ORIGIN=https://SUBDOMINIO-PRIVADO-DE-HOMOLOGACAO
export AUDITAR_NPM_NETWORK=NOME-REAL-DA-REDE-DO-NPM
bash scripts/preflight-private.sh
```

Se a verificação falhar, **não iniciar nada**. Ela exige URL HTTPS diferente do domínio final, segredos locais e nenhum host port publicado.

## 3. Criar o banco SOMENTE de homologação

Começar com o Compose **padrão, sem login**; isto cria apenas os serviços dedicados e mantém a API bloqueada.

```bash
docker compose -p auditar-sst-web-hml -f compose.staging.yml up --build -d --wait
```

Só num banco **novo e vazio**, aplicar migrações 001, 002, 003, 004, 005 e 006 nessa ordem, uma única vez:

```bash
docker compose -p auditar-sst-web-hml -f compose.staging.yml exec -T db \
  psql -U auditar_web_hml -d auditar_web_hml -v ON_ERROR_STOP=1 -f /db-init/migrations/001_initial.sql

docker compose -p auditar-sst-web-hml -f compose.staging.yml exec -T db \
  psql -U auditar_web_hml -d auditar_web_hml -v ON_ERROR_STOP=1 -f /db-init/migrations/002_web_auth.sql

docker compose -p auditar-sst-web-hml -f compose.staging.yml exec -T db \
  psql -U auditar_web_hml -d auditar_web_hml -v ON_ERROR_STOP=1 -f /db-init/migrations/003_auth_login_limit.sql

docker compose -p auditar-sst-web-hml -f compose.staging.yml exec -T db \
  psql -U auditar_web_hml -d auditar_web_hml -v ON_ERROR_STOP=1 -f /db-init/migrations/004_inspections_pilot.sql

docker compose -p auditar-sst-web-hml -f compose.staging.yml exec -T db \
  psql -U auditar_web_hml -d auditar_web_hml -v ON_ERROR_STOP=1 -f /db-init/migrations/005_agenda_pilot.sql

docker compose -p auditar-sst-web-hml -f compose.staging.yml exec -T db \
  psql -U auditar_web_hml -d auditar_web_hml -v ON_ERROR_STOP=1 -f /db-init/migrations/006_client_portal_admin.sql
```

**Não executar** arquivos em `db/tests/seed_*.sql` na VPS. Eles contêm identidades e senhas fictícias públicas **exclusivas da CI descartável**.

## 4. Criar papéis distintos e ativar API privada

Primeiro remontar só o banco deste projeto com os dois novos segredos; o volume é preservado:

```bash
docker compose -p auditar-sst-web-hml -f compose.staging.yml -f compose.private-auth.example.yml \
  up -d --no-deps --wait db

docker compose -p auditar-sst-web-hml -f compose.staging.yml -f compose.private-auth.example.yml \
  exec -T db sh /db-init/scripts/create_private_roles.sh
```

O script recusa roles existentes e não redefine senhas silenciosamente. Ele cria:
- `sst_web_data_hml`: somente operações SST com `sst_app_runtime` e escopo por empresa;
- `sst_web_auth_hml`: somente sessões/credenciais com `sst_auth_runtime`.

Agora ativar **somente API** privada, que verifica o HTTPS configurado, papéis não-superuser e segredos. O script `private-entrypoint.sh` inicia brevemente como root apenas para copiar os segredos legíveis por root para um `tmpfs` efêmero, restringe-os ao usuário `node` e **descarta privilégios antes de iniciar o servidor Node**. Os segredos originais permanecem `0600` e a API não usa um filesystem persistente para essa cópia:

```bash
docker compose -p auditar-sst-web-hml -f compose.staging.yml -f compose.private-auth.example.yml \
  up --build -d --no-deps --wait api
```

Se a API não ficar saudável, consultar logs sem copiar senhas para chats ou arquivos públicos; manter o DNS/proxy atual intocado.

## 5. Criar somente o primeiro usuário FICTÍCIO de teste

```bash
export AUDITAR_PROVISION_FIRST_ADMIN=CONFIRM_PRIVATE_STAGING
bash scripts/provision-first-admin.sh
unset AUDITAR_PROVISION_FIRST_ADMIN
```

Informe empresa com nome iniciando por **TESTE**, nome fictício, e-mail `@example.invalid` e senha NOVA de homologação. O script recebe a senha sem ecoá-la no terminal, gera um verificador scrypt e só permite execução na base vazia de homologação. Não reutilizar senha do app existente.

## 6. Conectar somente o frontend ao Nginx Proxy Manager

Após conferir rede e **NPM Access List**:

```bash
docker compose -p auditar-sst-web-hml -f compose.staging.yml \
  -f compose.private-auth.example.yml -f compose.npm.example.yml \
  up -d --no-deps web
```

Criar um Proxy Host **novo** para a URL privada:
- Forward Hostname: `auditar-sst-web-hml`
- Forward Port: `8080`
- Scheme interno: `http` pela rede NPM dedicada
- SSL/TLS válido, HTTPS obrigatório e Access List de homologação

**Não** abrir portas do host, não expor DB/API, não reutilizar o Proxy Host de `tst.auditarsolucoes.com.br`, não mexer nos outros sistemas.

## 7. Testar com o Júlio

- Abrir a URL privada HTTPS e a aba **Acesso de homologação**.
- Entrar com o usuário fictício criado e selecionar a empresa.
- Criar uma vistoria fictícia, incluir achado/NC, concluir e verificar o histórico; depois informar correção, rejeitar com motivo e validar.
- Criar tarefa de agenda fictícia; gestor atribui a técnico, técnico inicia/conclui e registra comentário. Verificar que outra empresa não lê tarefas.
- Abrir solicitação de apoio no painel do cliente, responder como técnico, encerrar e reabrir; verificar que empresa B não vê os tickets de A.
- Registrar correção de NC no painel e validar/rejeitar pela equipe; verificar que somente gestor/ADM vê a Central Administrativa.
- Conferir atividade Web recente na Central ADM (não indica presença do Android/Windows) e a troca de empresa.
- Repetir o envio da vistoria com a mesma chave e confirmar que não gera duplicatas; testar rascunho em duas abas.
- Conferir histórico e verificar que outra empresa não vê os dados anteriores.
- Sair/entrar e conferir expiração/negação de sessões revogadas.
- Conferir consumo de memória, backups, logs e limites de tentativas de login.
- Testar no PC e celular; verificar que a tela original de demonstração não foi alterada.

A CI automatizada já simula boa parte desse fluxo no PostgreSQL real **descartável**, mas não substitui a homologação física com NPM/SSL da VPS.

## 8. Segurança e reversão

- Limitação básica de 10 tentativas por identidade em janela de 15 minutos. Manter NPM Access List e outras proteções na borda; ainda requer auditoria de segurança antes de acesso amplo.
- Novas sessões usam cookies Secure/HttpOnly/SameSite, controle de Origin e CSRF, 8h de validade; não armazenam token bruto no DB.
- Contêiner padrão continua fechado. **Só** o overlay `compose.private-auth.example.yml` ativa o bootstrap, e ele bloqueia o domínio definitivo.
- Para parar apenas o sistema de TESTE, preservar volumes:

```bash
docker compose -p auditar-sst-web-hml -f compose.staging.yml \
  -f compose.private-auth.example.yml -f compose.npm.example.yml stop
```

- Não utilizar `down -v`, `docker system prune`, limpeza de volumes, alteração de DNS ou exclusão do sistema errado sem novo inventário e autorização.

### Ainda NÃO entregue em produção

Vistorias/agenda/painel do cliente/ADM são apenas pilotos isolados, não estão integralmente migrados ao Node/Web; PDF/fotos/assinaturas ainda não estão migrados; os apps Flutter não usam esta API; não houve transferência de dados/Drive nem homologação geral. A implantação no domínio final exigirá backup testado, auditoria de permissões, restauração, rate limiting avançado, monitoramento, tratamento de senhas, carga e aprovação expressa da Auditar.
