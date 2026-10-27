# Auditoria de redundâncias de navegação — Auditar SST
Data: 13/10/2026.

## Implementação
Foi acrescentado um segundo inventário estático que complementa `NAVIGACAO_INVENTARIO`.
A rotina identifica classes de telas utilizadas por outros arquivos e contabiliza referências compartilhadas ou repetidas dentro da mesma tela. Exporta `DESTINOS_REPETIDOS.json` e `DESTINOS_REPETIDOS.md` nos artefatos de auditoria de Android e Windows.

## Critérios de interpretação
- Uma rota para a mesma tela na Home e no acompanhamento da obra NÃO é duplicação funcional por si só.
- Uma tela ter dois botões para o mesmo destino pode ser uma escolha de design, não recurso inútil.
- Classes com nomes repetidos em arquivos diferentes são sinalizadas, não excluídas.
- Esta análise não testa o clique real, fluxo após login ou disponibilidade das rotas do GS em produção.
- Antes de eliminar uma função, conferir registros de usuários e dependências, caminhos reais, permissões e testes físicos.

## Restrições
Nenhum módulo foi removido ou desativado.
Nenhum arquivo de `lib/`, banco, sincronização, autenticação, IA, fotos, Drive ou Apps Script foi modificado.
Os builds continuam gerando APK e instalador da linha Android v3.29.190 / Windows v3.30.113, sujeitos à aprovação do CI. PR #15 continua Draft, sem merge/deploy.

## Próxima análise
Cruzar o inventário de destinos com os 31/39 rótulos que já foram detectados como repetidos nas versões anteriores e propor mudanças de interface sem excluir fluxos.
