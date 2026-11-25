# Auditar SST — Assistente guiado APR, AR, PT e PET (homologação)

## Objetivo
Na empresa selecionada, acessar:
Central de Relatórios SST > APR, PT, AR e PET > **Assistente passo a passo**.

A coleta inicial armazena atividade, setor e tipo de tarefa **por usuário e
empresa**, sem reusar dados entre contas. Uma confirmação por documento permite
reaproveitar informações, sem substituir dados já registrados.

## Implementado
1. Roteiro dividido em quatro etapas visíveis:
   - escolher atividade; identificar tarefa e setor;
   - avaliar perigos possíveis e perguntas para conferir;
   - selecionar APR, AR, PT ou PET conforme a situação.
2. Sete modelos orientativos, adaptáveis: altura, espaço confinado,
   manutenção de máquinas, soldagem/corte, escavação, eletricidade e
   inspeção de forno/equipamento quente.
3. APR/AR/PT: importação explícita de identificação para campos vazios.
   Quando não existem etapas, adicionar **sugestões não conferidas**.
   Cada sugestão é bloqueada para exportação até que o usuário a revise
   manualmente no editor e informe responsável. Nenhuma medida é
   automaticamente considerada implementada.
4. PET: importação explícita SOMENTE de atividade e local.
   **Não** transferir medições O2/LIE/tóxicos, vigia, supervisor, resgate,
   treinamento, validade ou evidências de controle.
5. PET: registros complementares de leituras atmosféricas informadas
   (data/hora, ponto, O2, inflamáveis, tóxicos, detector e responsável),
   com até 30 registros, persistência no rascunho local e detalhamento
   no PDF. Não é monitoramento em tempo real.
6. PET: alertas críticos se controles estiverem como NÃO, faltarem
   campos essenciais ou forem inválidas as leituras básicas.
7. APR/AR/PT e PET: logo Auditar quando asset disponível,
   cabeçalho, seções e aviso reiterado de **MINUTA / NÃO AUTORIZADA**.
8. Testes de modelos e armazenamento e preflight estático no CI.

## Controles que não foram implementados
- Não emitir ou aprovar PT/PET, não liberar entrada, não criar assinatura
  digital certificada, não definir vigência real, suspender, revalidar ou
  encerrar autorizações com validade legal.
- Não comunicar com detectores atmosféricos, não interpretar leituras como
  atmosfera segura e não considerar o simples preenchimento como conferência.
- Não aplicar IA de risco ou gerar nexo causal, medições e controles reais.
- Não transferir leituras ou avaliações entre PETs, pois precisam refletir
  as condições específicas do momento e do espaço.
- Não sincronizar novos rascunhos à nuvem; usa settings locais atuais.
- O logo no PDF é carregado do asset existente quando presente; fallback
  é a identificação textual Auditar.

## Protocolo de testes antes do uso
- python3 tools/test_sst_apr_pt_ar_v1.py
- python3 tools/test_sst_pet_nr33_v1.py
- python3 tools/test_sst_activity_guide_v1.py
- Em montagem homologada: flutter analyze e flutter test dos arquivos
  sst_activity_guide_test.dart, sst_risk_documents_test.dart e
  sst_pet_nr33_test.dart.
- Compilação Android/Windows e testes em dispositivos com dados fictícios:
  1. salvar plano na empresa A/usuário A;
  2. abrir APR e importar somente após confirmar;
  3. verificar bloqueio do PDF por sugestão não conferida;
  4. editar cada sugestão e informar responsável;
  5. abrir outra AR/PT e reusar apenas dados compatíveis;
  6. abrir PET e confirmar que O2, LIE, vigia, resgate etc. ficaram vazios;
  7. registrar várias leituras e verificar PDF e histórico;
  8. alternar usuário/empresa e testar isolamento;
  9. falhar salvamento e confirmar que o rascunho foi protegido.
- Revisar a metodologia P x S conforme o PGR do cliente, responsabilidades,
  LGPD e procedimento real de liberação antes de uso operacional.
- Não mesclar nem distribuir para o aplicativo instalado sem homologação,
  backup, análise NR e aprovação do responsável.

## Fontes públicas de referência
- NR-33 (MTE): https://www.gov.br/trabalho-e-emprego/pt-br/acesso-a-informacao/participacao-social/conselhos-e-orgaos-colegiados/comissao-tripartite-partitaria-permanente/normas-regulamentadora/normas-regulamentadoras-vigentes/norma-regulamentadora-no-33-nr-33
- NR-35 (MTE, atualização 2026): https://www.gov.br/trabalho-e-emprego/pt-br/acesso-a-informacao/participacao-social/conselhos-e-orgaos-colegiados/comissao-tripartite-partitaria-permanente/normas-regulamentadora/normas-regulamentadoras-vigentes/norma-regulamentadora-no-35-nr-35
