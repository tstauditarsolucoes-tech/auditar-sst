# Auditar SST - Assistente IA de Investigação: análise de fotos (homologação)

## Entrada
Empresa > Central de Relatórios SST > Investigação guiada de acidente/incidente
> Analisar fotos do acidente com IA.

Depende das PRs #75 (estabilização) e #76 (investigação guiada).
Este trabalho é **somente branch experimental**. Não há atualização instalada,
merge, ativação do backend ou serviço novo.

## O que foi desenvolvido
1. Reutiliza fotografias anexadas ao formulário nos campos
   incident-03 (evidências) e incident-04 (condições), até 2 imagens por envio.
2. Permite anexar fotos pela galeria e câmera Android; galeria no Windows.
3. Exige confirmação de privacidade e, em seguida, confirmação adicional de
   envio ao serviço de IA que o Auditar SST já utiliza. Nada é transmitido
   por mera seleção da foto.
4. Usa o fluxo de análise fotográfica **geral** que já existe no app,
   sem alterar IA, transporte, chave, autenticação, sync, banco ou Apps Script.
5. Exibe descrição visual, perigo/consequência hipotéticos e medidas propostas.
   A saída depende do formato realmente devolvido pelo serviço existente.
6. Botões encaminham sugestões para revisão manual do técnico:
   - incident-03: evidências e descrição da foto;
   - incident-04: condições do local;
   - incident-08: medidas preventivas;
   Nunca escreve nos campos sem revisão. Campo fica **NÃO APURADO** até uma
   nova ação do técnico. As hipóteses NÃO preenchem incident-07 automaticamente.
7. Salva rascunho usando o fluxo que já existia na Central de Relatórios.
   Análise bruta não é salva separadamente e não vira PDF por si só.
8. Mantém limite de tamanho e texto; descarta resposta sem leitura visual.

## Privacidade
- Não enviar fotos de pessoas identificáveis, ferimentos, documento pessoal
  ou prontuário; o app pede confirmação humana, não oferece desfoque automático.
- O serviço atual recebe imagens e nome da empresa; depende de internet.
  Verificar termos, retenção e acesso do fornecedor antes da homologação.
- Fotos selecionadas permanecem no armazenamento local já existente, sujeito
  à revisão de segurança/LGPD; não há criptografia nova neste PR.
- Confirmar isolamento de conta/empresa, inclusive quando muda o usuário
  enquanto a requisição está em andamento.
- Falha de rede, imagem ausente ou resposta vazia não altera o relatório.

## Limitações
- O backend atual foi criado para observações de SST, não especificamente
  para acidentes. Portanto **não há motor novo de investigação com IA**:
  os resultados são leitura visual genérica e requerem conferência humana.
- Não há classificação automática de causa raiz, correlação causal, análise
  formal de cinco porquês, anonimização por imagem, antes/depois ou CAT.
- Nem NR, nem culpa, nem nexo, nem falha de treinamento podem ser inferidos
  somente da fotografia.
- Ainda precisa de integração completa, flutter analyze/test e teste em
  Android e Windows com dados fictícios antes de qualquer distribuição.

## Homologação
- Rodar python tools/test_sst_accident_investigation_guide_v1.py
- Rodar python tools/test_sst_accident_photo_ai_v1.py
- Testar o DTO com flutter test test/sst_accident_photo_ai_test.dart,
  depois de montar o aplicativo de homologação.
- Verificar os fluxos: foto ausente, câmera negada, duas fotos, privacidade
  desmarcada, cancelar confirmação, resposta vazia, timeout, mudança de
  empresa/conta, revisão, salvamento, PDF e histórico.
- Testar somente com imagens fictícias sem pessoas.
- Verificar que nenhum campo é marcado como apurado automaticamente.
- Revalidar SHA, proteção do banco, sincronização, login e Apps Scripts.
