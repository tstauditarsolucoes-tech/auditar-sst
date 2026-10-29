# Auditoria inicial do código real — Auditar SST

Inspeção de fontes visíveis na branch organize/sst-em-pasta-20261027, SHA b331fb9a1fc88755cdc00652e110ed9d0a7185e4. Não é auditoria de segurança completa nem prova de execução do sistema web.

## 1. Como o projeto atual realmente é montado

- Base Flutter em source_overrides/Auditar_SST_v1_5_dashboard/ (pubspec.yaml, lib/main.dart, telas e serviços).
- Três ZIPs legados Auditar_SST_v1.5_dashboard_completo*.zip mais scripts sequenciais em tools/ e incrementos em feature_sources/ e build_sources/.
- O produto Android/Windows **não** é simplesmente uma pasta de frontend pronta: os workflows build-v329106-client-portal.yml e build-v33030-client-portal.yml compõem as versões finais executando scripts e patches.
- Antes de portar, o programador precisa gerar e auditar **um snapshot de fonte efetivamente montada**, separado por plataforma, sem copiar para um artefato público qualquer configuração/chave usada na compilação.
- Há dois painéis/admins legados: auditar-sst-master/ (HTML/CSS/JS) e a Central Online Google Apps Script. Podem fornecer referência visual/funcional, mas não podem ser hospedados como produção sem substituir a camada de chamadas.

## 2. Bloqueios verificáveis para execução direta em navegador

| Origem observada | Motivo | Tratamento para nova aplicação web |
| --- | --- | --- |
| lib/main.dart importa dart:io, sqflite e sqflite_common_ffi | A base assume sistemas desktop/mobile e usa Platform.isWindows/SQLite local | Eliminar dependência de APIs nativas no frontend web; fonte oficial de dados no servidor |
| pubspec.yaml contém path_provider, image_picker, file_picker, printing, share_plus e signature | Recursos de arquivo, impressão/câmera/assinatura requerem tratamento específico por navegador | Testar APIs de navegador e armazenamento temporário; centralizar mídia no backend |
| lib/services/auth_service.dart e device_sync_service.dart | Login, tokens, registros locais e alterações sincronizadas com a Central | Preservar contratos legados; criar sessão web nova, autenticação e autorização no backend |
| lib/services/web_service_config.dart usa String.fromEnvironment para AUDITAR_SYNC_KEY | Chave operacional não pode ser incluída no bundle JavaScript de um site | Segredo só no servidor; nunca expor variável ou dart-define equivalente ao frontend |
| Código Apps Script em painel_web_google_apps_script/Code.gs e MultiUser.gs | Regras atuais se apoiam em PropertiesService, Sheets/Drive e endpoint do GAS | Contratos de API próprios; adaptar integrações no servidor, sob autorização |
| build_sources/v3.29.106-client-portal/ClientPortal.html contém google.script.run | Chamadas do GAS existem no contêiner Apps Script, não numa página web externa comum | Substituir na nova UI por fetch autenticado da API própria |
| hostinger-media-api/index.php | API PHP de fotos/evidências existente, com chave de serviço e storage privado | Auditar autenticação por usuário/empresa e manter adaptador server-to-server |
| feature_sources/OperationalAgendaV1.gs | Agenda de tarefas e trilha de eventos usam planilhas Google | Implementar entidades e eventos no banco escolhido, com validação de papéis no servidor |
| feature_sources/ClientPortalTreatments_v1.gs | Linha do tempo de tratativas é aditiva, empresa/ocorrência vinculadas | Preservar ID, autor, ordem, decisão e motivo de rejeição em nova API |
| source_overrides/.../painel_web_google_apps_script/EpiSync.gs | Integração legada compartilhada com EPI aparece na árvore do SST | Inventariar dependência antes de separar serviços; não migrar EPI inadvertidamente |

Estas constatações se baseiam em arquivos consultados, não em uma execução do app no navegador.

## 3. Módulos funcionais e prioridade de migração

