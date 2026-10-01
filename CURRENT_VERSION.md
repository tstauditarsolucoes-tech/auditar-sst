# Auditar SST — versão atual

## Linha vigente

| Plataforma | Versão |
|---|---|
| Android | **v3.29.150+292** |
| Windows | **v3.30.69+256** |

**Branch de trabalho:** `feature/client-panel-permissions-v329106`  
**Pull Request:** `#15`  
**Estado:** ✅ CI final validada em 01/10/2026.

## Validação final

- Android: workflow run `36928782210` — **success**.
- Windows: workflow run `36928782260` — **success**.
- APK: `Auditar-SST-v3.29.150-Android.apk` — SHA-256 `36e06d78d748d4edc233cbeee0afb28c47bf4607660a222658995cff59fc91e8`.
- Windows instalador: `Auditar-SST-Setup-v3.30.69.exe` — SHA-256 `758b81fe315494d9553be7ec3dade4b48938b727331daf7eb059ccf5bc03d0c5`.
- Windows portátil: `Auditar-SST-Windows-v3.30.69-PORTATIL.zip` — SHA-256 `047d412551a60b76e6484aed4dfa4bf49fdc3955d9c0f8c7fa90886b520eb7dd`.
- Revisão visual: Central de documentos sem corte do título/Histórico de envios e abas Hoje/Busca/Evidências com contraste corrigido.
- Núcleo protegido preservado pelas regressões do pipeline.
- A validação de CI não substitui o teste físico do APK e do executável em aparelho/PC real.

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

- Android: workflow run `36928782210` — **success**
- Artefato: `Auditar-SST-v3.29.150-Android-Pacote-Operacional`
- Windows: workflow run `36928782260` — **success**
- Artefato: `Auditar-SST-v3.30.69-Windows-Ajuste-Visual`
- Commit do app validado: `513ef6dcebebd0597c01d3b2fdcc79f19487a15c`
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
