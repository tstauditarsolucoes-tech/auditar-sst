# Candidato de treinamento Auditar SST - 26/10/2026

## Escopo
- Reforço do mini tutorial por conta (tutorialVersion 2), com textos revisados para operação de campo, NCs, rascunhos, relatórios, empresa/obra, histórico e gestão.
- Entradas novas no catálogo: novidades, tratativas, linha do tempo, biblioteca offline, supervisão ADM, agenda e NR-18.
- Atalho Novidades do app ao lado de Ajuda rápida, sujeito à conferência em aparelhos estreitos.
- Fix defensivo do ponto de inserção de status da biblioteca após atalho Linha do Tempo.

## Segurança
- Não altera SQLite, login, autenticação, GS, sincronização, fotos, PDF ou bases de clientes.
- Não publicar Central, não executar setupAuditar(), não mesclar PR #15.
- Confirmar compilação Android + Windows do mesmo commit e testar em contas/empresa fictícias.

## Roteiro de homologação do mini tutorial
1. Usuário que já viu v1: ao abrir Home deve aparecer tutorial atualizado uma vez para v2.
2. Usuário novo: dicas por área; verificar tamanho em tela Android estreita.
3. Botão Ajuda rápida abre ajuda Home; botão Novidades do app abre catálogo resumido.
4. Configurações > Reiniciar mini tutorial restaura dicas para conta atual.
5. NC: texto não afirma como pronta a edição de título; apresenta como pendência.
6. Linha do Tempo: texto indica disponibilidade por versão.
7. Tratativas: texto indica dependência da Central e das permissões.
8. ADM: Último contato não deve ser descrito como online em tempo real.
9. Android 360 x 640 e Windows em janela normal e maximizada: sem recortes/overflow.
10. Executar regressão de login, mídia, rascunho, PDF, fila e sincronização antes de distribuir.
