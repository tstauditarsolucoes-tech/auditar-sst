# Entrega técnica para Júlio César Angelim — Auditar SST

**Preparado em 27/10/2026.** Branch `migration/preparacao-web-20261027`, PR #23 **DRAFT**.  
**Status:** React, Node, PostgreSQL e autenticação NOVA habilitáveis em ambiente **privado e isolado, somente dados fictícios**, com configuração opt-in. NÃO é produto final, não afeta app instalado ou domínio atual. **Não é o Auditar SST completo pronto para publicar no domínio principal.**

## 1. O produto que a Auditar quer receber

**Armazenamento principal definido:** PostgreSQL e mídia privada (fotos, assinaturas, PDFs) integralmente no servidor próprio; **não usar Google Drive na arquitetura final**. O Drive atual permanece intocado para migração auditada. Júlio deve dimensionar espaço e backups independentes conforme [../ARMAZENAMENTO_PROPRIO_SEM_DRIVE.md](../ARMAZENAMENTO_PROPRIO_SEM_DRIVE.md).

**Um Auditar SST com três clientes**: Android APK Flutter atual, Windows instalador EXE Flutter atual e nova Web React responsiva, conectados futuramente à MESMA API Node/PostgreSQL. A arquitetura oficial está em [../DECISAO_3_VERSOES_SERVIDOR_PROPRIO.md](../DECISAO_3_VERSOES_SERVIDOR_PROPRIO.md). Manter fluxo visual e offline das versões instaladas; migrar a comunicação com a Central Online/Apps Script progressivamente e com testes. Nenhuma funcionalidade das versões originais deve desaparecer por causa do servidor novo.

## 2. O que esta branch contém hoje

| Componente | Entregue agora | Limitação |
| --- | --- | --- |
| Web | React/TypeScript/Vite, layout celular/PC, matriz/Assistente Offline e guia opcional de login/NCs conectadas para homologação | Telas principais continuam demonstrativas; painel de acesso funciona só após ativar explicitamente auth/DB no backend isolado |
| API | Node.js 24, NCs, login web e sessões/CSRF; bootstrap privado opt-in com duas contas limitadas e limite inicial de tentativas; testado em CI | Por padrão continua bloqueada (401); só o overlay de homologação privada com TLS e controle de acesso ativa o login |
| Banco | PostgreSQL 17, migrações 001–003: domínio SST/RLS, login/sessões e limitação de tentativas | Ainda sem usuários reais, backup real ou armazenamento privado de mídia |
| Proxy | Nginx serve React e repassa /api/ internamente | Sem acesso público ou certificado neste pacote |
| Docker | Compose isolado, nenhum host port, segredo via arquivo externo | Não conectado à VPS nem ao NPM |
| Testes | TypeScript, NCs×PostgreSQL e NOVO login×PostgreSQL de CI efêmera, troca de empresa, cookie e proteção CSRF, React e smoke Docker | Não valida contas reais, mídia, autenticação Flutter nem integrações legadas |

A pasta `web/static` contém a sonda antiga, não é usada no build React. **Nenhum segredo, foto, assinatura ou dado de cliente foi enviado ao repositório público.**

## 3. Comandos seguros na VPS — apenas homologação

Julio deverá usar **somente diretório separado de teste**, sem alterar os sistemas que já rodam. Recomendado acesso SSH e Docker com permissão adequada, quota de memória/disco conferida e ciência do administrador da VPS.

```bash
git clone https://github.com/tstauditarsolucoes-tech/auditar-sst.git
cd auditar-sst
git switch migration/preparacao-web-20261027
cd Auditar-SST/web-migration/infra

# Preparar credencial só da base de HOMOLOGAÇÃO (não versionar):
install -d -m 0700 secrets
umask 077
openssl rand -base64 48 > secrets/postgres_password

# Pré-validação sem iniciar recursos:
bash scripts/preflight.sh
```

**Atenção:** se já existir clone, pasta, branch ou serviço local, não sobrescrever. No Git público há código do app e histórico; revisar antes de copiar arquivos para a VPS. Os comandos de clonagem acima não são migração de dados.

Após preflight, **somente com autorização do administrador para iniciar contêineres de homologação**, executar:

```bash
docker compose -p auditar-sst-web-hml -f compose.staging.yml up --build -d --wait
bash scripts/smoke-staging.sh
docker compose -p auditar-sst-web-hml -f compose.staging.yml ps
```

Isso apenas confirma frontend React, endpoint de saúde e imagem da API cuja lógica de NC permanece bloqueada sem autenticação; o banco inicia vazio e precisa da migração de homologação seguindo `db/README.md`. **Não oferece URL externa nem converte aplicativos.**

### Se quiser visualizar no navegador sem trocar o domínio atual

