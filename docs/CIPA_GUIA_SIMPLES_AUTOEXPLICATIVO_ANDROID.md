# CIPA fácil — fluxo guiado da versão Android atual

Este roteiro é um incremento **de interface** para a gestão já existente do
Auditar SST em Flutter. Não envolve o sistema Web/VPS, não implementa canal de
denúncias, e não cria conta individual de integrante da CIPA.

## Como deve funcionar no Android

1. Entrar no app com a conta interna já autorizada, escolher empresa e abrir
   **CIPA → Painel**.
2. No cartão **Sua CIPA, passo a passo**, ler o próximo passo recomendado.
   O botão principal abre o cadastro existente correspondente. Não é um novo
   formulário nem um procedimento automático que dispensa a conferência.
3. Abrir **Ver todas as 8 etapas** para percorrer mandato, processo eleitoral
   se aplicável, integrantes, treinamento, reuniões, atas, ações e documentos.
4. O ícone de ajuda explica o significado de cada etapa, a informação já
   cadastrada e o que não pode ser concluído automaticamente.
5. Utilizar os atalhos **Preparar reunião**, **Registrar situação** e **Nova
   ação** para a rotina, depois conferir dados e evidências.
6. Para relatos e informações recebidas pela CIPA, usar **Participação →
   Pendências para avaliação**. A conferência administrativa não encerra NC.

## O que o sistema ajuda a não esquecer

- Verifica se há mandato ativo e membros cadastrados.
- Alerta quando não localiza comprovantes de treinamento para membros
  vinculados; ausência no app não prova falta de capacitação.
- Sugere confirmar realização de reunião cuja data passou, mas que continua
  registrada como "Agendada". Não cria outra reunião para ocultar a pendência.
- Destaca reunião realizada que não possui ata vinculada, mas não presume
  que a ata foi assinada ou que todos compareceram.
- Destaca ações com prazo vencido e pedidos de acompanhamento.
- Mostra a existência de documentação marcada como pendente, sem presumir
  quais documentos são legalmente exigíveis para cada estabelecimento.

## Proteção dos registros

- **Nenhuma mudança** nos formulários originais de eleição, mandato, membro,
  reunião, ata, plano de ação, treinamento, documentos ou relatórios.
- Não altera as tabelas locais, IDs, autenticação, sincronização, Drive,
  armazenamento de fotos, assinaturas, IA ou Apps Script.
- Os indicadores significam **dados encontrados ou pontos para conferir**:
  não substituem dimensionamento, avaliação da NR-05 nem certificação legal.
- Não presumir eleição obrigatória de empresa que tem modelo de representação
  diverso, nem usar registros de mandato anterior como prova de mandato atual.
- O modo simplificado de participação não equivale a um portal individual.
  **Não compartilhar credenciais técnicas ou de ADM com membros da CIPA.**

## Validação antes de liberar APK

- Os testes puros Dart do guia verificam 8 etapas, prioridades e exceções.
- O teste Python garante que o instalador altera exclusivamente a interface
  CIPA e impede reinstalação silenciosa.
- A montagem completa do Android ainda deve passar por `flutter analyze`,
  testes de widgets e navegação com 360/412 px e fonte ampliada.
- Homologar uma empresa com CIPA completa e outra sem CIPA constituída:
  conferir enquadramento, eleição/designado e dados por mandato.
- Testar reuniões agendadas passadas, realizadas, canceladas; atas com e sem
  assinatura; arquivos; sincronização offline/online; histórico intacto.
- Só depois de validar, compilar APK com a **mesma chave de assinatura** e
  confirmar backup antes de atualizar aparelhos em produção.

**Situação:** branch de homologação; NÃO instalada ou publicada.
