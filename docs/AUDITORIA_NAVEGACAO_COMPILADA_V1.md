# Inventário real de telas e possíveis redundâncias — Auditar SST

## Método
A auditoria é executada **depois de todos os patches** que montam o Flutter, imediatamente antes do build release. Inspeciona apenas os arquivos finais de lib/ e a cópia do Code.gs incluída no pacote de homologação. Não altera os módulos, o banco, a autenticação, as fotos, os relatórios ou a sincronização.

Em cada artefato Android/Windows a pasta `Auditoria-Navegacao` passa a conter dois arquivos: inventário de telas/rotas em JSON e relatório legível em Markdown.

## Interpretação
- **Cadeia estática de importação** permite encontrar telas claramente referenciadas a partir de main.dart. Uma tela fora dessa cadeia é apenas uma **candidata** para investigação, nunca um módulo comprovadamente inútil.
- **Rótulos repetidos** em mais de uma tela são apenas pontos de duplicidade de navegação. A mesma ação no contexto da empresa e da obra pode ser necessária.
- **Import local ausente** é tratado como erro antes do build final.
- **Rotas GS no pacote** mostram somente presença textual na cópia de homologação. Não significam que a rota esteja ativa no serviço publicado.

## Regras
1. Não excluir nenhuma tela ou entrada por causa desse relatório.
2. Identificar o caminho do usuário e se o botão navega para a mesma função com filtros corretos.
3. Conferir evidências e registros históricos antes de consolidar implementações.
4. Testar login, acesso multiempresa, offline, relatórios/fotos, Android e Windows.
5. PR #15 permanece Draft. Não fazer merge/deploy do Apps Script sem autorização.
