# Auditar SST — pasta organizada (candidata)

Esta pasta reúne **somente o aplicativo Auditar SST** (Android e Windows), com suas fontes, bases, scripts de montagem, testes, documentos, módulos administrativos e cópias dos dois workflows principais.

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

Este é um **espelho organizado para revisão**, sem excluir nem mudar os caminhos dos arquivos originais. Assim os builds e a PR #15 permanecem preservados. Antes de remover os diretórios SST antigos, é obrigatório migrar os workflows para trabalhar dentro de `Auditar-SST/`, validar CI, dados, fotos, histórico, assinaturas, login offline, PDFs e atualização em aparelho real.

Nenhum APK foi publicado, nenhum Apps Script foi implantado e nenhum banco de dados do usuário foi modificado nesta organização. **Não usar esta pasta, sozinha, como comprovação de release homologada.**
