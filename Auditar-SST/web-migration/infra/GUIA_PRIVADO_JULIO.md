> **Escopo atualizado:** a Auditar decidiu **não migrar dados antigos**. A Web nova será iniciada vazia quando homologada; o sistema antigo permanece preservado e não deverá ser apagado. Consulte [INICIO_LIMPO_SEM_MIGRACAO_20261027.md](../INICIO_LIMPO_SEM_MIGRACAO_20261027.md). Isso não autoriza implantação no domínio atual.

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

Só num banco **novo e vazio**, aplicar migrações 001, 002, 003, 004, 005, 006, 007, 008, 009, 010, 011, 012 e 013 nessa ordem, uma única vez:

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

docker compose -p auditar-sst-web-hml -f compose.staging.yml exec -T db \
  psql -U auditar_web_hml -d auditar_web_hml -v ON_ERROR_STOP=1 -f /db-init/migrations/007_private_media_pilot.sql

docker compose -p auditar-sst-web-hml -f compose.staging.yml exec -T db \
  psql -U auditar_web_hml -d auditar_web_hml -v ON_ERROR_STOP=1 -f /db-init/migrations/008_action_plan_pilot.sql

docker compose -p auditar-sst-web-hml -f compose.staging.yml exec -T db \
  psql -U auditar_web_hml -d auditar_web_hml -v ON_ERROR_STOP=1 -f /db-init/migrations/009_training_sessions_pilot.sql

docker compose -p auditar-sst-web-hml -f compose.staging.yml exec -T db \
  psql -U auditar_web_hml -d auditar_web_hml -v ON_ERROR_STOP=1 -f /db-init/migrations/010_cipa_pilot.sql

docker compose -p auditar-sst-web-hml -f compose.staging.yml exec -T db \
  psql -U auditar_web_hml -d auditar_web_hml -v ON_ERROR_STOP=1 -f /db-init/migrations/011_nc_recommendation_pdf.sql

docker compose -p auditar-sst-web-hml -f compose.staging.yml exec -T db \
  psql -U auditar_web_hml -d auditar_web_hml -v ON_ERROR_STOP=1 -f /db-init/migrations/012_training_attendance_draft.sql

docker compose -p auditar-sst-web-hml -f compose.staging.yml exec -T db \
  psql -U auditar_web_hml -d auditar_web_hml -v ON_ERROR_STOP=1 -f /db-init/migrations/013_native_auth_pilot.sql
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
- `evidence_data_hml`: volume Docker NOVO com fotos de homologação, separado de outros volumes, montado apenas na API privada e nunca publicado no NPM. Backup de **banco + volume** deve ser coordenado.

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
- Anexar foto **fictícia** de até 2 MB a NC e vistoria, abrir no painel autenticado e validar que outra empresa não acessa nem o arquivo nem seus metadados. Não carregar fotografias reais.
- Concluir vistoria de teste com ao menos três achados e baixar PDF: capa seguida de páginas de até dois achados; conferir foto, tamanho, quebras, acentos e leitura em Android/Windows. PDF piloto não inclui assinatura e não substitui o Padrão Auditar 3.
- Repetir o envio da vistoria com a mesma chave e confirmar que não gera duplicatas; testar rascunho em duas abas.
- Conferir histórico e verificar que outra empresa não vê os dados anteriores.
- Sair/entrar e conferir expiração/negação de sessões revogadas.
- Conferir consumo de memória, backups, logs e limites de tentativas de login.
- Registrar estratégia de cópia criptografada e teste de restauração do PostgreSQL **junto do volume** `evidence_data_hml`; não reutilizar o backup do Drive como substituto.
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

Vistorias/agenda/painel do cliente/ADM/fotos de teste são pilotos isolados, não integram sistemas legados; PDF definitivo Padrão Auditar 3, assinaturas e fotografias reais ainda não foram migrados; os apps Flutter não usam esta API; não houve transferência de dados/Drive nem homologação geral. A implantação no domínio final exigirá backup testado, auditoria de permissões, restauração, rate limiting avançado, monitoramento, tratamento de senhas, carga e aprovação expressa da Auditar.