- Júlio pode criar um hostname de HOMOLOGAÇÃO restrito a equipe, diferente de `tst.auditarsolucoes.com.br` (não presumir que já exista).
- Descobrir o nome da rede Docker do Nginx Proxy Manager e, somente se autorizado, defini-lo localmente em `AUDITAR_NPM_NETWORK`. Não colocar a variável/segredo no Git.
- Revisar [GUIA_NGINX_PROXY_MANAGER_TST.md](GUIA_NGINX_PROXY_MANAGER_TST.md) antes de conectar apenas o serviço `web` à rede externa.
- O NPM deverá apontar para `auditar-sst-web-hml:8080` no **hostname de teste**, com SSL válido e lista de acesso restrita. Nunca expor API/DB diretamente.

Para a configuração candidata com NPM:

```bash
export AUDITAR_NPM_NETWORK=SUBSTITUIR_PELO_NOME_VERIFICADO_DA_REDE
bash scripts/preflight.sh --npm
# O comando abaixo SOMENTE após autorização e criação/revisão do staging:
docker compose -p auditar-sst-web-hml -f compose.staging.yml -f compose.npm.example.yml up --build -d --wait
bash scripts/smoke-staging.sh --npm
```

**Não executar simultaneamente as duas variantes do comando `up` no mesmo projeto sem conferir a rede e o estado dos contêineres.**

## 4. O que NÃO pode ser feito ainda

- Não usar o domínio definitivo como se o sistema estivesse pronto; o endereço já serve outro sistema instalado por engano.
- Não alterar o Proxy Host atual, desligar contêineres antigos, apagar volumes ou modificar o DNS.
- Não cadastrar usuários reais, abrir banco/porta 5432, colocar foto de cliente, chaves, senhas ou backups no GitHub.
- Não migrar dados do Apps Script, Drive, autenticação, IA, fotos/assinaturas ou filas offline sem aprovar um plano com contagens, hashes e rollback.
- Não publicar APK/EXE nem disponibilizar download público. As versões instaladas continuam operando separadamente.

## 5. Critérios para a hospedagem REAL do Auditar SST

**Ainda não atendidos:**
1. Ativar com segurança a autenticação nova já prototipada em CI: contas de banco separadas, provisionamento/recuperação, rate limit, proxy HTTPS, testes reais com sessões e desenvolver API SST completa.
2. Expandir esquema inicial e migrações versionadas, backup automático fora da VPS, ensaio de recuperação, armazenamento privado de mídia dentro do servidor e integridade de anexos.
3. Migração funcional Web: vistorias, NCs/tratativas, agenda, relatórios, fotos, assinaturas, painel Cliente, ADM, CIPA e módulos em uso.
4. Adaptar Android e Windows à nova API mantendo offline, testar uploads/filas/conflitos e instalar versões de homologação em aparelhos reais.
5. Ensaiar migração legada sem perdas e compatibilidade entre os três clientes.
6. Plano de virada do Nginx Proxy Manager com backup do sistema antigo, aprovação da Auditar e reversão praticada.

**Regra de aceite:** somente após estes itens, Julio poderá recomendar apontar `tst.auditarsolucoes.com.br` para o novo backend/web. A retirada do sistema errado exige identificação exata e preservação de eventuais dados/volumes compartilhados.

## 6. Contato técnico de entrega

- Código/branch: https://github.com/tstauditarsolucoes-tech/auditar-sst/tree/migration/preparacao-web-20261027
- PR de revisão: https://github.com/tstauditarsolucoes-tech/auditar-sst/pull/23
- Arquitetura: `../DECISAO_3_VERSOES_SERVIDOR_PROPRIO.md`
- Plano de transição: `../PLANO_DE_MIGRACAO.md`
- Plano de virada: `PLANO_DE_VIRADA_DO_DOMINIO_TST.md`

**Responsabilidades:** o desenvolvimento pode preparar o projeto; Julio administra VPS, redes/NPM, acesso, SSL, backups e deploy após autorização. A Auditar realiza homologação funcional e autoriza a virada.


## 7. Tela nova de acesso (somente teste de homologação)

Há uma aba **Acesso de homologação** no React (`web/src/WebAuthPilot.tsx`) com formulário de login novo, seleção de empresa vinculada, lista/criação de NC, relato/validação de correção, linha do tempo e logout. As demais telas continuam com exemplos fictícios e não foram substituídas. **A aba de acesso não funciona no Docker padrão:** a API permanece com autenticação desabilitada e retorna 401. Só habilitar com contas novas autorizadas, URL HTTPS de teste, revisão de CSRF, rate limiting e conexão a banco segregado; não usar senhas da Central Online atual nem dados reais antes da homologação aprovada.


## Preparação para primeiro acesso PRIVADO do Júlio

O pacote adicional está explicado em **[GUIA_PRIVADO_JULIO.md](GUIA_PRIVADO_JULIO.md)**: preflight sem deploy, segredos Docker locais, migrações 001–003, roles distintos, bootstrap opt-in, conta fictícia inicial, NPM em hostname novo com SSL/Access List, testes e parada sem remover volumes. O domínio principal permanece bloqueado pelo bootstrap para impedir substituição prematura.
