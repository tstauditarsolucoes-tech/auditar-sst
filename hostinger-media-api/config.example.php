<?php
// Copie este arquivo para config.php SOMENTE no servidor Hostinger.
// Não envie config.php com a chave real para o GitHub.
return [
    // Gere uma chave longa e aleatória (mínimo recomendado: 64 caracteres).
    'api_key' => 'TROQUE-POR-UMA-CHAVE-LONGA-E-ALEATORIA',

    // Preferencialmente use uma pasta FORA de public_html.
    // Exemplo Hostinger (ajuste ao seu usuário/domínio):
    // '/home/u123456789/domains/seu-dominio.com/auditar_storage'
    'storage_dir' => '/CAMINHO/PRIVADO/auditar_storage',

    // Mesmo limite atual do app: 12 MB por mídia.
    'max_bytes' => 12 * 1024 * 1024,
];