## Armazenamento próprio: primeira entrega de homologação (007)

Fotos **fictícias** JPEG/PNG/WebP (até 2 MB) são enviadas em sessão HTTPS da web nova, armazenadas no volume nomeado `evidence_data_hml` em caminho não exposto ao NPM, e registradas no PostgreSQL com hash SHA-256, tamanho, perfil/empresa e identificador estável. Leitura exige login e escopo de empresa; não há URL pública nem cópia para Google Drive. A implementação confirma cabeçalho básico do arquivo, mas ainda exige validação mais profunda, antivírus, cotas por empresa, retenção, integridade/restauração em caso de falha entre disco e banco e estratégia de backup antes de uso real. Não colocar assinatura biométrica nem dado sensível neste piloto.

**Atenção:** um backup de banco sozinho não recupera fotos; um backup de volume sozinho não recupera vínculos. Planejar cópia consistente dos dois recursos com teste de restauração. O entrypoint padrão não monta o volume de mídia e permanece fechado.


## PDF de vistoria — piloto 008 lógico (sem nova migração SQL)

O endpoint autenticado GET /api/v1/reports/inspections/:id/pdf gera PDF de vistoria **concluída** inteiramente em memória (sem arquivo persistente), com capa, nome da empresa da sessão, risco e até dois achados por página, incorporando a primeira foto JPEG/PNG de teste de cada NC, quando houver. PDFs ainda não representam o relatório profissional final, não incluem assinatura nem todas as informações do Flutter/Apps Script; fotos WebP continuam visíveis apenas no painel. Não enviar esse material de homologação a clientes nem considerar como relatório oficial. Testar visualmente e aprovar modelo antes de produção.


## Inventário pré-migração do legado: SOMENTE leitura de cópia

Antes de importar registros reais, o responsável deve fazer um backup completo **fora do repositório público**, seguindo as regras de acesso dos dados de clientes. Em um equipamento controlado, manter uma CÓPIA numa pasta exclusiva com nome iniciando por `auditar-sst-backup-`, por exemplo `/dados/privados/auditar-sst-backup-20261027`. Após verificar permissões locais, executar `node tools/inventory-legacy-backup.mjs /dados/privados/auditar-sst-backup-20261027`. O script só lê arquivos, calcula hashes internamente e devolve totais por extensão, tamanho e quantidade de possíveis duplicatas; não publica nomes, conteúdo, fotos, hashes individuais, IDs ou credenciais. Ele **não transfere nada** ao PostgreSQL. Não apontar para pastas de produção, Google Drive montado ou diretórios amplos. Antes da migração real, comparar inventários antes/depois e validar integridade dos documentos, permissões, autorização e plano de retorno.


## Auditoria de compatibilidade antes de pensar em migrar os aparelhos

O Node da homologacao disponibiliza `GET /api/v1/migration/compatibility` e `POST /api/v1/migration/compatibility/check` para uma **sessao ADM da nova base**, exigindo origem e CSRF em POST. Esses endpoints aceitam somente contagens (sem linhas, anexos ou credenciais) e devolvem **bloqueio expresso de sincronizacao real**; nao sao `device_sync_push/pull`. Consulte [MATRIZ_COMPATIBILIDADE_LEGADA_20261027.md](../MATRIZ_COMPATIBILIDADE_LEGADA_20261027.md).

Nao alterar URL, token, fila, cursor nem banco SQLite nos aplicativos Flutter existentes com base nesse resultado. O teste de compatibilidade e apenas a primeira camada de seguranca.


## Plano de Ação — piloto Web (migração 008)

