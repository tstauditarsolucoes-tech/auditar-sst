# Visita Inteligente Auditar — etapa de homologação

## Objetivo
Preparar a visita de campo com base nas **Rondas Expressas salvas localmente** para a empresa selecionada. Não é uma nova aplicação, não modifica o banco e não envia informação à Central.

## Como funciona
1. O técnico escolhe uma empresa pelo fluxo já existente e abre **Iniciar vistoria**.
2. Seleciona **Preparar Visita Inteligente**. Sem empresa escolhida, o atalho não aparece.
3. A tela consulta os registros `OBSERVACAO_SEGURANCA` locais e exibe três indicadores:
   - Rondas locais com `roundId` distinto;
   - Observações classificadas como NC/risco/condição ou ato inseguro e ainda não explicitamente corrigidas;
   - Possíveis repetições: setor e descrição similares em pelo menos duas rondas distintas.
4. Mostra até cinco observações para conferência e os botões **Fazer nova ronda** e **Fazer checklist completo**, mantendo as telas originais.
5. Ao voltar de uma vistoria, recarrega o resumo local. Um erro de leitura não é apresentado como zero ocorrências.

## Controles
- O cálculo recebe somente a empresa selecionada; filtra registros antes de gerar indicadores. Não combina dados de empresas diferentes.
- Deduplicação por ID de registro e por ID de ronda.
- Recorrências são **hipóteses** que o TST precisa verificar, jamais constatação automática de persistência de risco.
- Uma vistoria marcada como **Concluída** não encerra uma NC; apenas estados explícitos de correção/validação deixam de contá-la como aberta.
- Sem dados, a interface deixa claro que isso **não comprova ausência de riscos**.
- **Diagnóstico local:** a tela mostra se a consulta de dados do aparelho funcionou, mas não afirma que houve sincronização com servidor ou sucesso de envio.
- Não importa todo o histórico: **somente Rondas Expressas locais**. Checklists, plano de ação, CIPA, treinamentos e arquivos da nuvem dependem de integração e testes posteriores.
- Não muda permissões, PDFs, assinatura, Apps Script, fotos, política de sincronização ou o projeto Web.

## Homologação pendente
- Integrar à versão real Android e verificar a compatibilidade das estruturas `Company`, `SstRecord` e `AppDatabase` com a versão instalada.
- Verificar o comportamento no Windows (a integração atual foi preparada sobre o seletor Android).
- Comparar contagens e registros com dados fictícios e autorizados em múltiplas empresas e rondas.
- Conferir consulta rápida, tratamento de falhas, mudança de empresa, tamanho de fonte e navegação em aparelho real.
- Fazer backup, revisar as PRs dependentes e apenas depois preparar builds de homologação.

## Arquivos
- `feature_sources/visit_intelligence_v1.dart`: regras puras e escopo.
- `feature_sources/smart_visit_briefing_screen_v1.dart`: consulta e interface.
- `feature_sources/android_visit_type_chooser_v1.dart`: atalho.
- `tools/patch_android_unified_visits_v1.py`: cópia/instalação somente em ambiente de homologação.
- Testes puros e widget Flutter em `validate-android-unified-visits.yml`.

**Não integrado ao app instalado; não é APK nem EXE pronto.**