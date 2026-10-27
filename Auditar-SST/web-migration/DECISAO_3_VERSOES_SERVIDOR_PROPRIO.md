# Decisão de arquitetura — UM Auditar SST, TRÊS interfaces, servidor próprio
Data: 27/10/2026. Diretriz confirmada pelo proprietário (Luan/Auditar).

**Decisão complementar aprovada:** todas as informações e mídias do sistema novo serão armazenadas no servidor próprio. O Drive será somente fonte legada de migração e não fará parte da arquitetura final. Ver [ARMAZENAMENTO_PROPRIO_SEM_DRIVE.md](ARMAZENAMENTO_PROPRIO_SEM_DRIVE.md).

## Objetivo de produto, sem ambiguidade

**Preservar o aplicativo Auditar SST atual como produto Android e Windows e adicionar uma versão Web nativa de navegador.** As três versões devem compartilhar os mesmos dados e regras no backend da Auditar, **substituindo a dependência operacional do Google Apps Script/Central Online por serviços próprios**, após migração verificada. Não é um projeto de substituir o APK e EXE por um simples site/PWA.

| Canal | Aplicativo alvo | Regra de compatibilidade |
| --- | --- | --- |
| Android | APK instalável atual (Flutter) | Preservar fluxo, telas, fotografia/câmera, assinatura, offline, rascunhos e desempenho; alterações internas de transporte somente após contrato/testes |
| Windows | EXE instalador + opção portátil existentes (Flutter) | Preservar interface adaptada ao PC, atalhos, PDF/impressão, offline e fluxo atual; atualizar mecanismo de API sem quebrar uso |
| Web | React/TypeScript, acessado pelo navegador, responsivo | Reproduzir os módulos essenciais e permissões do produto, com layouts adaptados; sem necessidade de APK/EXE |

O objetivo é **paridade funcional**, não igualdade de pixels entre desktop, telefone e web. A navegação das versões instaladas continua familiar; alterações de banco/sincronização são internas, separadas, auditadas e homologadas.

## Backend alvo (uma única autoridade)

- API Node.js hospedada em contêiner Docker na VPS compartilhada, atrás do Nginx Proxy Manager e HTTPS.
- PostgreSQL isolado por banco/volume próprio com migrações versionadas e backups/restauração testados.
- Mídia privada **no servidor próprio**: fotos, assinaturas, evidências e PDFs em armazenamento de objetos privado, acessados via API com autorização por usuário/empresa e integridade verificável; sem Drive operacional. Backups criptografados em local independente da VPS.
- Identidade e autorização: perfis cliente, técnico, gestor, ADM; vinculação por empresa e grupos; trilha de auditoria.
- Agenda, NC, vistorias, relatórios e tratativas como serviços/contratos compartilhados pelos três clientes.
- Um único sistema de identificação e eventos com IDs imutáveis, autoria e históricos preservados.

```text
   [Android / Flutter] -------\
   [Windows / Flutter] --------> API Auditar SST / Node ---- PostgreSQL
   [Web / React] -------------/                  \--------- Mídia privada
                  HTTPS via Nginx Proxy Manager
```

O domínio final será `tst.auditarsolucoes.com.br`. **Atualmente aponta para um sistema errado que só poderá ser substituído com autorização explícita para a virada, backup, testes e rollback.** A simples criação desta branch não altera proxy, domínio, Docker, senhas nem serviços existentes.

## Compatibilidade, dados existentes e modo offline

1. Congelar inventário de tabelas/entidades, APIs Apps Script, versões de aplicativos, esquemas locais, volumes Drive/Hostinger e permissões reais.
2. Criar API nova em paralelo; **não desligar o Apps Script** durante o desenvolvimento.
3. Implementar contratos de API versionados (`/api/v1`) e testes de autorização multiempresa antes de conectar apps reais.
4. Desenhar adaptador de transporte Android/Windows com mecanismo de versionamento/migração de armazenamento local; preservar fila offline, chaves locais, rascunhos, fotos e conflitos.
5. Migrar dados para homologação com exportação autorizada, IDs de correlação, contagens, checksums de anexos e comparação por empresa.
6. Testar em paralelo com amostras e decidir uma **fonte de verdade por etapa**. Sem escrita simultânea sem regra de reconciliação aprovada.
7. Fazer compilações de teste APK/EXE e homologar Android, Windows e Web, inclusive modo offline e rede instável.
8. Após aceite da Auditar, executar corte controlado de sincronização, janela de virada do domínio e descomissionamento do Apps Script, mantendo backup e capacidade de retorno.

**Não implementar a substituição da autenticação/sincronização real, migração de fotos ou acesso a banco de produção antes de plano de dados e aprovação específica.**

## Paridade funcional mínima (três clientes)

- Contas por empresa/grupo, login e permissões; central ADM com criação de contas e supervisão.
- Vistorias, Ronda Expressa, rascunhos, evidências antes/depois, assistente offline e conclusões sem IA.
- NCs com títulos amigáveis, prioridade, recorrência e validação/rejeição de correção com motivo e histórico.
- Agenda com atribuidor, responsável, notificação, prazo e acompanhamento.
- Painel do Cliente com pendências, fotos de correção, linha do tempo, comunicação e solicitações.
- Treinamentos/DDS, CIPA, documentos, relatórios/PDF Padrão Auditar 3 e envios seguros.
- Legibilidade no Windows, layouts móveis adaptativos, carregamento incremental/cache e não apagar cache entre sessões.
- Fotos e assinaturas originais intactas, trilha de auditoria e segregação rigorosa entre empresas.

Recursos que dependam de hardware (biometria, câmera, impressão) precisam de mecanismos específicos por plataforma; não presumir equivalência sem teste.

## Entregas e critérios verificáveis

| Entrega | Critério |
| --- | --- |
| Fundação web isolada | Build React, testes e Docker sem deploy — primeira prova técnica já em PR #23 |
| Contratos do servidor | API autenticada, teste de acesso cruzado por empresa, histórico e migrações de banco de staging |
| Primeiro fluxo ponta a ponta | NC fictícia criada no web, visível no Android/Windows de teste e vice-versa, sem Apps Script |
| Migração de dados staging | Contagens, vínculos, hashes de fotos/assinaturas e relatórios íntegros |
| Homologação das 3 versões | APK, EXE e web aceitos pelo técnico, cliente e ADM; teste offline/sincronização |
| Produção | Backups/restore, métricas, plano de rollback, virada autorizada do domínio e desligamento supervisionado dos scripts legados |

### Progresso real em 27/10

- CI React/TypeScript + Docker validada; matriz de risco e nomes amigáveis de NC portados **somente para protótipo web com dados fictícios**, sem persistência.
- Backend próprio ainda contém apenas endpoint de saúde; Postgres staging vazio.
- Android e Windows não foram conectados ao novo backend; sem mudança nos GS, sincronização ou dados.
- **Nenhum deploy ou migração de dados reais foi feito.**
