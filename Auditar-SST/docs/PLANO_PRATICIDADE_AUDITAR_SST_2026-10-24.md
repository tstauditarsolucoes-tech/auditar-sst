# Auditar SST — acabamento, praticidade e estabilidade (24/10/2026)

## Situação e salvaguardas
O usuário solicitou priorizar facilidade no campo e confiabilidade, sem ampliar o escopo indiscriminadamente.
Este trabalho permanece na branch `feature/client-panel-permissions-v329106`; PR #15 permanece DRAFT e não deve ser mesclado. Não alterar autenticação, SQLite, sincronização, mídia, Drive, IA, dados históricos, nem publicar Apps Script automaticamente. Não executar `setupAuditar()`.

## Evidências do diagnóstico
- Captura de 24/10: cabeçalho azul-escuro da tela de Evidências com texto/ícones das abas quase invisíveis, título truncado e identificação da NC quebrada em linhas excessivas.
- Inventário estático da compilação v3.29.197: 66 telas alcançáveis e nenhum import local ausente; 31 rótulos de navegação repetidos. Repetição pode corresponder a contextos legítimos: não excluir por contagem.
- Compilações anteriores Android v3.29.197 e Windows v3.30.125 concluíram com sucesso; isso não significa homologação com servidores e aparelhos reais.
- O Apps Script original foi atualizado pelo usuário; qualquer validação de tratativas/agenda/avisos deve observar permissões, isolamento por empresa e risco de escrita na planilha.

## Entrega 1 — tela Evidências e recorrências
Commit `ce2dfb2157918f5729f7e12f4a0faed9682820e1`
- `TabBar` com rótulos e indicador explicitamente claros.
- Título compacto `Evidências SST`, com descrição completa acessível via tooltip.
- Cabeçalho da NC em duas linhas, status em linha própria e opção de copiar código.
- Texto de introdução reduzido.
- Teste de regressão acrescentado a `tools/test_screenshot_ux_v1.py`.
- Alterações apenas em Flutter UI/testes; nenhum GS, sincronização, banco, login, fotos ou PDF foi editado neste commit.
- CI Android/Windows precisa concluir para novo APK/EXE.

## Próximas prioridades — critérios objetivos
1. **Visita em campo**: identificar empresa -> registrar observação/NC com foto -> salvar -> reabrir com dados intactos. Priorizar ação principal e eliminar rótulos confusos, sem excluir atalhos contextuais usados.
2. **Pendências**: destacar abertas, vencidas, correção informada e validação pelo técnico; nenhuma informação do cliente fecha NC automaticamente.
3. **PC/ADM**: gestão de técnicos e agenda em layout desktop, leitura confortável, filtros práticos; status "ativo recentemente" não significa app aberto.
4. **Relatórios**: PDF A4 legível, fotos não esticadas, códigos e normas visíveis, compartilhamento Android e exportação Windows testados com dados não sensíveis.
5. **Painel cliente**: solicitação -> resposta -> informar correção -> validar/rejeitar -> histórico consistente, com duas empresas separadas; notificações opt-in somente após homologação.
6. **Confiabilidade**: atualizar Android sem desinstalar, offline, login, sincronização e preservação de registros/fotos, com plano de reversão.

## Para aprovação
- Exigir CI Android/Windows verde e testes manuais no celular e Windows.
- Para telas visuais, conferir fontes grandes, orientação padrão e dimensões reduzidas.
- Não atribuir regressões sem reproduzir no artefato da mesma compilação.
- Testar operações que gravam apenas em ambiente isolado de homologação.
