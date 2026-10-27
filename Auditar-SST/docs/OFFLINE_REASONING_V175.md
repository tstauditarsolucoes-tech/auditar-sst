# Sugestões offline — Android 3.29.176 / Windows 3.30.99

Implementação adicional ao catálogo existente, sem modelo de IA e sem consultas à rede. A identificação de equipamento e falha usa regras, sinônimos e normalização explícita; não é compreensão livre de linguagem.

## Comportamento

- 23 regras para comandos, parada de emergência, sensores de proteção, proteção de máquinas, bloqueio, andaimes, ancoragem, eletricidade, extintores, abandono e EPI.
- Equipamento e falha devem estar na mesma oração para uma correspondência de regra. Contexto segmenta a apresentação (obra, padaria, cerâmica, laticínio, oficina), sem inventar falhas.
- Diferencia botão genérico de parada de emergência; sensor genérico não confirma falha de intertravamento.
- Frases negativas, incertas e corrigidas reconhecidas não são tratadas como falha atual. A detecção de correção é conservadora: pode pedir reformulação de relatos que misturem histórico e falhas novas.
- A biblioteca anterior continua disponível como modelos semelhantes quando não há correspondência de regra. Exige revisão, sem sinalizar diagnóstico confirmado.
- Uma sugestão inicial e expansão para alternativas. A prévia permite editar título, descrição, risco, consequência, recomendação e prioridade antes de aplicar.
- Uma pergunta por regra ajuda a explicitar exposição/contexto. A prioridade é uma triagem editável, não uma matriz formal ou laudo automático. Exposição atual a algumas condições graves propõe Crítica; as demais começam em Alta e dependem de revisão.
- Aprendizado automático quando o técnico aplica o texto revisado, sem pergunta ou caixa de salvar. Um arquivo local complementar guarda descrição genérica da regra/modelo e as correções técnicas, sem copiar o texto da observação atual. Digitar ou cancelar não gera aprendizado. Modelos aprendidos têm preferência na próxima busca compatível; falha de gravação não impede aplicar o registro.
- A leitura abrange o caminho canônico `auditar_sst/offline_report_knowledge/offline_report_knowledge_v1.json` e o legado na raiz do suporte. O aprendizado automático fica em `offline_reasoning_learning_v1.json`, separado da biblioteca anterior, com até 500 modelos recentes e escrita serializada. Não migra nem apaga arquivos existentes. Cache é invalidado após aprovação.

## Isolamento e validação

Patch altera o widget de sugestões, ajusta a aplicação explícita dos campos revisados na Vistoria e Ronda e adiciona o motor, testes e versão. Verifica hashes de todos os arquivos de lib fora do widget e das duas telas de integração e dos arquivos da Central presentes na aplicação reconstruída. Banco, modelos, demais telas, sincronização, autenticação, mídia, IA e serviço de conhecimento permanecem byte a byte iguais no patch. Não requer novo GS.

Testes cobrem exemplos positivos, negações, correções, incerteza, separação de assuntos, prioridade, biblioteca anterior, leitura legada/canônica e prévia em 360/412/1280 px, aplicação editada e cancelamento. CI executa análise, regressões e compila os dois alvos. Homologação física permanece necessária: abrir registro, testar offline, cancelar/aplicar, aplicar texto revisado e reabrir o app para conferir o aprendizado automático, além de conferir fluxos usuais e sincronização em ambiente de teste.

## Referências temáticas

As regras mostram temas normativos para conferência pelo técnico, sem afirmar enquadramento em subitem ou conformidade automática. EPI depende da avaliação do perigo e da atividade; luvas junto a partes rotativas exigem avaliação específica. Incêndio depende também das exigências estaduais e do projeto. Prioridade e recomendações precisam de validação profissional no local.

Páginas oficiais consultadas em 08/10/2026:
- NR-6: https://www.gov.br/trabalho-e-emprego/pt-br/acesso-a-informacao/participacao-social/conselhos-e-orgaos-colegiados/comissao-tripartite-partitaria-permanente/normas-regulamentadora/normas-regulamentadoras-vigentes/norma-regulamentadora-no-6-nr-6
- NR-10: https://www.gov.br/trabalho-e-emprego/pt-br/acesso-a-informacao/participacao-social/conselhos-e-orgaos-colegiados/comissao-tripartite-partitaria-permanente/normas-regulamentadora/normas-regulamentadoras-vigentes/norma-regulamentadora-no-10-nr-10
- NR-12: https://www.gov.br/trabalho-e-emprego/pt-br/acesso-a-informacao/participacao-social/conselhos-e-orgaos-colegiados/comissao-tripartite-partitaria-permanente/normas-regulamentadora/normas-regulamentadoras-vigentes/norma-regulamentadora-no-12-nr-12
- NR-18: https://www.gov.br/trabalho-e-emprego/pt-br/acesso-a-informacao/participacao-social/conselhos-e-orgaos-colegiados/comissao-tripartite-partitaria-permanente/normas-regulamentadora/normas-regulamentadoras-vigentes/norma-regulamentadora-no-18-nr-18
- NR-23: https://www.gov.br/trabalho-e-emprego/pt-br/acesso-a-informacao/participacao-social/conselhos-e-orgaos-colegiados/comissao-tripartite-partitaria-permanente/normas-regulamentadora/normas-regulamentadoras-vigentes/norma-regulamentadora-no-23-nr-23
- NR-35: https://www.gov.br/trabalho-e-emprego/pt-br/acesso-a-informacao/participacao-social/conselhos-e-orgaos-colegiados/comissao-tripartite-partitaria-permanente/normas-regulamentadora/normas-regulamentadoras-vigentes/norma-regulamentadora-no-35-nr-35

Esta versão amplia regras locais e reaproveitamento de modelos. Não interpreta qualquer texto, imagem ou norma como uma IA; temas não cobertos continuam dependentes de revisão manual ou dos recursos de IA já existentes.


## Refinamento da interface (3.29.176 / 3.30.99)

- Uma sugestão principal com prévia de até duas linhas; estado "Correspondência forte" somente com equipamento e falha reconhecidos pela regra local.
- "Aplicar" aceita os fatos atuais sem abrir diálogo; "Ajustar" mantém a revisão completa; "Outras opções" expande os demais modelos.
- Sem falha identificada em extintor, botoeira, sensor ou andaime, o sistema solicita mais detalhes em vez de preencher uma NC pela presença de um nome.
- Não aprende pela digitação ou ao cancelar. Aprende automaticamente ao aplicar uma sugestão, sem interromper o registro enquanto grava localmente.
- Para modelos sem regra forte, a revisão é necessária antes de aplicar. Descrições reutilizáveis sem regra guardam o título genérico, não o texto da empresa/obra.
- Corrige condição de teste na qual aguardar a gravação antes de fechar o diálogo podia deixar o registro sem aplicação. A gravação local assíncrona deve ser conferida em teste físico.

## Checklist de aceitação (teste físico)

- No Android 360/412 px e no Windows, confirmar visualização de somente uma sugestão principal, duas linhas e ações que não ultrapassem a tela.
- Diferenciar extintor obstruído, desobstruído e sem sinalização; sem estado observável, pedir detalhes.
- Com o aparelho sem internet, aplicar uma sugestão e editar outra; reabrir e conferir reaproveitamento local.
- Confirmar que cancelar não cria modelo e que o sistema não modifica a descrição dos fatos informados.
- Verificar que modelos não são compartilhados entre aparelhos sem atualização específica de sincronização.
