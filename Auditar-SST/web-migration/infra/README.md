# Base executável de homologação Docker — Auditar SST Web

**Somente infraestrutura/sonda isolada. Não é migração funcional do app e NÃO usa dados de produção.**

Este pacote cria, em um projeto Docker Compose separado:
- web: página estática de verificação com proxy /api/ pelo Nginx;
- api: Node.js 24 LTS, com apenas GET /api/v1/health;
- db: PostgreSQL 17 com volume próprio, ainda sem tabelas de clientes.

O portal definitivo será desenvolvido em React + TypeScript; o componente estático atual apenas prova que navegador -> proxy -> Node funciona. Nenhum login simulado ou dados fictícios de clientes são apresentados como reais.

**Domínio ocupado:** o proprietário confirmou que tst.auditarsolucoes.com.br está servindo um sistema que será substituído. Leia primeiro [PLANO_DE_VIRADA_DO_DOMINIO_TST.md](PLANO_DE_VIRADA_DO_DOMINIO_TST.md); nenhuma troca está autorizada agora.

## Integração com Nginx Proxy Manager e domínio informado

- Domínio final indicado: tst.auditarsolucoes.com.br.
- Proxy existente: Nginx Proxy Manager.
- Leia [GUIA_NGINX_PROXY_MANAGER_TST.md](GUIA_NGINX_PROXY_MANAGER_TST.md) antes de alterar qualquer rota.
- O arquivo [compose.npm.example.yml](compose.npm.example.yml) é um override opcional com rede externa, sem host ports.
- **Não foi criado nem alterado qualquer Proxy Host; não substitua um serviço já usando esse domínio.**

## Por que não interfere nos outros sistemas da VPS

- Nenhum serviço usa ports: **não publica 80, 443, 3000 nem 5432 no host**.
- Rede backend interna para API/PostgreSQL; rede frontend_net exclusiva do projeto.
- Banco e volume isolados pelo nome de projeto Compose.
- Nenhum segredo, conta, dado pessoal, foto ou banco existente é acessado.
- Não conecta a Central Online/Apps Script/Hostinger; não modifica aplicativos existentes.
- Não liga restart automático. A inclusão no domínio/proxy real depende de aprovação.

## Testes seguros (para o programador; não foram executados na VPS)

1. Em ambiente de homologação, crie localmente a pasta infra/secrets e o arquivo infra/secrets/postgres_password com senha aleatória forte, protegido por permissões restritas. **Nunca versionar ou compartilhar esse arquivo**.
2. Verifique primeiro a configuração com:
   docker compose -p auditar-sst-web-hml -f compose.staging.yml config --quiet
3. Execute os testes do Node localmente:
   node --test api/server.test.mjs
4. Crie os contêineres apenas em ambiente autorizado:
   docker compose -p auditar-sst-web-hml -f compose.staging.yml up --build -d
5. Confira estado e logs com docker compose ps e docker compose logs (mesmos parâmetros -p/-f).
6. Confirme a API dentro do próprio contêiner:
   docker compose -p auditar-sst-web-hml -f compose.staging.yml exec api node -e "fetch('http://127.0.0.1:3000/api/v1/health').then(r=>r.json()).then(console.log)"

A interface web não ficará acessível externamente até o administrador conectar o proxy reverso existente à rede/container web, ou configurar um binding controlado apenas para homologação. **Não abrir 5432 ou a API diretamente na internet.**

## Próximas etapas antes de qualquer deploy

- Confirmar qual proxy reverso já existe na VPS (Traefik, Nginx, Caddy, Portainer etc.), domínio de staging e portas internas livres.
- Criar políticas de backup/restore para o novo volume Postgres antes de inserir dados.
- Implementar login/tenants no backend, React frontend e testes de segurança; exigir cookies seguros, CSRF e trilha de auditoria.
- Somente depois, migrar NC/agenda/fotos em cópia de homologação com aprovação.
- Não executar docker compose down --volumes; remover volumes pode causar perda de dados.

O contrato funcional proposto está em ../API_WEB_PROPOSTA.yaml. A implantação real na VPS ainda depende de autorização e revisão do programador.
