# Investigação com IA por fotos — refinamentos de uso e segurança

## Escopo
Incremento experimental sobre PR #77 (que depende de #76 e #75).
Não há mudança na produção, no banco, sincronização, IA/backend, Google Apps
Scripts nem versões instaladas. A análise usa o serviço de fotos já existente.

## Alterações implementadas
1. **Seleção explícita de até duas fotos por análise.** Antes, as primeiras
   duas fotos eram escolhidas automaticamente. Agora o técnico seleciona cada
   imagem e consegue ver sua origem: "Evidências" ou "Condições".
2. **Consentimento renovado** ao alterar foto, empresa ou conta. A troca
   invalida a sugestão existente. Requisições em andamento com contexto antigo
   não podem apresentar sugestões no formulário atual.
3. **Perguntas de conferência em campo.** Regras simples detectam palavras
   no texto retornado pela IA e apresentam perguntas sobre máquina/esteira,
   andaime/escada/altura ou piso/vazamento. Não são detecção visual adicional
   nem prova de causa.
4. **Campo já apurado protegido.** A IA não acrescenta texto nem rebaixa o
   status de um item já validado pelo técnico. É necessário abrir o editor
   manual para revisar esse item.
5. **Anexo sem perder tempo.** O botão escolhe a primeira vaga disponível no
   campo "Evidências" (até duas fotos) ou "Condições" (até duas fotos).
6. **Roteiro de fotografia segura.** Sugere visão geral, detalhe do
   equipamento/proteção e entorno. Não orienta manipular a cena ou realizar
   atividade arriscada.

## O que permanece obrigatório
- Atendimento e segurança imediata têm prioridade.
- Descrever fatos e fontes; separar hipótese, relato, evidência e conclusão.
- Não usar imagem para afirmar culpa, nexo causal, lesão ou conformidade.
- Não enviar fotos com pessoas identificáveis ou dados de saúde. O app não
  oferece anonimização automática; a confirmação do usuário não substitui
  governança de dados pessoais, autorização, retenção e LGPD.
- Nenhuma sugestão muda o formulário sem editor e revisão; conteúdo novo
  fica "Não apurado" até conferência e seleção manual do status.
- CAT/eSocial e eventual revisão PGR não são automatizados.
- É necessário homologar Android e Windows em aparelhos de teste com fotos
  fictícias e confirmar tempos de resposta, dados/sessões, PDFs e retenção.

## Testes previstos
- python tools/test_sst_accident_investigation_guide_v1.py
- python tools/test_sst_accident_photo_ai_v1.py
- python tools/test_sst_accident_photo_ux_v1.py
- Depois da montagem integral, executar Dart format/analyze e Flutter test
  incluindo sst_accident_photo_ai_test.dart.
- Testar 0, 1, 2, 3 e 4 fotos, seleção manual, foto removida durante análise,
  mudança de usuário/empresa, perda de rede, botão Cancelar, item apurado,
  registro parcial e emissão do PDF.
