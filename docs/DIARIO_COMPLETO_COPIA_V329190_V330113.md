# Auditar SST — cópia local do diário completo (13/10/2026)

- Código em validação: Android **v3.29.190+332** / Windows **v3.30.113+300**.
- Na tela **Acompanhamento da obra > Diário da obra**, ação explícita **Copiar diário completo**.
- Reúne os até 80 lançamentos recentes com o arquivo local de registros anteriores, preservado desde v3.29.189 / v3.30.112.
- Ordena por data registrada, informa obra, etapa e quantidade. Não altera a informação SST original e não envia dados automaticamente.
- A cópia vai para a área de transferência **somente após o toque**; orientar o técnico a conferir antes de compartilhar, pois contém observações de campo.
- Usuário e obra têm escopos próprios e a autorização é reconferida antes da cópia.
- Continua havendo limite de 80 registros no payload de obras da Central V1, sem perda do arquivo local anterior.
- Sem alterações de GS, autenticação, sincronização, banco SST, fotos, Drive, IA ou PDFs.
- Requer CI, testes físicos Android/Windows e conferência do conteúdo copiado.
- PR #15 permanece em DRAFT; sem merge ou deploy.
