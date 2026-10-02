# Auditar SST — versão atual

## Linha vigente

| Plataforma | Versão |
|---|---|
| Android | **v3.29.152+294** |
| Windows | **v3.30.71+258** |

**Branch de trabalho:** `feature/client-panel-permissions-v329106`  
**Pull Request:** `#15`  
**Estado:** ✅ CI final validada em 01/10/2026.

## Validação final

- Android: workflow run `37049955381` — **success**.
- Windows: workflow run `37049963066` — **success**.
- APK: `Auditar-SST-v3.29.151-Android.apk` — SHA-256 `36e06d78d748d4edc233cbeee0afb28c47bf4607660a222658995cff59fc91e8`.
- Windows instalador: `Auditar-SST-Setup-v3.30.70.exe` — SHA-256 `758b81fe315494d9553be7ec3dade4b48938b727331daf7eb059ccf5bc03d0c5`.
- Windows portátil: `Auditar-SST-Windows-v3.30.70-PORTATIL.zip` — SHA-256 `047d412551a60b76e6484aed4dfa4bf49fdc3955d9c0f8c7fa90886b520eb7dd`.
- Revisão visual: Central de documentos sem corte do título/Histórico de envios e abas Hoje/Busca/Evidências com contraste corrigido.
- IA por foto da Ronda: em falha de comunicação com o Google, repete a mesma rota `checklist_photo` já usada pela IA da vistoria, com janela maior; a IA normal da vistoria foi preservada.
- Núcleo protegido preservado pelas regressões do pipeline.
- A validação de CI não substitui o teste físico do APK e do executável em aparelho/PC real.

## Padrão Auditar 3 — modelo principal

- Modelo principal dos relatórios de vistoria técnica.
- Layout fiel ao PDF aprovado: logo Auditar à esquerda, empresa/título ao centro e somente a logo cadastrada do cliente à direita.
- Se a empresa não tiver logo cadastrada, o lado direito permanece vazio; não há repetição da logo Auditar nem logo fixa de cliente.
- Identificação com razão social, CNPJ, localidade, data e endereço completo.
- Achados em duas colunas: evidência fotográfica à esquerda; Local, Situação, Risco, Correção e Prioridade à direita.
- Fechamento com conclusão, referências gerais e Técnico em Segurança do Trabalho.
- `Padrão Auditar` e `Padrão Auditar 2` permanecem disponíveis como alternativas.

## Escopo acumulado da linha atual

- Central Inteligente de Campo e busca global.
- Evidências Antes × Depois e alerta conservador de recorrências.
- Relatórios com progresso de geração e modelos gerenciais.
- Ronda com IA, rascunhos, fotos e recuperação.
- Treinamentos com fotos, fichas físicas, assinaturas sequenciais, pesquisa e filtros.
- Visão unificada de DDS, treinamentos e integrações.
- CIPA com mandato, membros, reuniões, atas, ações, eleição, treinamentos, documentos, histórico e atalhos de pendências.
- Central Administrativa Auditar para conta ADM.
- Painel do Cliente com múltiplos acessos individuais e permissões.
- Inspeção mensal de extintores.
- Android com chave permanente de assinatura.
- Windows com instalador e versão portátil.

## Builds validados

- Android: workflow run `37049955381` — **success**
- Artefato: `Auditar-SST-v3.29.151-Android-Pacote-Operacional`
- Windows: workflow run `37049963066` — **success**
- Artefato: `Auditar-SST-v3.30.70-Windows-IA-Ronda`
- Commits validados dos workflows: Android `3607275e78bc5d5c59f1c42e8ab7a820a0a82655`; Windows `ba7d49ceaa0047848cbe7ed62433104ff75d22f7`
- Alterações posteriores a esse commit neste arquivo/README são somente documentação.

## Núcleo protegido

Não alterar sem autorização expressa:

```text
lib/database.dart
lib/services/device_sync_service.dart
lib/services/apps_script_http.dart
lib/services/sync_coordinator.dart
lib/services/auth_service.dart
lib/services/drive_service.dart
lib/services/media_sync_service.dart
lib/services/ai_assistant_service.dart
painel_web_google_apps_script/Code.gs
painel_web_google_apps_script/MultiUser.gs
painel_web_google_apps_script/ClientPortal.gs
painel_web_google_apps_script/ClientPortal.html
painel_web_google_apps_script/ReportEmail.gs
```

As melhorias devem ser aditivas, isoladas e validadas por regressão antes do build.

## Workflows oficiais desta linha

- Android: `.github/workflows/build-v329106-client-portal.yml`
- Windows: `.github/workflows/build-v33030-client-portal.yml`

> Este arquivo deve ser atualizado sempre que a versão oficial da branch mudar.
