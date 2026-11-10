# Portal Minha CIPA — Vistoria orientada de observação visual

Escopo: cliente **Android separado para membros da CIPA**, associado ao aplicativo atual Android/Windows de gestão. Não faz parte do projeto Web/VPS. A sessão individual e o vínculo empresa/mandato/membro precisam ser confirmados pelo servidor antes de habilitar o portal.

## Entrega de desenvolvimento

A tela `Minha CIPA` oferece o botão **Fazer vistoria orientada** somente quando o callback de observação foi autorizado. O membro informa setor/local, escolhe tema e responde perguntas simples com **Sim / Não / Não sei/não verifiquei**. Há campo opcional para observação. Temas: organização e circulação, máquinas/equipamentos, incêndio/emergência, ambiente/proteção.

O roteiro gera texto identificável como **OBSERVAÇÃO VISUAL** e reutiliza `onObserve(place,note)`, a via de registro já prevista para o portal pessoal. Não cria autorização adicional, não grava diretamente no banco, não envia fotos, não classifica o risco nem abre/fecha NC. O formulário apresenta resultado de envio **apenas quando o callback autorizado conclui com sucesso**; falhas mantêm o formulário aberto com aviso de confirmação pendente. A equipe técnica continua responsável por análise e eventual encaminhamento.

Não exige conhecimento de NRs e não instrui o membro a operar máquinas, medir ruído/calor, executar teste elétrico, acessar altura, espaço confinado ou outras zonas de risco. É uma orientação de participação preventiva, não substitui inspeção técnica.

## Segurança e limites

- Não expor chave AUDITAR_SYNC_KEY, login técnico/administrativo, dados de terceiros ou outras empresas.
- Não habilitar acesso real sem homologação da Central e validação servidor-side do escopo da sessão.
- Não coletar dados médicos, acusações pessoais nem denúncias sensíveis por esse formulário.
- A origem técnica do registro deverá guardar autoria, empresa/mandato e timestamp no backend; a UI não certifica esses campos.
- Foto e anexos não estão implementados. Se incluídos futuramente, exigirão fluxo autenticado, limites de tamanho e proteção de dados.
- Na ausência de rede, não prometer salvamento ou fila offline; o envio só é confirmado pelo servidor.
- A aba de gestão deverá receber estes registros na triagem para validação do técnico; integração de backend real não foi homologada.

## Arquivos
- `feature_sources/cipa_member_guided_inspection_v1.dart`: roteiro e formulário Flutter
- `feature_sources/cipa_member_portal_screen_v1.dart`: botão e acionamento no portal
- `feature_sources/cipa_member_guided_inspection_test_v1.dart`: testes de perguntas, validade e envio
- `.github/workflows/validate-cipa-portal-simple.yml`: workflow de validação isolada

## Antes de publicar

- [ ] Executar o CI e corrigir quaisquer falhas.
- [ ] Testar em Android pequeno, fonte ampliada, teclado e leitor de tela.
- [ ] Confirmar o tamanho máximo de relatos aceito na Central.
- [ ] Testar sessão revogada, empresas diferentes, mandatos antigos e envio duplicado.
- [ ] Testar conclusão de upload apenas após autorização e confirmação servidor.
- [ ] Testar recebimento pelo TST e histórico para o membro.
- [ ] Fazer builds e testes reais de Android; aprovação para publicação separada.
- [ ] Manter o APK do técnico/ADM separado do cliente dos membros.

## Refinamento de usabilidade e segurança — 09/11/2026

- Perguntas de todos os temas usam a mesma orientação: **Sim = situação que merece conferência**, sem representar irregularidade ou gravidade confirmada.
- Nenhuma resposta vem pré-selecionada. Para enviar, o integrante deve responder às três perguntas; **Não sei/não verifiquei** continua uma resposta válida.
- Contador e barra de progresso informam quantas perguntas faltam.
- O resumo marca quantas situações foram assinaladas e quantos itens não foram verificados, sem classificar risco ou decidir conformidade.
- Aviso preventivo aparece se uma pergunta receber **Sim**; não exige aproximação, inspeção perigosa ou correção pelo membro.
- O resumo é limitado a **1.200 caracteres** para respeitar o limite atualmente previsto pelo backend de homologação.
- O membro passa a ver **Minhas vistorias orientadas** separadas de **Outras observações**. Somente itens já autorizados da própria lista de observações entram nessas seções. O servidor atual marca o relato como **Registrada**; revisão técnica e mudança de situação **não foram implementadas nesta etapa**.
- Ao concluir o envio, uma falha posterior de atualização do painel não gera mensagem errada de falha de envio nem incentiva duplicação. Falha no envio em si mantém o formulário aberto e não anuncia sucesso.
- O guia rápido de participação passou a explicar a vistoria segura.
- Novos testes de respostas explícitas, progressão, limites, separação por membro/empresa/mandato e falha de rede foram adicionados ao workflow de Flutter.
- **Não afirmar CI aprovado ainda:** as verificações de CI, a integração real com a Central, o login e os testes em aparelho físico seguem pendentes.

## Critérios para a próxima fase

Para mostrar os estados **Recebido → Em análise → Orientação enviada → Concluído**, será preciso criar e homologar uma transição de estado com autoria, data e permissões do técnico no backend. O membro deverá consultar o estado sem poder mudá-lo. Até lá, o portal apresenta somente o status já fornecido pelo servidor, sem inventar tramitação.

Fotos deverão passar por upload autenticado, autorização de leitura, política de retenção e testes contra vazamento entre empresas; **não ativar anexos antes disso**. O módulo não salva dados offline e não pode prometer rascunho persistente em aparelho de membro.
