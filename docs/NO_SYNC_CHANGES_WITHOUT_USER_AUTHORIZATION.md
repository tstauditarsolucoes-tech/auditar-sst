# Auditar SST — Regra de proteção da sincronização

Diretriz expressa do proprietário (26/09/2026): **não alterar a sincronização sem solicitação e autorização explícitas dele**.

## Arquivos protegidos
- `lib/services/device_sync_service.dart`
- `lib/services/sync_coordinator.dart`
- `lib/services/media_sync_service.dart`
- `lib/services/drive_service.dart`
- `lib/services/apps_script_http.dart`
- `lib/services/auth_service.dart`
- `lib/database.dart`
- `painel_web_google_apps_script/Code.gs`
- `painel_web_google_apps_script/MultiUser.gs`
- `painel_web_google_apps_script/ClientPortal.gs`

Esta proteção também vale para as filas de mídia, payloads, tabelas, endpoints, regras de restauração e os arquivos de integração associados.

**Não modificar, refatorar, substituir, otimizar, limpar ou corrigir** os itens protegidos por iniciativa própria. Não aproveitar alterações de outro módulo para mexer neles. Se uma melhoria depender disso, parar essa parte e obter autorização específica previamente.

Para cada melhoria em relatório, DDS, treinamento, CIPA ou painel: aplicar patch isolado à interface/renderer, comparar SHA-256 dos arquivos protegidos antes e depois e bloquear a compilação se qualquer hash mudar. Não incluir alterações de sincronização em commits destinados a outros módulos.

A base Android funcional validada pelo usuário com chave permanente é **v3.29.123**. O pacote v3.29.124 acrescenta apenas pré-visualização, aviso de evidências e progresso de emissão no relatório, com guarda de arquivos protegidos. A assinatura permanente deve ser preservada nas atualizações.

Toda mudança deve ser testada antes da entrega. Uma compilação bem-sucedida não equivale à validação funcional em dispositivo.