Depois das migrações 001–008, o piloto de homologação inclui uma área de **Plano de Ação SST** com NC vinculada, responsável ativo da empresa, prazo opcional, revisão contra sobrescrita e histórico de criação/edição/andamento/conclusão/cancelamento. Os endpoints privados autenticados são `GET/POST /api/v1/action-plans`, `GET/PATCH /api/v1/action-plans/:id` e `POST /api/v1/action-plans/:id/status`. Nenhum plano do legado foi importado. Testes de isolamento e idempotência executam apenas sobre dados artificiais na GitHub Actions. **Não testar com cliente real.**

## Treinamentos/DDS/Integração Web — piloto 009

Apenas contas da EQUIPE em homologação privada podem abrir registros de Treinamentos e DDS após login. A nova área cadastra tipo, tema, setor, referência à NR, instrutor, data, duração e contagem declarada de participantes. Histórico append-only, alteração com revisão, criação e conclusão com idempotência, e isolamento por empresa no PostgreSQL. Cliente não acessa esses registros. Para marcar como realizado é necessário informar duração e contagem de participantes; **isso não representa lista de presença assinada, certificado, qualificação profissional nem comprovação de cumprimento de NR.**

Teste uma atividade fictícia planejada, edite duração e participantes, marque realizada, valide histórico, outro perfil e outra empresa. Não utilize dados pessoais, certificados, listas ou fotografias reais nesta homologação. O aplicativo Flutter e suas informações históricas continuam inalterados.


## CIPA Web — piloto 010 (apenas cadastros sintéticos)

A nova aba CIPA da homologação privada tem mandato (início/fim, data de eleição declarada), representantes com tipo e condição, agenda de reunião, resumo de reunião informada, andamento administrativo e linha do tempo somente para inclusão. A API exige login novo, empresa ativa e CSRF em todas as mutações. Contas do cliente NÃO acessam este módulo; somente gestor/ADM pode marcar mandato como ativo ou encerrado.

Este cadastro **não valida dimensionamento, eleição, votação, listas de presença, atas assinadas, designação formal, carga horária, atas eleitorais nem conformidade com a NR-5**. Não cadastrar nomes verdadeiros, não enviar fotografias ou documentos reais e não considerar a área como entrega legal. Testar mandatário fictício, representante fictício, reunião, conclusão, mudança de empresa e a vedação para cliente. O sistema Flutter e o Apps Script atual não são modificados.


## Revisão do PDF de vistoria e recomendações (migração 011, somente homologação)

Uma NC registrada dentro da vistoria pode armazenar uma **recomendação técnica** separada da descrição, com limite de 1.600 caracteres. O PDF piloto apresenta até 2 achados por página e cria páginas adicionais com fotos maiores (até duas evidências por página). O PDF consulta **apenas a primeira foto JPEG/PNG de cada NC** na base NOVA de teste, não faz cópia das mídias nem migra o Google Drive.

O modelo ainda NÃO está homologado como **Padrão Auditar 3**: falta assinatura, conferência tipográfica/visual em celular e PC, aprovar logo/marca oficial, texto integral dos campos que excedem o espaço do cartão e referências legais completas. Textos longos nos cartões podem ser reduzidos visualmente; o registro original permanece íntegro no PostgreSQL. Não enviar a clientes nem substituir o relatório oficial. Antes de aprovar, gerar PDF com 0, 1, 2, 3 e 30 NCs fictícias e fotos horizontais/verticais; conferir renderização e anexos, sem usar dados pessoais.


## Participantes de treinamento — minuta PDF, piloto 012

A nova área Treinamentos/DDS aceita SOMENTE **nomes FICTÍCIOS** para simular uma relação de participantes informados, com estado `nao_confirmada` ou `declarada`. A inclusão é somente append-only, limitada a 100 registros por atividade, vinculada à empresa da sessão e com chave de envio contra duplicidade. Somente criador/gestor/ADM podem registrar; cliente não lê. A rota `GET /api/v1/reports/trainings/:id/attendance.pdf` gera uma **minuta** PDF privada sem assinaturas e sem certificados. O documento é marcado em todas as páginas como **MINUTA - NÃO COMPROVA PRESENÇA**. Ele NÃO pode ser enviado ao cliente como prova de treinamento, nem usado para comprovar requisitos da NR.

