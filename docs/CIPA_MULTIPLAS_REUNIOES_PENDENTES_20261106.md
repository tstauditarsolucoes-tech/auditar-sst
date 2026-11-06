# CIPA — refinamento de múltiplas reuniões pendentes

## Problema
O cartão de reunião assistida focava uma reunião e podia deixar menos evidentes outras reuniões realizadas sem ata vinculada ou ainda agendadas com data passada no mesmo mandato.

## Mudança
A regra de orientação local passa a incluir, quando existem pelo menos duas pendências, uma linha **Conferir N reuniões pendentes** com dois totais: realizadas sem ata vinculada e agendamentos com data passada. O atalho abre a lista já existente de reuniões e não edita nenhum dado sem ação explícita.

## Segurança
Sem presunção de irregularidade normativa: o alerta apenas informa que registros precisam de conferência. Não marca presença, assinatura, reunião realizada ou ação concluída; não muda autenticação, backend, sincronização ou projeto Web. Continua exigida a seleção por empresa e mandato feita pela tela da gestão atual.

Dois cenários adicionais no teste de regras: 3 pendências simultâneas e apenas 1 pendência sem alerta duplicado. **Testes e montagem completa em Android e Windows ainda precisam ser executados.**

Dependência: PR #36, em homologação. Nenhum APK/EXE publicado.