| Ordem | Módulo | Fontes de referência | Validação mínima |
| --- | --- | --- | --- |
| 0 | Login, perfis, empresas e permissões | auth_service.dart, MultiUser.gs, admin_access_policy_v329137.dart | Cliente A não vê dados da empresa B, inclusive URLs/IDs alterados |
| 1 | Home gerencial, pendências, nomes amigáveis de NC | executive_dashboard_screen_v33091.dart, field_operational_control_screen_v33091.dart, nc_title_store_v1.dart | Totais e filtros batem com origem |
| 1 | NC, tratamento/linha do tempo e evidência | ClientPortal.html, ClientPortalTreatments_v1.gs, correction_evidence_center_v329147.dart | Cliente informa correção; técnico valida ou rejeita com motivo; evento preservado |
| 1 | Agenda e supervisão | technician_agenda_screen_v330123.dart, OperationalAgendaV1.gs, TechnicianSupervisionCloud_v1.gs | ADM atribui; técnico visualiza; histórico e último visto consistentes |
| 2 | Vistorias, Ronda Expressa, planos de ação e diário de obra | quick_visit_screen_v329174_v33097.dart, worksite_* e nr18_* | Criação, edição, fotos e relatórios preservados |
| 2 | Relatórios PDF, assinatura, treinamento/DDS, documentos e CIPA | auditar_standard3_pdf_service_v329152.dart, training_activity_center_*, cipa_management_screen_* | PDFs e assinaturas não perdem dados nem qualidade |
| 3 | Assistente offline/IA e sincronização de rascunhos | offline_reasoning_v329175.dart, offline_sst_deep_catalog_v2.dart, device_sync_service.dart | Conflitos, fila offline, reenvio, permissão e limites testados |

## 4. Contratos legados identificados

- Google Apps Script doPost reconhece ações como auth_login (via MultiUser), device_sync_push, device_sync_pull, sync, drive_upload, ai_assistant e outras; não mapear apenas pelo nome, inspecionar payloads.
- Portal GS inclui clientPortalLogin, clientPortalData, clientPortalSubmitEvidence, clientPortalReviewEvidence, clientPortalReportPdf, clientPortalTreatmentList e clientPortalTreatmentPost.
- Agenda usa agenda_tecnicos_v1 com operação de listagem/criação/status e registro imutável no histórico.
- O atendimento de ocorrência usa assunto por companyId/topicId, incluindo tópico GERAL. O cliente não pode tomar decisões técnicas nem fechar NC unilateralmente.
- O sistema atual usa tabelas locais e snapshots publicados; não existe prova aqui de um banco web relacional que possa ser importado diretamente.

## 5. Riscos de compatibilidade e segurança

1. **Segredo no navegador:** nunca incorporar AUDITAR_SYNC_KEY, token de serviço Hostinger, chaves de IA ou credenciais Drive ao bundle.
2. **Isolamento multiempresa:** toda consulta e mutação requer verificação no servidor da identidade e empresa permitida. Não confiar no companyId enviado pela tela.
3. **Identidade/histórico:** manter IDs originais, datas/timezone, anexos e assinaturas; migração reversível e auditoria de diferenças.
4. **Offline:** a versão web precisa de decisão específica (online-first ou PWA com IndexedDB/filas). Não prometer paridade offline sem desenvolvimento/testes.
5. **Relatórios:** preservar evidências e qualidade do Padrão Auditar 3; PDF deve ser homologado em navegador e no backend.
6. **Dados sensíveis:** repositório público deve conter só código e dados fictícios; backups/chaves fora do Git e do diretório publicado.

## 6. O que ainda precisa de investigação

- Capturar snapshot montado Android v3.29.198 / Windows v3.30.126 e gerar manifesto de dependências/incompatibilidades web.
- Inventariar tabelas e colunas reais (incluindo migrações SQLite e Sheets), IDs e volume de registros por empresa.
- Identificar contratos exatos de autenticação/mídia/assinaturas/PDF sem publicar credenciais.
- Consultar detalhes da infraestrutura de destino, retenção e requisitos LGPD.
- Executar testes de aceitação numa cópia sanitizada dos dados, nunca diretamente em produção.
