# Auditar SST Web — migração incremental (27/10/2026)

**Estado: primeira parte funcional migrada; não é o sistema completo nem release de produção.**

O objetivo é preparar uma nova tecnologia web na branch isolada `migration/preparacao-web-20261027` para o programador Júlio César Angelim. As versões Android/Windows, a Central Online e a Gestão EPI continuam intactas.

## O que já foi convertido de Flutter/Dart

- **Matriz de risco:** cálculo de pontuação (1 a 25), bônus de recorrência (+2, limitado a 25) e faixas Baixa/Média/Alta/Crítica portados para `infra/web/src/domain/nc.ts`.
- **Nomes amigáveis das NCs:** normalização, limite de 80 caracteres, fallback da primeira frase, preservação do ID e da descrição original. Esta demonstração edita nomes somente em memória (sem persistência).
- **Interface React + TypeScript:** dashboard responsivo, simulador de prioridade, filtros de NCs fictícias e edição de nomes, no diretório `infra/web/src/`.
- **Testes automatizados** das funções portadas e build de frontend na GitHub Actions.

Veja os detalhes em [infra/web/MIGRACAO_DART_PARA_TYPESCRIPT.md](infra/web/MIGRACAO_DART_PARA_TYPESCRIPT.md) e os comandos Docker em [infra/README.md](infra/README.md).

### O que NÃO foi migrado ainda

Não há acesso a NCs reais, autenticação, sincronização, banco de clientes, fotos, assinaturas, relatórios/PDF, agenda, CIPA, IA, painel do cliente ou Central ADM. Backend Node responde somente no endpoint de saúde. O banco PostgreSQL de staging está vazio. A migração dos dados exigirá consentimento específico, backup, validação de permissões e homologação. Não confundir com produto pronto.

## Decisão confirmada: Android, Windows e Web\n\nO objetivo **não é substituir o app instalado por um site**. São três clientes do mesmo Auditar SST: APK Android e EXE Windows atuais, preservados em aparência/fluxo/offline; mais um novo portal Web com paridade de funcionalidades. O Apps Script será substituído gradualmente por um **backend único próprio** após testes de migração e segurança. Leia [DECISAO_3_VERSOES_SERVIDOR_PROPRIO.md](DECISAO_3_VERSOES_SERVIDOR_PROPRIO.md).\n\n## Documentos técnicos para o programador

1. [AUDITORIA_DO_CODIGO.md](AUDITORIA_DO_CODIGO.md) — diagnóstico de fontes e obstáculos de portabilidade.
2. [PLANO_DE_MIGRACAO.md](PLANO_DE_MIGRACAO.md) — plano de arquitetura e etapas com critérios de aceite.
3. [API_WEB_PROPOSTA.yaml](API_WEB_PROPOSTA.yaml) — contrato OpenAPI futuro, **não implementado**.
4. [CHECKLIST_PARA_O_PROGRAMADOR.md](CHECKLIST_PARA_O_PROGRAMADOR.md) — decisões e testes restantes.
5. [infra/PLANO_DE_VIRADA_DO_DOMINIO_TST.md](infra/PLANO_DE_VIRADA_DO_DOMINIO_TST.md) — substituição futura segura da rota existente.

## Infraestrutura informada em 27/10/2026

VPS compartilhada com outros sistemas, Docker, Node.js e banco em contêiner; Nginx Proxy Manager. Domínio final `tst.auditarsolucoes.com.br`, hoje ocupado por outro sistema que será retirado **apenas após a homologação do novo sistema e plano de reversão**. Nenhuma instalação, remoção, troca de proxy ou domínio foi feita.

A stack React/Vite/TypeScript + Node/PostgreSQL é uma proposta de migração incremental. Flutter Web também serve páginas sem instalar arquivos no dispositivo do usuário, mas plugins/arquivos/SQLite atuais requerem análise. A escolha e o plano de produção precisam ser revisados com o programador.

## Repositório e precauções

- Fonte SST original: branch `organize/sst-em-pasta-20261027`, SHA inicial `b331fb9a1fc88755cdc00652e110ed9d0a7185e4`.
- Os aplicativos Android/Windows e Central seguem disponíveis durante a reconstrução.
- Branch web específica não altera autenticação, sincronização, IA, Google Apps Script, fotos/Drive nem dados persistentes.
- Este código está em repositório público: nunca incluir senhas, chaves, usuários reais ou arquivos de clientes.
- O PR web permanece **DRAFT** até revisão e testes.
