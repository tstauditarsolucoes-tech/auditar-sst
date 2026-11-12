# Minha CIPA — uso fácil e leitura de orientação (11/11/2026)

**Somente código de homologação** do cliente Android individual CIPA e da gestão do Auditar SST. Não foi publicado APK, nem implantado backend ou alterada a versão Web/VPS do Júlio.

## Vistoria guiada: uma pergunta por tela
- Entrada: confirma local e tema (11 roteiros, três perguntas cada). Dados do membro, função na CIPA, empresa e mandato aparecem a partir do perfil autorizado da sessão; **não são inseridos no texto livre do relato**.
- Ao abrir uma **vistoria programada**, o tema e o local inicial aparecem preenchidos e podem ser corrigidos pelo integrante.
- O membro vê uma pergunta por vez, escolhe **Sim**, **Não** ou **Não sei/não verifiquei** em botões grandes. Nenhuma resposta é marcada antecipadamente.
- A navegação permite **Voltar**, avançar e **Conferir respostas**. Só há envio ao final; erros de conexão deixam a revisão visível. Nenhum rascunho é persistido offline.
- Perguntas mantêm foco em observações visuais seguras; **Sim** indica situação relatada, não infração confirmada. O membro não deve acessar áreas restritas ou corrigir equipamento para verificar.

## Li a orientação: somente ciência
- Devolutiva da equipe técnica pode aparecer no histórico individual de observações. O botão **Li a orientação** surge somente quando o registro tem mensagem, status `Orientação enviada` e ID de revisão atual.
- Novo endpoint `cipa_member_ack_feedback` exige sessão individual **válida**, vínculo com a observação própria, revisão atual e idempotência; revalida tudo sob lock antes da gravação.
- A ciência é guardada em planilha de homologação com usuário, empresa, mandato, integrante, relato, revisão e data. Uma orientação posterior volta a exigir confirmação de leitura.
- **Leitura não é concordância, assinatura de ata, aprovação da medida, correção do risco nem encerramento de NC.**
- A API do cliente Android está ligada ao botão de leitura em `feature_sources/cipa_member_app_main_v1.dart`. A montagem isolada agora inclui a dependência de widget do roteiro.
- Sem sessão validada o histórico fica fechado. O membro não pode confirmar leitura de outra empresa, de outro integrante ou de revisão anterior.

## Central simplificada
- A tela administrativa exibe três contagens da consulta: **Recebidos**, **Em análise** e **Orientações enviadas**. Dados completos permanecem disponíveis somente a perfis autorizados.
- As informações dependem da consulta e não devem ser anunciadas como contagem global de todas as empresas.

## Homologação necessária
- Verificar testes Node/backend, API, widget em celular pequeno e montagem real do projeto Flutter individual.
- Integrar **explicitamente** os novos arquivos de Apps Script ao backend de homologação após backup. Não trocar regras de produção sem autorização e testes em duas empresas e mandatos.
- Validar em aparelho físico, diferentes tamanhos de fonte, rede instável, sessão expirada e revisão substituída.
- O portal para membros continua pendente de autorização e entrega; não distribuir o app administrativo nem expor a chave de sincronização.
- Fotos, notificações push e rascunhos offline protegidos continuam fora desta alteração.

O fluxo pode apoiar a atuação da CIPA, mas não substitui avaliações SST, o atendimento legal à NR-05 ou a gestão efetiva do plano de ação.
