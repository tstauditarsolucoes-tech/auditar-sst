# Contrato de integração CIPA — descoberta inicial (não implementado)

## Fontes verificadas
- Flutter legado: `build_sources/v3.29.76-cipa/cipa_management_service.dart` na branch `feature/client-panel-permissions-v329106`. Os registros são `SstRecord` persistidos via `AppDatabase.instance.upsertSstRecord`; `records(type, companyId)` filtra por empresa. Tipos: `CIPA_MANDATO`, `CIPA_MEMBRO`, `CIPA_REUNIAO`, `CIPA_ATA`, `CIPA_ACAO`, `CIPA_DOCUMENTO`, `CIPA_COMISSAO_ELEITORAL`. IDs gerados com UUID v4 quando não fornecidos; campos `payload` específicos por tipo.
- Portal novo: `Auditar-SST/web-migration/infra/api/cipaPortalService.mjs` na branch `migration/preparacao-web-20261027`. Usa PostgreSQL com tabelas `sst.cipa_mandate`, `sst.cipa_portal_action`, `sst.cipa_meeting`, `sst.cipa_portal_entry`, `sst.cipa_portal_grant`. Restringe operações por `company_id`, mandato e conta; eventos possuem `client_request_id` e hash para idempotência.

## Incompatibilidades e decisões obrigatórias
1. `SstRecord.id` e IDs PostgreSQL não devem ser tratados como equivalentes, mesmo que ambos sejam UUID. Criar tabela de correspondência `source_system + source_company_id + source_record_type + source_record_id -> target_company_id + target_record_id`, com unicidade, trilha de auditoria e validação do tenant. Não mapear por nome/e-mail.
2. O app atual persiste registros genéricos; o portal usa entidades relacionais e estados próprios. Mapear cada tipo e status, especialmente atas/assinaturas, antes de qualquer escrita bidirecional.
3. O app atual usa Central Online, e o portal usa banco próprio. Não conectar o cliente diretamente ao PostgreSQL, não compartilhar senha de serviço e não confiar em `companyId` fornecido pelo cliente.
4. Não publicar registros antigos automaticamente. Fazer importação experimental com dados sintéticos e comparação de contagens, anexos, checksums e histórico.
5. Eventos de conclusão e validação precisam de chave idempotente estável, controle de revisão e registro de origem. Uma confirmação de leitura não é presença nem assinatura.
6. O portal só pode receber ações explicitamente atribuídas ao membro autorizado. Dados da CIPA e NCs do cliente não podem ser expostos entre empresas.
7. Offline: manter fila local no app, reenviar com a mesma chave, confirmar somente após ACK persistido; conflitos devem exigir resolução explícita, sem sobrescrever anexos ou assinaturas.

## Sequência de implementação e aceite
- [ ] Inspecionar esquema `SstRecord`, transporte Central Online, autenticação e migrations PostgreSQL para fechar o contrato de campos.
- [ ] Criar testes de contrato para mandatos, membros, reuniões, ações, atas e anexos, com dados sintéticos e dois tenants.
- [ ] Implementar adaptador isolado em ambiente de teste com feature flag desativada por padrão, logs sem dados pessoais e modo somente leitura inicialmente.
- [ ] Implementar eventos de ida e volta, deduplicação e conflitos com testes de perda de rede, revogação e mudança de mandato.
- [ ] Homologar Android, Windows e portal em HTTPS privado, com backup e restauração, antes de habilitar escrita.

**Proibido nesta fase:** merge, deploy, alteração de Central Online em produção, migração automática, exclusão de dados, ativação do domínio final ou canal de denúncias.

Relacionado: #24 e #25.
