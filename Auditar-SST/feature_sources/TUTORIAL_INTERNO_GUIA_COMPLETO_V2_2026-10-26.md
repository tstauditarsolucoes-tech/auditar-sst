# HOMOLOGAÇÃO DO TUTORIAL INTERNO V2 — 26/10/2026

## Funcionalidade implementada no código
- Tela inicial: ícone "Guia de uso" abre central interna pesquisável.
- Configurações > Ajuda e mini tutorial > Abrir guia completo do app.
- 31 assuntos organizados em cinco grupos; exemplos práticos e instruções numeradas.
- Botão "Novidades do app" aborda recursos recentes e ressalta dependências de Central/perfil.
- Dicas revisadas reaparecem uma vez por conta na versão 2; usuário pode desativar e reiniciar.
- Pop-ups com altura limitada e rolagem para aparelhos pequenos.

## Verificações obrigatórias
1. Compilar o mesmo commit em Android e Windows.
2. Android: entrar na Home, tocar "Guia de uso", pesquisar NC, fotos, PDF, offline, cliente e agenda.
3. Abrir um tema, navegar pelas três etapas, fechar e retornar à busca, sem recorte inferior.
4. Em Configurações, abrir o guia e executar Reiniciar mini tutorial em conta de teste.
5. Testar modo paisagem, teclado aberto e janela Windows estreita/maximizada.
6. Confirmar que textos de títulos amigáveis de NC não afirmam função homologada.
7. Confirmar que tratativas e painel cliente apresentam dependência das permissões da Central Online.
8. Conferir login, banco, fotos, sincronização, PDF e fila com dados isolados de teste.
9. Manter PR #15 DRAFT e não executar merge/deploy de produção.

Não altera dados existentes. Documento de controle de homologação, não prova de aprovação prática.
