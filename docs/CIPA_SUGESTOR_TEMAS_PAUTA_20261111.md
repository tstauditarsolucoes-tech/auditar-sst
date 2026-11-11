# Assistente de Temas e Pautas da CIPA — homologação (11/11/2026)

## Proposta
Complementar a **Reunião assistida: antes e depois** já existente no Auditar SST Android/Windows com um único botão grande: **Sugerir tema para a pauta da ata**.

O responsável escolhe o ramo/setor, confere sugestões de temas, visualiza os pontos a discutir e usa **Copiar pauta e abrir reunião** para continuar no editor original. A pauta pode ser editada livremente antes de sua utilização.

## Base das sugestões
- Roteiros por setor: geral, cerâmica, construção civil, panificação, laticínios, logística e depósitos, limpeza urbana e comércio/escritórios.
- Se há ações em aberto **no mandato e empresa em uso**, prioriza a sugestão **Acompanhamento das ações pendentes da CIPA**, com quantidade em aberto e quantidade vencida extraídas dos registros já existentes.
- Temas gerais de participação dos trabalhadores, prevenção do assédio e melhoria contínua, **sem presumir acidentes ou denúncias**.
- Não encaminha ou compartilha automaticamente as informações com outras empresas.

## Segurança da ata
A sugestão é um **rascunho de pauta pré-reunião**, não uma ata. Não preencher automaticamente nomes de presentes, presenças, falas, votações, decisões, responsáveis, prazos, assinaturas ou ciência de integrantes. Esses fatos devem ser registrados após a reunião e conferidos pela pessoa responsável.

O assistente não altera a base de dados, a autenticação ou o status de não conformidades; apenas consulta os dados já disponíveis na sessão atual e prepara texto para cópia. Não é certificado de cumprimento da NR-05.

## Integração e limites
Implementado em `feature_sources/cipa_meeting_coach_rules_v1.dart` e `feature_sources/cipa_meeting_coach_home_v1.dart`. O instalador `tools/patch_cipa_meeting_coach_v1.py` integra o cartão à tela `cipa_management_screen.dart` **somente em uma cópia de homologação** e declara o suporte à área de transferência, sem sobrescrever os documentos originais nem alterar o aplicativo em produção.

O editor da reunião é aberto por uma ação explícita, mas o texto **não é inserido automaticamente** no campo de pauta: o responsável precisa colar e revisar. Em ambiente com proibição de uso da área de transferência, o texto permanece selecionável.

## Testes
- Cenários puros de sugestões dos setores, pendências, vencimentos, validação de entradas e ausência de fatos inventados.
- Fixture Flutter para escolha do tema e abertura explícita do editor.
- Teste do instalador em cópia temporária, com proteção dos demais arquivos.
- Antes de disponibilizar: testar no Android/Windows real, avaliar suporte à cópia/cola, textos grandes, credenciais e vínculos reais, fluxo de ata pós-reunião e reversão.

**Não houve instalação, merge de PR, publicação do Web/VPS do Júlio ou ativação de contas de membros.**
