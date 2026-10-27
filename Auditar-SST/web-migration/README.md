# Auditar SST Web — preparação técnica (27/10/2026)

**Estado: preparação de migração; não é aplicação web funcional nem release.**

Esta pasta foi criada numa branch isolada para o programador avaliar a migração do Auditar SST Android/Windows + Central Online para um sistema acessível em navegador, em servidor próprio.

## Documentos para começar

1. [AUDITORIA_DO_CODIGO.md](AUDITORIA_DO_CODIGO.md) — diagnóstico do código real, onde cada função está e quais bloqueios existem.
2. [PLANO_DE_MIGRACAO.md](PLANO_DE_MIGRACAO.md) — arquitetura recomendada, etapas com entregas verificáveis, migração dos dados e homologação.
3. [API_WEB_PROPOSTA.yaml](API_WEB_PROPOSTA.yaml) — contrato OpenAPI inicial da **futura** API web, ainda não implementado.
4. [CHECKLIST_PARA_O_PROGRAMADOR.md](CHECKLIST_PARA_O_PROGRAMADOR.md) — decisões necessárias e critérios de aceite.

## Escopo

- Preservar Android e Windows atuais em paralelo.
- Preparar uma nova interface web responsiva para técnico, cliente e ADM.
- Transformar as funções de Central/Apps Script em contratos de backend **sem modificar a Central atual**.
- Isolar dados por empresa no servidor, manter eventos e histórico auditável.
- Tratar fotos, assinaturas e PDFs como dados privados.
- Planejar importação com backups e conferência de contagens/checksums.
- Não utilizar chaves embutidas em JavaScript entregue ao navegador.

## Infraestrutura informada pelo programador (27/10/2026)

A hospedagem será em VPS compartilhada com outros sistemas, com Docker, Node.js e banco em contêiner permitidos. Preparação isolada: [infra/README.md](infra/README.md) e [infra/compose.staging.yml](infra/compose.staging.yml). **Nenhum contêiner foi iniciado no servidor real.** Ainda faltam proxy reverso, domínio e política de backup.

## Escolha técnica proposta, a confirmar com o programador

- **Se houver VPS/servidor com Node:** frontend React + TypeScript + Vite; API Node.js + TypeScript (por exemplo Fastify); PostgreSQL; armazenamento privado de objetos; HTTPS/reverse proxy.
- **Se for apenas hospedagem PHP compartilhada:** frontend React + TypeScript + Vite; backend PHP com framework e autenticação/controle de acesso auditados; banco suportado pela hospedagem. A estrutura de frontend/contrato HTTP permanece semelhante.
- **Alternativa a analisar:** Flutter Web sem reescrever toda a UI. Flutter Web não exige instalação no dispositivo do cliente, porém os atuais usos de dart:io, SQLite/FFI, arquivos e plugins do Auditar SST impedem assumir compatibilidade direta.

Nenhuma das alternativas foi aprovada como definitiva. Não enviar nenhuma pasta de código ao public_html antes de decidir segurança, banco, domínio e migração.

## Referência congelada

- Repositório: tstauditarsolucoes-tech/auditar-sst (público).
- Origem da análise: branch organize/sst-em-pasta-20261027, SHA b331fb9a1fc88755cdc00652e110ed9d0a7185e4.
- Builds identificados: Android v3.29.198 e Windows v3.30.126 (candidatos; não equivalem a homologação web).
- Esta branch altera **somente** documentação/contrato de preparação; não modifica arquivos protegidos de sync/autenticação/banco, o painel GS, APK, EXE ou infraestrutura em produção.

## Resultado esperado da próxima etapa

Após confirmar a infraestrutura, criar no mesmo repositório uma aplicação web separada (front/backend) com dados de teste fictícios. Só integrar dados reais depois de aprovar os contratos, controle de acesso multiempresa, backups e testes de reversão.
