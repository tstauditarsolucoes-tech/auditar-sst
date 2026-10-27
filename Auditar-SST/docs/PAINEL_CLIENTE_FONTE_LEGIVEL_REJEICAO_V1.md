# Auditar SST | Painel do Cliente — candidato de homologação (26/10/2026)

## Alterações visuais
- Fonte-base confortável, cartões e campos ampliados, quebra de linhas e controles A−/A+.
- Identificação de NC por título ou descrição existente; código oficial sempre disponível.
- Orientação técnica não publicada é mostrada como pendente, sem inventar NR.

## Evidências
- O cliente envia descrição/foto, recebe protocolo, acompanha situação.
- O técnico visualiza a evidência e precisa informar justificativa (mínimo 8 caracteres) ao rejeitar.
- O cliente autorizado vê o motivo e sabe que precisa complementar.
- Aprovar evidência **não conclui nem encerra NC**.

## Estrutura técnica
- `ClientPortal.html`: ajustes de interface.
- `ClientPortal.gs`: retorna motivo, valida a rejeição e grava em planilha **aditiva** `ClientPortalEvidenceReviewReasonsV1`.
- A planilha histórica de evidências preserva suas dez colunas.
- Nenhuma troca de login, contas, banco, Drive, sincronização ou mídia.

## Instalação segura — NÃO publicada
1. Fazer backup integral dos GS e HTML atuais da Central Online.
2. Comparar o `ClientPortal.gs` candidato com a versão ativa: **não sobrescrever sem reconciliar diferenças**, inclusive patches e integrações atuais.
3. Homologar com um cliente de teste e conta TST da mesma empresa; repetir com outra empresa para verificar isolamento.
4. Enviar evidência, rejeitar com motivo, consultar histórico e conferir que NC permaneceu aberta.
5. Verificar a legibilidade em computador e celular, inclusive A−/A+ e impressão de plano.
6. Publicar nova versão só depois de homologação e autorização explícita.

## Estado
Alteração de desenvolvimento, não instalação em produção.
O PR #15 deve permanecer DRAFT, sem merge.
Não executar setupAuditar().
