# Auditar SST — código consolidado em pasta única (candidato de migração)

Esta pasta passou a reunir **todo o código-fonte do aplicativo Auditar SST** (Android e Windows), com suas fontes, bases, scripts de montagem, testes, documentos, módulos administrativos e cópias dos dois workflows principais.

- Origem: `tstauditarsolucoes-tech/auditar-sst`, branch `feature/client-panel-permissions-v329106`.
- Snapshot de origem: `2002fd8d9228eb210aa0bf778dfd8b994d1396ad` (26/10/2026).
- Preparação em 27/10/2026; Android v3.29.198 e Windows v3.30.126 são as compilações mais recentes identificadas.
- **Não foram incluídos** `auditar-epi*`, `gestao-epi*` nem `COMERCIALIZACAO_GESTAO_EPI.md`.

## Onde está cada parte

- `source_overrides/`, `source_v3290_final/`, `Auditar_SST_v1.5_dashboard_completo*.zip`: bases Flutter legadas do aplicativo.
- `feature_sources/`: módulos Android/Windows, agenda, painel do cliente, ADM e biblioteca SST.
- `tools/`, `build_sources/`: montagem, melhorias e testes incrementais.
- `auditar-sst-master/`, `auditar-sst-master-windows/`: componentes administrativos.
- `hostinger-media-api/`, `entrega_gs_2026-10-14/`: fontes de integração existentes; **não implantar automaticamente**.
- `docs/`: documentação e homologação.
- `ci/workflows/`: **cópias de referência** dos workflows atuais. O GitHub Actions continua lendo os arquivos originais em `/.github/workflows/`.

## Segurança e etapa seguinte

Na branch de organização, os antigos diretórios SST foram **retirados da raiz** e preservados aqui, com os mesmos objetos Git, sem excluir histórico. Os workflows ativos, que precisam permanecer em `/.github/workflows/`, copiam temporariamente esta pasta para a raiz **apenas no runner de CI**, preservando os scripts existentes. O Gestão EPI permanece na raiz, independente.

**Preparação da migração de tecnologia para web:** consulte [web-migration/README.md](web-migration/README.md) para auditoria do código, arquitetura, fases e contrato inicial de API (proposta, sem implementação de produção).

**Para o programador web:** consulte [`docs/GUIA_PROGRAMADOR_WEB_SERVIDOR_PROPRIO_20261027.md`](docs/GUIA_PROGRAMADOR_WEB_SERVIDOR_PROPRIO_20261027.md). A interface atual Android/Windows e o Painel Apps Script exigem adaptação e homologação antes de rodar em servidor próprio.

Nenhum APK foi publicado, nenhum Apps Script foi implantado e nenhum banco de dados do usuário foi modificado nesta organização. O CI completo da nova estrutura e a operação web ainda precisam ser homologados. **Não usar esta pasta, sozinha, como comprovação de release homologada.**
