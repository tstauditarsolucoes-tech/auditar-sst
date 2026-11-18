# Consolidação pré-homologação Android — 18/11/2026

## Escopo conferido
A cadeia atual de PRs é **#27 → #50 → #53**. A presente etapa
reforça a segurança da instalação em ambiente de testes e a detecção
de possíveis recorrências da Visita Inteligente.

- **#27**: seletor único e fluxos de vistoria existentes.
- **#50**: indicadores de Rondas Expressas sem duplicação básica.
- **#53**: histórico e sugestões locais para empresa selecionada.
- **Esta PR**: preflight completo e restauração em caso de falha durante
  a instalação, mais regressão de descrições longas.

**Nenhuma PR desta cadeia é uma homologação do aplicativo real.**
Os testes Flutter existentes usam uma fixture isolada, com modelos
e banco simulados. Não foram gerados APK, EXE ou distribuição.

## Riscos verificados e bloqueios
1. O instalador anterior copiava arquivos e alterava a tela Quick Visit
   antes de checar a versão e todas as âncoras da Home. Agora os
   cálculos e verificações ocorrem antes das gravações; erros durante
   a escrita tentam restaurar os originais e remover novos arquivos.
   Isso **não substitui backup completo** nem protege de queda abrupta
   de energia/disco durante a gravação.
2. O instalador aceita **apenas** a base com
   `version: 3.29.200+342` e propõe `3.29.201+343`.
   Em outras versões, deve parar; não alterar a versão instalada à força.
3. A detecção de recorrências precisa usar a descrição integral, mesmo
   que o cartão mostre apenas os primeiros 180 caracteres.
4. É necessário conferir o contrato real de `Company`, `SstRecord`,
   `AppDatabase.getSstRecords`, os caminhos de importação e os
   construtores das telas antes de gerar build.
5. Os indicadores da Home ainda precisam ser comparados com os dados
   reais para garantir que Rondas não estejam já incluídas no total
   de vistorias ou nos registros de não conformidade.
6. Verificar permissões e segregação de empresas/grupos, reconexão
   offline, retorno da navegação e falha de leitura em aparelhos reais.
7. Windows, checklists, planos de ação, relatórios enviados,
   Biblioteca Técnica, CIPA e diagnóstico real de sincronização
   **não foram integrados** pela Visita Inteligente.

## Ordem segura antes da entrega
1. Revisar e concluir homologação de #27, #50 e #53 na sequência.
2. Confirmar fonte Android efetiva e fazer backup verificável.
3. Aplicar o instalador **somente em uma cópia de homologação**,
   após checar versão e contratos de modelos/banco.
4. Executar regressões isoladas, compilar Android completo e validar
   telas de navegação, Ronda, checklist e indicadores em aparelho físico
   usando empresas/dados fictícios autorizados.
5. Validar banco offline, sincronização e tratamento de dados por
   empresa/grupo. Não tratar consulta local como sincronização.
6. Avaliar inclusão gradual de checklists, planos de ação, relatórios
   e CIPA com testes específicos e sem alterar dados anteriores.
7. Avaliar adaptação Windows e somente depois preparar APK/EXE
   de homologação para aprovação expressa.

## Comandos isolados de validação
```bash
python3 -m py_compile tools/patch_android_unified_visits_v1.py tools/test_android_unified_visits_preflight_v1.py
python3 tools/test_android_unified_visits_preflight_v1.py
dart feature_sources/visit_intelligence_test_v1.dart
```

A rotina de CI executa também análise Dart e teste widget Flutter em
um projeto **fictício**; não substitui validação na instalação verdadeira.

**Regra:** não alterar dispositivos instalados, banco real, VPS, Web/Júlio
ou produção nesta etapa.
