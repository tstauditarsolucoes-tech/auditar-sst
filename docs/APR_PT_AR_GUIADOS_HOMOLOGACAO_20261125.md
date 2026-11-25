# Auditar SST — APR, PT e AR guiados (homologação)

## Significado das siglas confirmado pelo usuário
- APR: Análise Preliminar de Riscos
- PT: Permissão de Trabalho
- AR: Análise de Risco

Não criar PRE. PET para espaços confinados deve seguir especificamente NR-33;
a PT genérica aqui NÃO substitui PET.

## Onde abrir
Empresa > Central de Relatórios SST > APR, PT e AR guiados

## O que esta PR implementa
1. Três tipos de rascunho independentes, com tela de seleção simples.
2. Dados gerais: atividade, local, data, elaborador, condições impeditivas,
   emergência e resgate.
3. Lista de até 50 etapas/perigos: etapa, perigo, consequência, controles,
   responsável proposto e P x S ilustrativo de 1 a 5.
4. APR e AR são registros de análise de riscos; não emitem autorização.
5. PT exige ainda equipe, validade PROPOSTA, pessoa a consultar para aprovação
   e vínculo informado à AR/APR, mas **permanece minuta não autorizada**.
6. PDFs multipágina com aviso de MINUTA e NÃO AUTORIZA INÍCIO DE TRABALHO.
   Não existe assinatura/autoridade real, validade verificada ou encerramento
   de PT nesta primeira etapa. A emissão de PDF não libera atividade.
7. Rascunhos em settings locais já existentes, separados por conta, empresa
   e tipo. Versões arquivadas são preservadas; não reescrever versão anterior.
8. Retentativa visível se o salvamento falhar; impedir saída silenciosa com
   dados pendentes; confirmação para arquivar e iniciar outro rascunho.
9. Apenas arquivos novos no patch de homologação da Central de Relatórios.
   Sem alterar DB, sincronização, login, IA, Apps Script ou aplicativo instalado.
10. Testes Dart do modelo/isolamento e preflight Python sem dados reais.

## Atenção a limites
- PT real depende de verificação em campo, autorização do responsável definido
  pela organização, vigência, registros, revalidação e encerramento conforme
  natureza da atividade e NR pertinente. Nesta entrega: apenas minuta.
- A matriz P x S é ilustrativa, NÃO a metodologia de risco aprovada do PGR;
  deve ser adaptada antes de uso operacional.
- APR/AR não demonstram conformidade normativa só por gerar PDF.
- Validação de autenticação, persistência SQLite, retenção e segregação de
  usuários é necessária antes de operar com dados reais.
- Offline funciona apenas na medida em que o armazenamento local existente
  esteja homologado; não há sincronização automática deste novo módulo.
- Não foram implementadas assinaturas digitais, fotos, parecer IA específico,
  PT autorizada, aprovação remota, reutilização de dados do PGR nem PET.

## Homologação necessária
- Rodar python3 tools/test_sst_apr_pt_ar_v1.py.
- Montar cópias do app pelos scripts existentes, Dart format/analyze/test.
- Executar test/sst_risk_documents_test.dart nos dois ambientes.
- Simular: rascunho incompleto, não salvar, troca de conta/empresa, falha
  durante arquivamento, histórico e geração do PDF multipágina.
- Conferir layout do PDF, textos longos, A4 e impressão Android/Windows.
- Testar PT nunca apresentando estado de autorização válida.
- Testar em dispositivos físicos com empresas/dados fictícios, fazer backup
  e aprovar expressamente antes de qualquer instalação ou merge.

## Contexto normativo
Consultar a redação vigente da NR-01 (GRO), NR-35 (análise de risco e PT para
situações aplicáveis) e NR-33 (PET obrigatória para espaços confinados).
