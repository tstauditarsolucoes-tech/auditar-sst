# Auditar SST — versão atual

## Linha vigente

| Plataforma | Versão |
|---|---|
| Android | **v3.29.149+291** |
| Windows | **v3.30.68+255** |

**Branch de trabalho:** `feature/client-panel-permissions-v329106`  
**Pull Request:** `#15`  
**Estado:** CI final em validação em 01/10/2026.

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
