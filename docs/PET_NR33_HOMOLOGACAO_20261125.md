# Auditar SST: PET NR-33 — minuta guiada para espaços confinados

## Objetivo e limite
Adicionar a opção **PET - Permissão de Entrada e Trabalho**, distinta da
**PT genérica**, na tela Empresa > Central de Relatórios SST > APR, PT, AR e PET.

Esta é a primeira etapa: **formulário e MINUTA local de PET, não emissão
legal, autorização de entrada, assinatura certificada ou fechamento de PET**.

## Campos incluídos
- Identificação e localização do espaço confinado, objetivo da entrada;
- referência à análise dos riscos/PGR, perigos, controles, bloqueio,
  ventilação e condições específicas antes da entrada;
- nomes e funções de supervisores, vigias e trabalhadores autorizados,
  equipe de resgate;
- datas/horários PROPOSTOS de emissão e término;
- avaliação inicial da atmosfera: O2 (%), inflamáveis (% LIE), gases/vapores
  tóxicos por nome, valor e unidade; outros agentes; hora, quem mediu,
  equipamento e situação de calibração/testes;
- monitoramento atmosférico contínuo, plano e equipamentos de resgate,
  comunicação, EPIs/EPCs, treinamentos e aptidão;
- plano de encerramento e pendências;
- 11 itens de conferência com estado NÃO VERIFICADO / SIM INFORMADO /
  NÃO / N/A JUSTIFICADO, nunca “liberado”.

A tela orienta o técnico a usar medições reais feitas com supervisor fora
do espaço, imediatamente antes da entrada, e a não interpretar uma leitura
isolada como prova de segurança. O2 e LIE são apenas números informados, sem
classificação automatizada de atmosferas seguras.

## Persistência e geração de PDF
Rascunho por conta+empresa, utilizando apenas settings locais existentes,
sem migrar banco nem alterar Apps Scripts. Histórico de minutas arquivadas
é separado, não representa o arquivo legal de PET emitida.
O PDF A4 sempre contém **MINUTA NÃO AUTORIZADA / ENTRADA PROIBIDA**,
sem campos que simulem assinatura ou autorização efetuada.
Uma minuta com resposta “NÃO” pode ser exportada como registro para
conferência, **jamais como permissão de entrada válida**.

## NR-33, dispositivos que precisam ser verificados para produção
- 33.5.5–33.5.7: emissão ANTES da entrada, dados mínimos, assinaturas
  de supervisores e vigias, meio físico/digital e certificação;
- 33.5.8–33.5.12: rastreabilidade, arquivamento por 5 anos da PET
  EMITIDA, acesso pelos trabalhadores, validade/encerramento e condições
  estritas para prorrogação;
- 33.5.15: avaliação inicial imediata, monitoramento contínuo e aparelhos;
- 33.5.20: plano e equipe de resgate;
- 33.5.21.5 e Anexo II: adaptar o modelo de PET aos espaços da empresa.
Na produção, exigir também a definição do fluxo de certificação de
assinaturas, acesso permanente pelo vigia, plano de retirada, controle de
alterações, vencimento e encerramento, e retenção obrigatória.

## Plano de testes e bloqueios
1. Preflight: python3 tools/test_sst_pet_nr33_v1.py
2. Regressão: python3 tools/test_sst_apr_pt_ar_v1.py
3. Flutter test: test/sst_pet_nr33_test.dart (após montagem do app)
4. Flutter analyze e build Android/Windows em cópias de homologação.
5. Campo com vírgula decimal, leituras ausentes/inválidas e N/A sem
   justificativa devem bloquear PDF de revisão.
6. Validar troca de empresa/usuário, modo offline, rascunho, histórico,
   múltiplas páginas PDF e erros de salvamento; dados fictícios apenas.
7. Nunca validar um botão de “autorizar entrada” neste protótipo.
8. Sem merge, instalação, ativação ou alteração do app instalado antes de
   CI completo, revisão SST/jurídica, backup e homologação em dispositivos.

Fonte técnica principal:
https://www.gov.br/trabalho-e-emprego/pt-br/acesso-a-informacao/participacao-social/conselhos-e-orgaos-colegiados/comissao-tripartite-partitaria-permanente/arquivos/normas-regulamentadoras/nr-33-atualizada-2022-_retificada.pdf
