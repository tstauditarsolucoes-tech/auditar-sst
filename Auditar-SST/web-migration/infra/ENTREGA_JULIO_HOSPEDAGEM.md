# Entrega técnica para Júlio César Angelim — Auditar SST

**Preparado em 27/10/2026.** Branch `migration/preparacao-web-20261027`, PR #23 **DRAFT**.  
**Status:** infraestrutura Docker, primeira interface React, esquema PostgreSQL multiempresa e protótipo protegido de regras HTTP de NCs, próprios para **homologação isolada com dados fictícios**. **Não é o Auditar SST completo pronto para publicar no domínio principal.**

## 1. O produto que a Auditar quer receber

**Armazenamento principal definido:** PostgreSQL e mídia privada (fotos, assinaturas, PDFs) integralmente no servidor próprio; **não usar Google Drive na arquitetura final**. O Drive atual permanece intocado para migração auditada. Júlio deve dimensionar espaço e backups independentes conforme [../ARMAZENAMENTO_PROPRIO_SEM_DRIVE.md](../ARMAZENAMENTO_PROPRIO_SEM_DRIVE.md).

**Um Auditar SST com três clientes**: Android APK Flutter atual, Windows instalador EXE Flutter atual e nova Web React responsiva, conectados futuramente à MESMA API Node/PostgreSQL. A arquitetura oficial está em [../DECISAO_3_VERSOES_SERVIDOR_PROPRIO.md](../DECISAO_3_VERSOES_SERVIDOR_PROPRIO.md). Manter fluxo visual e offline das versões instaladas; migrar a comunicação com a Central Online/Apps Script progressivamente e com testes. Nenhuma funcionalidade das versões originais deve desaparecer por causa do servidor novo.

## 2. O que esta branch contém hoje

| Componente | Entregue agora | Limitação |
| --- | --- | --- |
| Web | React/TypeScript/Vite, layout celular/PC, matriz de risco e título amigável de NC migrados de Dart | NCs demonstrativas em memória, não existe CRUD real |
| API | Node.js 24, health e lógica/rotas de NCs: criar, listar, histórico, informar/validar/rejeitar correções; testes com pool simulado | Sem autenticação real ou conexão de banco configurada: rotas de NC retornam 401 por segurança |
| Banco | PostgreSQL 17, migração 001: empresas, vínculos, vistorias, NCs, histórico, evidências (metadados), tarefas, auditoria e RLS multiempresa | Ainda sem credenciais, dados reais, backup operacional ou upload privado |
| Proxy | Nginx serve React e repassa /api/ internamente | Sem acesso público ou certificado neste pacote |
| Docker | Compose isolado, nenhum host port, segredo via arquivo externo | Não conectado à VPS nem ao NPM |
| Testes | Regras TypeScript, Node NCs com pool simulado, esquema SQL e RLS multiempresa com dados fictícios/ROLLBACK, build React e smoke Docker | Não valida API contra Postgres real, sessões reais nem integrações legadas |

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
1. Integrar backend Node a credenciais PostgreSQL de mínimo privilégio e autenticador de sessão verificado, testar rotas reais NC×PostgreSQL e desenvolver toda API SST com autorização/monitoramento.
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
