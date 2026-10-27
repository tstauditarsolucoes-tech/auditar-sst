# Primeiro serviço de NCs da nova API (isolado, sem login real)

O arquivo `api/ncService.mjs` implementa regras de negócio da futura API do Auditar SST:
- Listar e criar não conformidades por empresa.
- Registrar evento inicial e histórico cronológico.
- Cliente pode informar correção com comentário.
- Apenas técnico/gestor/ADM pode validar ou rejeitar; rejeição exige motivo.
- Transições protegidas por lock `FOR UPDATE`, transação única e eventos preservados.
- Consultas parametrizadas e `SET LOCAL ROLE sst_app_runtime` + `app.company_id` em cada transação.

`api/server.mjs` define endpoints `/api/v1/nonconformities`, `/:id/events`, `/:id/correction`, `/:id/decision`. **Sem um verificador de sessão real injetado no servidor, todas essas rotas retornam 401 e NÃO acessam informações.** Headers como `x-role` e `x-company-id` são ignorados: não é possível fingir uma identidade pelo navegador.

Os testes `api/ncService.test.mjs` e `api/server.test.mjs` exercitam a lógica com banco simulado. **A CI agora também executa `api/integration.ci.test.mjs` contra PostgreSQL 17 REAL, efêmero e sem dados de clientes**, usando o usuário de teste sem SUPERUSER nem BYPASSRLS e duas empresas fictícias: criação, listagem, correção, rejeição, validação, histórico e isolamento. A seed `db/tests/seed_nc_integration_ci.sql` tem bloqueios para não ser aplicada em banco real/persistente. **Ainda não existe conexão de produção, login, token ou sessão.**

## Como será integrado com segurança

1. Implementar autenticação nova revisada para a web e adaptadores autenticados Android/Windows, sem substituir a Central Online antes dos testes.
2. Resolver a sessão em objeto interno verificado `{companyId,userId,role}` a partir de identidade real e vínculos no banco; nunca dos campos enviados pelo cliente.
3. Configurar `pg.Pool` usando conta PostgreSQL NÃO superuser, secret separado, TLS conforme ambiente e concessão mínima de `sst_app_runtime`.
4. Injetar ambos no startup do servidor: `createApp({pool, resolvePrincipal})`. **Isto ainda não foi implementado no entrypoint de hospedagem**.
5. Expandir os testes API×PostgreSQL CI já existentes para identidade real, sessões, auditoria, concorrência, evidências e autenticação, sem usar a seed fictícia em dados persistentes.
6. Homologar comportamento offline, fotos/assinaturas, backups e migração de dados antes do domínio final.

O que está no GitHub é uma base de negócio e um contrato HTTP protegido por padrão. **Não afirmar que o CRUD real está acessível na VPS ou que o sistema está pronto para produção.**


## Nova autenticação web — migração 002 (SOMENTE homologação)

`infra/db/migrations/002_web_auth.sql` cria credenciais com scrypt e sessões contendo apenas hash SHA-256 do token. O novo `api/authService.mjs` valida e-mail/senha, vínculo ativo por empresa e revogação; usa cookie `__Host-` com `HttpOnly`, `Secure`, `SameSite=Lax`, `Path=/` e expiração de 8 horas, mais checagem de `Origin` HTTPS fixo e token CSRF nas mutações. A seleção de empresa consulta o vínculo real na nova base a cada troca. O role `sst_auth_runtime` recebe acesso às tabelas de autenticação **mas não a vistorias e NCs**, enquanto `sst_app_runtime` não lê senhas/sessões. São conexões separadas.

**CI:** `api/integration.auth.ci.test.mjs` testa o login apenas com usuário/senha de exemplo (`example.invalid`) em PostgreSQL efêmero, autorizações, CSRF, isolamento entre empresas, troca de vínculo e logout. A seed `db/tests/seed_auth_integration_ci.sql` não deve ser usada na VPS.

**Não habilitado no contêiner entregue:** o `server.mjs` continua chamando `createApp()` sem pools nem `authService`; assim, endpoints de login/NC retornam 401 por padrão. Antes da ativação, implementar configuração segura de credenciais de duas contas de DB, validação de proxy HTTPS, proteção contra força bruta/rate limiting, provisionamento e recuperação de senhas, logs de segurança, revisão de cookies/CSRF, limpeza de sessões, backup e ensaio real de homologação. Nenhuma conta legada foi importada. **Isto não é login de produção.**


O frontend React inclui `web/src/WebAuthPilot.tsx`, aba **Acesso de homologação**, preparada para consumir estas rotas com cookie HttpOnly, token CSRF e troca de empresa. Como o entrypoint não habilita auth, a aba exibe uma orientação de configuração e não aceita contas reais. Ações nessa aba só terão efeito no banco NOVO de homologação quando o backend for ativado intencionalmente, diferentemente dos demais exemplos do protótipo.
