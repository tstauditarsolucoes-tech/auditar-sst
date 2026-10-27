# Auditar SST — API de mídia Hostinger

Esta API é a camada de armazenamento principal da v3.29.20. O Google Drive permanece como backup/contingência pela Central Online já existente.

## Publicação na Hostinger

1. Crie uma pasta pública para a API, por exemplo `public_html/auditar-media/`.
2. Envie para ela `index.php`, `.htaccess` e `.user.ini`.
3. Copie `config.example.php` para `config.php` **somente na Hostinger**.
4. Gere uma chave aleatória longa e informe em `api_key`.
5. Em `storage_dir`, aponte para uma pasta privada, preferencialmente fora de `public_html`, e garanta permissão de gravação pelo PHP.
6. Abra o endpoint somente para conferir o servidor; a API aceita operações por POST JSON. A ação `health` informa se a configuração foi carregada.

Exemplo de endpoint final:

`https://SEU-DOMINIO.com/auditar-media/index.php`

## Configuração do app

A compilação aceita duas definições novas:

- `AUDITAR_MEDIA_HOSTINGER_URL`: endpoint HTTPS da API.
- `AUDITAR_MEDIA_HOSTINGER_KEY`: mesma chave configurada em `config.php`.

Se essas definições estiverem vazias, o app continua funcionando pelo Google Drive sem quebrar o fluxo atual. Quando estão configuradas, o fluxo é:

- **envio:** tenta proteger a mídia na Hostinger e mantém a cópia no Google Drive;
- **recuperação:** tenta Hostinger primeiro e, se não encontrar ou houver indisponibilidade, usa o Google Drive;
- **offline:** o arquivo local permanece pendente e é reenviado em um próximo ciclo.

## Organização do armazenamento

A API usa identificadores determinísticos de empresa, tipo de mídia e entidade. A estrutura lógica é:

`empresa / tipo-de-midia / entidade / current.bin + metadata.json`

Os nomes de diretório são sanitizados e recebem hash, evitando colisões e tentativa de navegação de caminho. A mídia não precisa ficar publicamente acessível por URL; o app baixa os bytes pela própria API autenticada.

## Segurança

- Não publique `config.php` no repositório.
- Use HTTPS no domínio.
- Use uma chave forte e diferente da senha do painel Hostinger.
- Prefira `storage_dir` fora de `public_html`.
- A API limita mídia a 12 MB e aceita JPEG, PNG e WEBP, os mesmos formatos usados pelas fotos/logos/assinaturas do app.
- O servidor verifica SHA-256 quando enviado pelo app e novamente no download.

## Migração

A v3.29.20 não apaga arquivos antigos do Drive. Em aparelhos que já possuem mídias locais, elas são copiadas progressivamente para a Hostinger. Em uma reinstalação ou aparelho novo, o app procura a Hostinger primeiro e usa o Drive como fallback.
