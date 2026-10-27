# Roteiro de migração para aplicação web em servidor próprio

**Proposta técnica não implantada.** Prioridade: não perder registros/fotos/assinaturas nem interromper Android e Windows.

## 1. Arquitetura sugerida

Navegador (PC/celular)
-> Frontend responsivo React + TypeScript (Vite)
-> HTTPS / reverse proxy
-> API autenticada /api/v1 em servidor próprio
-> banco relacional com empresas/perfis/ocorrências/eventos
-> armazenamento privado de fotos, PDFs e assinaturas
-> serviços de e-mail/geração de PDF/auditoria e adaptadores de compatibilidade com Central Online.

Se o servidor for VPS, avaliar Fastify/NestJS + PostgreSQL; se for hospedagem exclusivamente PHP, avaliar framework PHP e banco que a infraestrutura suporta. A escolha depende do Julio/servidor; não há dependências instaladas nem runtime criado nesta entrega. OpenAPI é o contrato neutro.

**Por que sugerir uma UI web separada:** a base Flutter usa APIs nativas e componentes preparados para Android/Windows. Flutter Web também é tecnicamente possível e não exige instalação pelos clientes; a escolha React/Vite só faz sentido se a Auditar preferir interfaces web convencionais com DOM, rotas, responsividade e backend independente.

## 2. Transição em fases e portas de aprovação

### Fase 0 — inventário e proteção
- Identificar dono do servidor, DNS, TLS, banco, backups, storage e acesso técnico.
- Congelar referência de código, gerar snapshot de fonte montada e inventariar endpoints/tabelas/eventos.
- Backup verificável do ambiente atual e amostra anonimizada.
- Aprovar modelo multiempresa, perfis e política de fotos/assinaturas.
**Aceite:** inventário conferido pela Auditar, plano de reversão e hashes de referência.

### Fase 1 — fundação web sem dados reais
- App frontend com navegação responsiva e estados de carregamento legíveis.
- API /api/v1 separada, autenticação de sessão com cookie HttpOnly/Secure/SameSite, proteção CSRF conforme a estratégia, rate limiting e auditoria.
- Banco de homologação; migrações versionadas; testes de isolamento por empresa; observabilidade.
- Recursos iniciais: login, empresas autorizadas, dashboard e NCs **em dados fictícios**.
**Aceite:** testes automatizados incluindo acesso indevido entre empresas, sem segredos no frontend.

### Fase 2 — fluxo vertical de NC/Agenda
- Cliente sinaliza correção com texto/foto; técnico recebe, valida ou rejeita com motivo.
- Eventos de tratativa imutáveis, com autor/hora/empresa, referência à NC e notificações rastreáveis.
- Agenda administrativa para atribuir tarefas e acompanhar status.
- Fotos armazenadas privadas e acessadas via autorização, não via caminho público direto.
**Aceite:** testes ponta a ponta para cliente, técnico e ADM e rastreabilidade auditável.

### Fase 3 — vistorias e documentos
- Vistorias, Ronda Expressa, planos de ação, NR-18, treinamentos, DDS, CIPA e documentos.
- Geração de relatórios Padrão Auditar 3; fotos grandes, assinaturas, paginação e exportação.
- Compartilhamento protegido por empresa, múltiplos destinatários apenas com consentimento e trilha de envio.
**Aceite:** comparar PDFs/contagens/permits com amostra validada no sistema atual.

### Fase 4 — dados históricos e convivência
- Extrair dados com aprovação, mapear IDs e tabelas, registrar divergências e migrar para banco staging.
- Verificar contagens, checksums de anexos, vínculos por empresa e histórico antes/depois.
- Rodar em paralelo à Central Online; definir fonte única para cada entidade e regra de reconciliação.
- Não implementar sincronização bidirecional nova sem autorização e testes contra conflitos.
**Aceite:** backup/restauração testados, nenhuma mídia perdida, rollback executável em simulação.

### Fase 5 — offline e homologação
- Decidir se web começa online-first ou PWA offline. Se offline: IndexedDB, filas, IDs idempotentes, criptografia/expiração e conflitos testados.
- Homologar Chrome/Edge/Firefox/Safari e Android/iOS em aparelhos reais.
- Testar acessibilidade, letras grandes, rede lenta, upload de foto, câmera, impressão, sessão, CORS e falhas.
- Acesso inicial restrito à Auditar; liberação por empresa após aceite escrito.

## 3. Regras de negócio a preservar

- Empresas e grupos; técnicos e administradores com permissões específicas por empresa.
- NCs abertas com título amigável, risco, prazo, prioridade e evidências.
- Cliente pode informar correção; não pode validar tecnicamente. Técnico pode validar ou rejeitar com motivo.
- Linha do tempo de tratativas cronológica, sem sobrescrever eventos antigos.
- Agenda com responsável, atribuidor, histórico, status e prazo.
- Relatórios sempre associados à empresa, vistoria e evidências corretas.
- Login e histórico offline dos apps instalados permanecem intactos durante a migração.

## 4. Modelo de dados alvo (conceitual, sem SQL de produção)

- company, company_group, user, user_company_permission, session
- inspection, non_conformity, nc_treatment_event, action_plan, evidence
- task, task_event, visit, report, report_delivery
- training, dds, cipa, document, audit_log, outbox_event

IDs legados devem ter coluna de correlação; eventos relevantes são append-only; evidências têm checksum, MIME, tamanho, proprietário e política de acesso. O contrato proposto em API_WEB_PROPOSTA.yaml é uma **primeira discussão**, não um formato validado de migração.

## 5. Critérios de go/no-go para produção

- ZERO segredos operacionais em JavaScript ou arquivos públicos.
- ZERO leitura ou escrita não autorizada entre empresas em testes automatizados.
- 100% das amostras de fotos/assinaturas de teste migradas com checksums iguais.
- Registro de auditoria em correção, rejeição, validação e atribuição de agenda.
- Restauração verificada, rollback documentado e backup periódico.
- Aprovação da Auditar após testes em PC/celular. Nunca publicar sem essa aprovação.
