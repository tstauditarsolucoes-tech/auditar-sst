# Sugestões offline — Android 3.29.175 / Windows 3.30.98

Implementação adicional ao catálogo existente, sem modelo de IA e sem consultas à rede. A identificação de equipamento e falha usa regras, sinônimos e normalização explícita; não é compreensão livre de linguagem.

## Comportamento

- 23 regras para comandos, parada de emergência, sensores de proteção, proteção de máquinas, bloqueio, andaimes, ancoragem, eletricidade, extintores, abandono e EPI.
- Equipamento e falha devem estar na mesma oração para uma correspondência de regra. Contexto segmenta a apresentação (obra, padaria, cerâmica, laticínio, oficina), sem inventar falhas.
- Diferencia botão genérico de parada de emergência; sensor genérico não confirma falha de intertravamento.
- Frases negativas, incertas e corrigidas reconhecidas não são tratadas como falha atual. A detecção de correção é conservadora: pode pedir reformulação de relatos que misturem histórico e falhas novas.
- A biblioteca anterior continua disponível como modelos semelhantes quando não há correspondência de regra. Exige revisão, sem sinalizar diagnóstico confirmado.
- Uma sugestão inicial e expansão para alternativas. A prévia permite editar título, descrição, risco, consequência, recomendação e prioridade antes de aplicar.
- Uma pergunta por regra ajuda a explicitar exposição/contexto. A prioridade é uma triagem editável, não uma matriz formal ou laudo automático. Exposição atual a algumas condições graves propõe Crítica; as demais começam em Alta e dependem de revisão.
- Aprendizado na prévia é opcional, por caixa desmarcada inicialmente e texto genérico separado. Reutiliza o serviço de aprovação já existente. Não aprende fotos nem dados de empresa automaticamente.
- A leitura abrange o caminho canônico `auditar_sst/offline_report_knowledge/offline_report_knowledge_v1.json` e o legado na raiz do suporte. Não migra nem apaga arquivos existentes. Cache é invalidado após aprovação.

## Isolamento e validação

Patch altera o widget de sugestões, adiciona o motor, testes e versão. Verifica hashes de todos os outros arquivos em lib e dos arquivos da Central presentes na aplicação reconstruída. Banco, modelos, telas, sincronização, autenticação, mídia, IA e serviço de conhecimento permanecem byte a byte iguais no patch. Não requer novo GS.

Testes cobrem exemplos positivos, negações, correções, incerteza, separação de assuntos, prioridade, biblioteca anterior, leitura legada/canônica e prévia em 360/412/1280 px, aplicação editada e cancelamento. CI executa análise, regressões e compila os dois alvos. Homologação física permanece necessária: abrir registro, testar offline, cancelar/aplicar, aprovar modelo e reabrir o app, além de conferir fluxos usuais e sincronização em ambiente de teste.

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
