# Primeiro serviço de NCs da nova API (isolado, sem login real)

O arquivo `api/ncService.mjs` implementa regras de negócio da futura API do Auditar SST:
- Listar e criar não conformidades por empresa.
- Registrar evento inicial e histórico cronológico.
- Cliente pode informar correção com comentário.
- Apenas técnico/gestor/ADM pode validar ou rejeitar; rejeição exige motivo.
- Transições protegidas por lock `FOR UPDATE`, transação única e eventos preservados.
- Consultas parametrizadas e `SET LOCAL ROLE sst_app_runtime` + `app.company_id` em cada transação.

`api/server.mjs` define endpoints `/api/v1/nonconformities`, `/:id/events`, `/:id/correction`, `/:id/decision`. **Sem um verificador de sessão real injetado no servidor, todas essas rotas retornam 401 e NÃO acessam informações.** Headers como `x-role` e `x-company-id` são ignorados: não é possível fingir uma identidade pelo navegador.

Os testes `api/ncService.test.mjs` e `api/server.test.mjs` exercitam a lógica por meio de um banco simulado. O banco PostgreSQL real de homologação já tem tabelas/RLS testadas separadamente. **Ainda não existe conexão de produção, login, token ou sessão.**

## Como será integrado com segurança

1. Implementar autenticação nova revisada para a web e adaptadores autenticados Android/Windows, sem substituir a Central Online antes dos testes.
2. Resolver a sessão em objeto interno verificado `{companyId,userId,role}` a partir de identidade real e vínculos no banco; nunca dos campos enviados pelo cliente.
3. Configurar `pg.Pool` usando conta PostgreSQL NÃO superuser, secret separado, TLS conforme ambiente e concessão mínima de `sst_app_runtime`.
4. Injetar ambos no startup do servidor: `createApp({pool, resolvePrincipal})`. **Isto ainda não foi implementado no entrypoint de hospedagem**.
5. Criar testes de integração reais da API no banco com duas empresas, auditoria, concorrência e fluxo client→tecnico, seguidos dos testes de autorização.
6. Homologar comportamento offline, fotos/assinaturas, backups e migração de dados antes do domínio final.

O que está no GitHub é uma base de negócio e um contrato HTTP protegido por padrão. **Não afirmar que o CRUD real está acessível na VPS ou que o sistema está pronto para produção.**
