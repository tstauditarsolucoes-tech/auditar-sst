# Auditar SST — Central de Relatórios SST (6 modelos) | Homologação

**Data:** 06/11/2026

## Objetivo

Criar **uma única central de relatórios dentro do cadastro da empresa**, sem
substituir a Ronda Expressa, a Vistoria ou os quatro relatórios gerenciais já
existentes. A navegação reúne seis tipos de relatório e atalhos para os dois
fluxos de inspeção que a equipe já utiliza.

## Modelos implementados

| Modelo | Itens | Observações |
|---|---:|---|
| Máquinas e equipamentos (referência NR-12) | 10 | Proteções, paradas, sensores, energias, limpeza e operação |
| Obras e canteiros (referência NR-18) | 10 | Guarda-corpos, andaimes, escadas, aberturas, elétrica e organização |
| Inspeção visual elétrica (referência NR-10) | 10 | Somente observações e documentação, sem medir aterramento ou emitir laudo |
| Trabalho em altura (referência NR-35) | 9 | Planejamento, proteção coletiva/individual, ancoragem e resposta a emergências |
| Investigação de acidente/incidente | 9 | Cronologia, fatos, fontes, hipóteses separadas de fatos e medidas preventivas |
| Relatório gerencial mensal | Reuso | Abre o gerencial existente em `ManagerReportKind.monthly`, lendo dados da empresa |

**Total dos novos roteiros de campo:** 48 questões. O relatório mensal não
duplica banco de dados, extração ou gerador gerencial.

## Fluxo no campo

1. Selecionar empresa → **Central de Relatórios SST**.
2. Selecionar um dos cinco roteiros ou o gerencial mensal.
3. Registrar local, atividade/equipamento, técnico e data. Na investigação,
   preencher também data/hora informadas e narrativa factual do evento.
4. Marcar **Não verificado**, **Conforme**, **Não conforme** ou **Não se aplica**;
   para investigação, **Não apurado**, **Apurado/registrado** ou **Não se aplica**.
5. Registrar observação com suas palavras; opcionalmente consultar uma
   recomendação da **biblioteca offline**, com revisão e confirmação antes
   de utilizar (não é preenchida automaticamente).
6. Anexar até duas fotos por item; imagens são copiadas para armazenamento
   local privado do dispositivo e NÃO são transmitidas para a Central.
7. Assinar opcionalmente com o dedo ou mouse; a assinatura só entra no
   documento quando gravada.
8. Gerar PDF **offline** com identificação, resumo, situações descritas,
   recomendação revisada, fotos e assinatura, sem presumir fatos não levantados.

O rascunho do modelo é gravado de maneira independente por empresa,
tipo e usuário no mecanismo de settings local já existente. Escritas são
serializadas para impedir que toques rápidos descartem texto anterior.

## Regras para impedir relatório fictício

- Todos os itens começam **não verificados**.
- Não conforme exige observação factual de pelo menos oito caracteres.
- Informações apuradas de acidente exigem observação factual e narrativa
  de ocorrência com data/hora informada.
- Não há PDF se faltarem identificação do técnico, data ou algum item
  examinado.
- Se ainda houver temas não verificados, o PDF é identificado como
  **RASCUNHO PARCIAL**.
- O PDF nunca certifica testes elétricos, medições, eficácia de sistemas,
  conformidade legal definitiva, CAT ou perícia.
- Referências NR são temáticas, exigindo avaliação da redação vigente.
- A assinatura não transforma o roteiro em laudo de habilitação profissional.
- Ações e observações destes roteiros **não criam NC oficial automaticamente**;
  use o fluxo de Vistoria/Ronda para abrir não conformidades e planos de ação
  vinculados ao banco SST.

## Arquitetura e proteção

- `feature_sources/sst_report_center_models_v1.dart`: dados puros, 5 modelos,
  controle de estados, validação e serialização de rascunhos com empresa e tipo.
- `feature_sources/sst_report_center_screen_v1.dart`: central + formulários
  com rascunho local, fotografias, assinatura e acesso à biblioteca de sugestões.
- `feature_sources/sst_report_center_pdf_v1.dart`: PDF baseado somente em
  itens registrados e fotos locais existentes.
- `tools/patch_sst_report_center_v1.py`: instalador aditivo, altera somente
  a tela do cadastro da empresa e o padrão inicial do gerencial, copia novos
  arquivos, verifica SHA-256 dos arquivos fora do escopo e bloqueia duplicação.
- `feature_sources/sst_report_center_models_test_v1.dart`: testes
  de quantidade, vínculo por empresa/tipo e validação de fatos.
- `tools/stage_sst_report_center_fixture_v1.py`: compila os componentes
  reais em um app Flutter de testes, usando stubs apenas para serviços externos.
- `.github/workflows/validate-sst-report-center-v1.yml`: testes dos
  seis tipos, UI e geração de PDF offline, sem acessar serviços reais.

O projeto **não modifica** `database.dart`, `models.dart`,
`auth_service.dart`, `device_sync_service.dart`, `Code.gs`,
`MultiUser.gs`, `media_sync_service.dart` ou PDFs antigos. Nenhuma
instalação foi realizada na versão em produção.

## Limitações desta primeira entrega

- Os rascunhos dos novos roteiros são **locais** e não sincronizam entre
  dispositivos; não foram integrados ao histórico oficial de inspeções.
- Cada empresa/modelo/usuário possui um rascunho de trabalho; fluxo de
  múltiplas visitas arquivadas, exportação automática ao histórico e
  identificação sequencial devem ser homologados antes do uso recorrente.
- O relatório mensal usa o gerador gerencial existente e depende dos
  registros locais já sincronizados; não deve ser interpretado como relatório
  de situação atual da nuvem sem atualização.
- A assinatura manuscrita é uma imagem opcional, não uma assinatura digital
  certificada por autoridade.
- A abertura do PDF utiliza o mecanismo de impressão/compartilhamento do
  sistema operacional e precisa ser testada em Android e Windows reais.
- **Exige compilação Android e Windows completas e homologação** com a
  base da Auditar antes de liberar aos usuários.

Fontes oficiais para conferência normativa:
[Normas Regulamentadoras vigentes — MTE](https://www.gov.br/trabalho-e-emprego/pt-br/acesso-a-informacao/participacao-social/conselhos-e-orgaos-colegiados/comissao-tripartite-partitaria-permanente/normas-regulamentadora/normas-regulamentadoras-vigentes).
