# Auditar SST — estado real e critérios de virada (27/10/2026)

**Branch:** migration/preparacao-web-20261027 · PR #23 DRAFT. **NÃO PUBLICAR NO DOMÍNIO FINAL.**

## Objetivo final

Android APK Flutter, Windows EXE Flutter e nova Web React/TypeScript devem compartilhar futuramente um backend Node/PostgreSQL na VPS. As interfaces instaladas não podem perder funções, arquivos, histórico ou uso offline. A origem Apps Script/Google Drive fica preservada até migração com backup, verificação e aceite.

## Disponível somente para homologação com dados fictícios

| Componente | Estado |
| --- | --- |
| Docker privado e Nginx Proxy Manager | Configuração pronta; sem deploy |
| PostgreSQL 17 e isolamento entre empresas | Testado em CI |
| Login Web, sessões seguras, CSRF | Piloto e CI |
| NCs, correções, rejeição/validação e histórico | Piloto e CI |
| Vistorias/Ronda, rascunho e achados | Piloto e CI |
| Agenda SST, prazos e designação | Piloto e CI |
| Plano de Ação vinculado à NC, prazo, responsável e histórico | Piloto, migração 008 e CI |
| Treinamentos, DDS e Integração (planejamento/andamento) | Piloto, migração 009 e CI; sem certificados ou listas de presença |
| CIPA (mandato, composição e reuniões) | Piloto, migração 010 e teste CI; sem voto, atas oficiais ou validação NR-5 |
| Painel Cliente, tickets e conversas | Piloto e CI |
| Central ADM e última atividade da Web | Piloto e CI |
| Fotos privadas JPEG/PNG/WebP no Docker | Piloto e CI, máximo 2 MB |
| PDF de vistoria de teste | Candidato com recomendação técnica e anexo de fotos maiores; sem Padrão Auditar 3 oficial |
| Android/Windows existentes | Preservados, sem migração de API |

## Primeiro passo disponível para inventário de cópias

O script privado tools/inventory-legacy-backup.mjs lê somente uma cópia local de backup e mostra contagens/tamanhos por tipo sem revelar nomes ou conteúdos. Não é um importador e não substitui a conferência manual. Consulte infra/GUIA_PRIVADO_JULIO.md.

## Nova auditoria do protocolo Flutter → Node (sem migrar dados)

Foi conferido o servico legado `device_sync_service.dart`: 16 tabelas SQLite, fila de mudancas, marcadores de exclusao, cursor e confirmacao das operacoes, atualmente usados via Apps Script. Criado um diagnostico autenticado, **somente com contagens ficticias** e retornando explicitamente `BLOCKED_FOR_REAL_SYNC`. O servidor NOVO nao recebe registros, nao confirma fila e nao substitui backend antigo. Veja [MATRIZ_COMPATIBILIDADE_LEGADA_20261027.md](MATRIZ_COMPATIBILIDADE_LEGADA_20261027.md).

## Bloqueios reais antes da produção

- [ ] Inventariar Apps Script, Sheets e Drive; exportar tudo com autorização específica.
- [ ] Conciliar contagens, IDs, históricos e hashes de arquivos por empresa sem sobrescrever origem.
- [ ] Migrar autenticação de usuários com processo auditado, recuperação de acesso e revisão de segurança.
- [ ] Implementar cliente Android e Windows para nova API, fila offline e resolução de conflitos.
- [ ] Migrar fotografias, assinaturas, documentos e PDFs preservando referências e visual.
- [ ] Finalizar módulos faltantes e paridade: CIPA legal e eleitoral, certificados/listas de presença e importação do histórico de DDS/treinamentos, integração do Plano de Ação legado, IA, notificações, relatórios Auditar 3, Supervisão completa.
- [ ] Cotas, varredura de mídia, criptografia, retenção, logs, backups regulares do banco + volume e teste de restauração.
- [ ] Testes físicos Android, Windows e navegador: offline, câmera, assinatura, PDF, grupos, permissões e conexão lenta.
- [ ] Testes de carga, falhas, atualização sem zerar cache, e acesso separado de empresas.
- [ ] Plano de rollback e aceite escrito antes de redirecionar tst.auditarsolucoes.com.br.

## Ações não autorizadas

Não apagar/mover dados reais; não reutilizar credenciais de produção; não enviar fotos ao GitHub; não mesclar PR #15 ou #23; não alterar DNS/Proxy Host existente; não executar limpeza de volumes, nem interromper sistemas vizinhos da VPS.

## Handoff

O Júlio deve seguir o guia privado [infra/GUIA_PRIVADO_JULIO.md](infra/GUIA_PRIVADO_JULIO.md), escolher URL HTTPS exclusiva de homologação e realizar testes com dados sintéticos e Access List NPM. O usuário só autorizará a virada após validação de integridade, paridade e restauração.

**CI bem-sucedida é evidência de testes de código, não homologação física ou liberação para produção.**
