# Auditar SST — Nome curto para identificar NCs (candidato)

O técnico pode usar **Nomear NC** na lista de não conformidades para definir um nome
curto (até 80 caracteres), como **Proteção removida** ou **Extintor vencido**.

- Mostra o nome escolhido em destaque e o código original abaixo.
- Permite pesquisar tanto pelo nome como pelo código ou descrição.
- Mantém o título no detalhe e nas listas de pendências que usam o mesmo registro.
- Sem apelido, exibe automaticamente uma frase curta da descrição.
- Apelidos são armazenados por conta **somente no aparelho atual**, na chave
  `app_settings.nc_display_names_v1_<usuário>` já existente; não há
  sincronização entre dispositivos e o painel web não muda automaticamente.
- Não muda ID, código, classificação, status, descrição oficial, PDF, autenticação,
  sincronização, fotos, esquema SQLite nem Apps Script.
- Deixar o campo vazio restaura a descrição automática.
- A alteração deve ser homologada no Android e no Windows antes do uso em produção.
- Validar contas diferentes, NCs com códigos parecidos e preservação de títulos
  após fechar/reabrir o app, sempre em dados de teste.

PR #15 continua DRAFT. Nenhuma publicação automática da Central.
