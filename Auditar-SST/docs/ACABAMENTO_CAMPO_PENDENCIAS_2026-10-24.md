# Auditar SST — Melhoria de praticidade e estabilidade

**Candidatos:** Android v3.29.198 (+340) e Windows v3.30.126 (+313).
**Branch:** feature/client-panel-permissions-v329106. **PR #15:** DRAFT, não fazer merge.

## Melhorias incluídas
- Tela Evidências SST: abas legíveis sobre cabeçalho escuro; código da NC em até duas linhas e ação Copiar.
- Tela inicial de visitas: Pendências destacado sem remover Iniciar visita, Rascunhos e Relatórios.
- Central de pendências Android e Windows: primeira prioridade da empresa em cartão clicável antes das informações da rede.
- Central de pendências Windows: filtro Somente vencidas, total visível, carregamento incremental por Mostrar mais pendências.
- Permanecem os acessos existentes à Ronda, vistoria, registro de NC, relatório, comunicação cliente e agenda.

## Proteções preservadas
Estas alterações afetam apenas telas Flutter, testes e numeração/empacotamento da release.
Não alteram: autenticação, GS publicado, SQLite, esquema de dados, sincronização, mídia/fotos, Drive, IA, serviço PDF ou dados das empresas.

## Testes automatizados
- tools/test_screenshot_ux_v1.py confere evidências, cadastro e fluxo de pendências.
- Fluxos anteriores de visita com contexto de empresa, comunicação cliente, agenda e permissões seguem com regressões.
- CI Android/Windows precisa concluir neste mesmo commit, compilando o app montado.

## Homologação prática (obrigatória antes da adoção geral)
1. Não desinstalar a versão antiga sem preservar fotos e pendências locais.
2. Atualizar pelo instalador e APK assinado compatível; conferir versão em Sobre e login.
3. Conferir empresa real em modo somente leitura; verificar registros, fotos, rascunhos, PDFs, indicadores sem gravar testes reais.
4. Na empresa de teste isolada: registrar vistoria com foto, salvar, fechar, reabrir, gerar e compartilhar PDF; validar também em janela PC estreita e maximizada.
5. Selecionar empresa e verificar cartão Prioridade imediata, pendências e navegação; no PC testar filtro de vencidas e Mostrar mais com >12 itens.
6. Conta cliente em empresa fictícia: Solicitar apoio -> resposta técnica -> Informar correção -> parecer técnico, sem encerrar NC automaticamente; verificar permissão de outra empresa negada.
7. Testar agenda e supervisão em contas ADM e técnico; último contato não significa usuário online no primeiro plano.
8. Com conexão estável, observar fila de envio com itens de teste; não apagar filas manualmente.
9. Se falhar login, sincronização, fotos ou relatório: documentar captura + registro do erro, interromper alterações e recuperar última versão estável.

**Não executar setupAuditar()** ou ativar novos triggers de e-mail para estes testes.
