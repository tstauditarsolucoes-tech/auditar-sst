# Primeira interface React/TypeScript do Auditar SST — Docker isolado

**Protótipo funcional com DADOS FICTÍCIOS. Não é versão completa e NÃO usa dados de produção.**

O pacote contém:
- `web/`: interface React 19 + TypeScript + Vite, responsiva para computador e celular, com funcionalidades reais **portadas de Dart** para matrizes de prioridade e nomes amigáveis das NCs. Filtros e edição nesta tela estão funcionais, mas não persistem ao recarregar;
- `api/`: Node.js 24, somente GET /api/v1/health;
- `db`: PostgreSQL 17 com volume de teste próprio, sem tabelas de clientes e sem conexão com o aplicativo;
- Nginx web na porta 8080 **somente dentro das redes Docker**, com proxy /api/ para Node.

**Não contém login ou conta real, importação de dados, sincronização, fotografias, assinaturas, agenda ou PDF.** Os cartões demonstrativos usam identificadores `DEMO-NC-...`, nunca dados de empresas reais.

## Testar só a lógica e a compilação do frontend

No diretório `infra/web`, com Node.js 24:

```bash
npm install --no-audit --no-fund
npm run test
npm run build
```

Para desenvolvimento local, `npm run dev`; a API de saúde só responde no ambiente com proxy Node. A aplicação funciona para demonstração mesmo com a API indisponível. O Dockerfile constrói o bundle React antes de servir os arquivos estáticos via Nginx.

Consulte [web/MIGRACAO_DART_PARA_TYPESCRIPT.md](web/MIGRACAO_DART_PARA_TYPESCRIPT.md) para funções portadas e limites.

## Domínio e Nginx Proxy Manager

O endereço `tst.auditarsolucoes.com.br` **já atende outro sistema, que o proprietário pretende substituir somente na virada final**. Siga [PLANO_DE_VIRADA_DO_DOMINIO_TST.md](PLANO_DE_VIRADA_DO_DOMINIO_TST.md) e [GUIA_NGINX_PROXY_MANAGER_TST.md](GUIA_NGINX_PROXY_MANAGER_TST.md). Não mudar rota, DNS, contêiner, domínio ou dados existentes agora. `compose.npm.example.yml` é apenas exemplo de rede externa.

## Isolamento dos serviços da VPS compartilhada

- O Compose NÃO publica `80`, `443`, `3000`, `5432` nem `8080` no host.
- API/PostgreSQL isolados na rede backend; frontend em rede do projeto.
- Senhas de banco lidas de segredo externo, nunca registradas no GitHub.
- Nenhuma operação sobre a Central Online, Apps Script, Drive, banco real ou serviços existentes.
- Sem reinicialização automática. Sem implantação na VPS.
- Nunca executar `docker compose down --volumes` num ambiente contendo dados.

## Homologação Docker pelo programador (somente após autorização)

1. Em ambiente reservado, criar `infra/secrets/postgres_password` com senha forte e acesso restrito (fora do Git).
2. Na pasta `infra`, verificar antes: `docker compose -p auditar-sst-web-hml -f compose.staging.yml config --quiet`.
3. Se autorizado em staging, subir isoladamente: `docker compose -p auditar-sst-web-hml -f compose.staging.yml up --build -d`.
4. Conferir `docker compose -p auditar-sst-web-hml -f compose.staging.yml ps`.
5. API: `docker compose -p auditar-sst-web-hml -f compose.staging.yml exec api node -e "fetch('http://127.0.0.1:3000/api/v1/health').then(r=>r.json()).then(console.log)"`.

**O frontend não ficará acessível pela internet até o administrador configurar um endereço de staging/proxy; isso não foi feito.** Não abrir diretamente o banco ou a API para a internet.

## Faltam para lançamento real

Identidade/autenticação, isolamento de empresas, API de NCs, auditoria, histórico, fotos e assinaturas, tarefas/agenda, documentos/PDF, painel do cliente e ADM, migração verificada dos dados e testes de segurança/carga/recuperação, backup/restauração e virada planejada do domínio. O OpenAPI é ainda um contrato proposto.

A pasta `web/static/` é a sonda estática antiga: permanece versionada como referência, mas **não é utilizada na nova imagem**.
