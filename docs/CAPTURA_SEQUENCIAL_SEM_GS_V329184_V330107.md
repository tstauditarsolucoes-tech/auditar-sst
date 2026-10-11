# Auditar SST: registro sequencial e falhas independentes

Alvos Android **v3.29.184+326** e Windows **v3.30.107+294**. PR #15 Draft.

**A — Uso em campo:** Depois de retornar do formulário de NC na Visita Rápida, uma ação discreta "Novo registro" permite abrir outro formulário com a mesma empresa selecionada. Continua utilizando os setores, a gravação, fotos, permissões e histórico originais. Não presume que houve salvamento caso o usuário tenha cancelado.

**B — SST offline:** Frases independentes são analisadas por equipamento. Um extintor já regularizado não apaga falha atual em botoeira, e a palavra "emergência" em outra oração não contamina a classificação do botão de partida. Separadores mantêm junto do fato histórico expressões de correção. Riscos e prioridades permanecem revisáveis.

**Proteção:** sem Apps Script novo ou implantado, migração de banco, mudança de autenticação, transporte, sincronização, mídia/Drive, IA ou relatório. O patch final confere hashes de outros arquivos da aplicação e da Central. Os pipelines devem rodar format/analyze/test e build antes da entrega. CI não equivale a homologação física.

**Aceitação física:** Android 360–412 px e Windows; testar 2 NCs na mesma empresa, cancelar NC e ver que não houve gravação falsa, checar sugestão em frase com problemas distintos, abrir fotos e relatórios anteriores.