Na VPS, executar migração 012 **apenas sobre banco NOVO de homologação** após 001–011. Não cadastrar trabalhadores reais, CPFs, assinaturas ou documentos. Verificar no teste do Júlio com 0, 1 e 16 participantes fictícios, exportação do PDF, separação por empresa e permissão de cliente. Não haverá migração do Drive/Sheets: os dados legados continuam preservados fora da nova plataforma. Para uso real serão necessários consentimento/política LGPD, coleta autenticada de presença/assinatura, validação profissional do conteúdo e layout de certificado, retenção, backups e auditoria.


## Relatório de vistoria Web: continuação automática e fotos maiores (candidato)

O PDF do ambiente novo mantém **até 2 achados por página**. Se descrição, título ou recomendação não couberem na área de resumo, todo o restante vai para **páginas de continuação**, evitando omissão de texto cadastrado. Fotos JPEG/PNG vinculadas a cada NC são verificadas pelo serviço privado e apresentadas **até 2 por NC, uma por página ampliada**; o original não é regravado nem extraído do Drive.

O piloto continua identificado como HOMOLOGAÇÃO, **não é o Padrão Auditar 3 aprovado**, não tem assinaturas oficiais e não está pronto para clientes. A CI utiliza dados fictícios e testa textos extensos, fotos múltiplas, permissões e geração; a **conferência visual em PC/Android** e validação do layout/marca Auditar continuam obrigatórias antes de publicação. Não migrar dados antigos. Não alterar o domínio atual.


## Diagnóstico Dart nativo, opcional e sem escrita

O novo endpoint `GET /api/v1/native/handshake` não exige login, não revela dados de empresas nem permite escrita. É apenas um handshake para futuras versões de testes, com `native.syncEnabled=false`, `native.writesEnabled=false`, `native.authentication=not-implemented` e `productionDataConnected=false`. O código Dart em `../native/flutter_probe` NÃO está conectado ao Android/Windows instalado e está desativado por padrão. Não mexer na configuração do Apps Script, não usar o domínio atual, não provisionar contas reais. Para consultar a sonda de modo privado, o Júlio pode abrir o endpoint HTTPS na homologação sem dados e verificar os campos, sem habilitar mudanças de servidor no aplicativo.


## Autenticação Nativa (piloto 013) — SOMENTE login/consulta/logout

A nova tabela `sst.native_session` armazena somente SHA-256 de tokens aleatórios, empresa e usuário NOVOS, expiração de **30 minutos**, revogação e vínculo ativo com conta. Usa **conta auth restrita**, e reutiliza credenciais criadas no PostgreSQL de homologação (jamais contas/cookies Apps Script). Endpoints `POST /api/v1/native/auth/login`, `GET /api/v1/native/auth/session` e `POST /api/v1/native/auth/logout` aceitam `Authorization: Bearer ...` (exceto login) e NÃO dão acesso às rotas Web de dados. Origin/cookie Web são recusados no subsistema nativo. Contador de tentativas por identidade é compartilhado com o login Web.

**OFF POR PADRÃO:** mesmo com o Docker privado e Web funcionando, essas rotas respondem 404 sem a variável `AUDITAR_ENABLE_NATIVE_AUTH=PRIVATE_STAGING_NATIVE_ONLY` passada somente ao serviço privado de teste. **Não habilite isso na VPS sem revisar HTTPS, política de uso de credenciais nativas, conta/segredos e plano de testes.** A sonda Dart permanece independente/desligada, APK e EXE antigos não foram recompilados. Tokens nativos ainda **não autorizam** escrever/ler NCs, vistorias, fotos, arquivos, ou emitir relatórios. Falta implementar esses recursos com controles específicos antes de compilar. O projeto não importa dados antigos.
