# CIPA — Central de acompanhamento e triagem (Android atual)

## Objetivo

Transformar registros de participação já existentes em uma fila **administrativa**
de acompanhamento para o técnico e a gestão da CIPA, sem presumir que são
não conformidades e sem alterar a situação técnica de ações ou NCs.

Este incremento não faz parte da versão Web/VPS. Não há canal de denúncias.

## Funcionalidades propostas

- **Pendências para avaliação** no topo da aba Participação, tanto no modo
  completo quanto no simplificado.
- Contagens de observações não conferidas, informações de andamento mais
  recentes aguardando análise, ações vencidas, reuniões realizadas sem ata e
  membros sem treinamento localizado.
- **Conferir situação:** registrar motivo/encaminhamento obrigatório. O evento
  `observation_review` acompanha o registro original de observação; não cria
  NC nem exclui a observação.
- **Conferir andamento:** registrar observação de gestão em
  `progress_review` vinculada ao **ID do informe específico**. Novo informe
  posterior exige nova conferência. O status da ação original não muda.
- No modo simplificado as pendências aparecem para visualização, mas o botão
  técnico de conferência fica oculto. **Isso não é controle de autorização**:
  o modo simplificado usa a mesma conta interna.

## Preservação de dados

Os eventos seguem o envelope existente `CIPA_DOCUMENTO`, com o marcador
`auditar.cipa.participation.v1`. Não há nova tabela, serviço HTTP, rota,
alteração de autenticação, sync, mídia, assinatura ou PDF.

A trilha de eventos é **operacional e compartilhada**; não permite afirmar
qual integrante individual confirmou uma análise, nem equivale a inspeção
técnica, assinatura de ata, presença ou cumprimento automático da NR-05.

## Cenários automatizados

- Revisão de observação vinculada a empresa e mandato corretos.
- Nunca aceitar revisão de outra empresa ou de outro registro.
- Informe de andamento analisado sai da fila.
- Novo informe posterior volta à fila.
- A implementação modifica somente os dois arquivos de tela CIPA e acrescenta
  fontes/testes CIPA; hashes de outras classes em lib e servidor são preservados.
- Patch não pode ser reaplicado silenciosamente.

## Pendências de homologação

- Executar a montagem completa do Android com Flutter Analyze e testes de
  regressão da CIPA e do aplicativo.
- Testar duas empresas, dois mandatos, uso offline/online, criação de
  observação, anexos, andamento e conferências em aparelho de teste.
- Conferir tela em 360/412 px e fonte ampliada.
- Verificar conflitos de conferências simultâneas em aparelhos distintos.
- Verificar prévia e histórico antes de publicar nova versão.
- **Portal individual de membros não entregue:** depende de autorização por
  empresa/mandato, revogação, auditoria e homologação do backend. Não distribuir
  credenciais de técnico/gestor/ADM para integrantes.

## Situação

Candidato em branch separada. Testes isolados passaram; sem liberação APK e
sem implantação na Central de produção.
