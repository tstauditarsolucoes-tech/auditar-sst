<?php
declare(strict_types=1);

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');

const API_VERSION = '1.0.0';
const DEFAULT_MAX_BYTES = 12582912; // 12 MB

function respond(array $data, int $status = 200): never {
    http_response_code($status);
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}

function read_config(): array {
    $file = __DIR__ . '/config.php';
    if (!is_file($file)) return [];
    $config = require $file;
    return is_array($config) ? $config : [];
}

function safe_segment(string $value): string {
    $value = trim($value);
    if ($value === '') return 'sem-id';
    $clean = preg_replace('/[^A-Za-z0-9._-]+/', '_', $value) ?: 'id';
    $clean = trim($clean, '._-');
    if ($clean === '') $clean = 'id';
    $clean = substr($clean, 0, 80);
    return $clean . '-' . substr(hash('sha256', $value), 0, 12);
}

function safe_filename(string $value): string {
    $value = basename(trim($value));
    $value = preg_replace('/[^A-Za-z0-9._ -]+/', '_', $value) ?: 'arquivo';
    $value = trim($value, " .\t\n\r\0\x0B");
    if ($value === '') $value = 'arquivo';
    return substr($value, 0, 140);
}

function request_payload(): array {
    if (($_SERVER['REQUEST_METHOD'] ?? '') === 'OPTIONS') respond(['ok' => true]);
    if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
        respond(['ok' => false, 'message' => 'Use POST com JSON.'], 405);
    }
    $raw = file_get_contents('php://input');
    if ($raw === false || trim($raw) === '') return [];
    $decoded = json_decode($raw, true);
    if (!is_array($decoded)) respond(['ok' => false, 'message' => 'JSON inválido.'], 400);
    return $decoded;
}

function require_api_key(array $config, array $payload): void {
    $expected = trim((string)($config['api_key'] ?? ''));
    if ($expected === '') respond(['ok' => false, 'message' => 'API ainda não configurada.'], 503);
    $header = trim((string)($_SERVER['HTTP_X_AUDITAR_KEY'] ?? ''));
    $body = trim((string)($payload['apiKey'] ?? ''));
    $received = $header !== '' ? $header : $body;
    if ($received === '' || !hash_equals($expected, $received)) {
        respond(['ok' => false, 'message' => 'Chave inválida.'], 401);
    }
}

function storage_root(array $config): string {
    $root = trim((string)($config['storage_dir'] ?? ''));
    if ($root === '') respond(['ok' => false, 'message' => 'Diretório de armazenamento não configurado.'], 503);
    if (!is_dir($root) && !mkdir($root, 0750, true) && !is_dir($root)) {
        respond(['ok' => false, 'message' => 'Não foi possível preparar o armazenamento.'], 500);
    }
    return rtrim($root, DIRECTORY_SEPARATOR);
}

function asset_dir(string $root, string $companyId, string $entityType, string $entityId): string {
    return $root . DIRECTORY_SEPARATOR . safe_segment($companyId)
        . DIRECTORY_SEPARATOR . safe_segment($entityType)
        . DIRECTORY_SEPARATOR . safe_segment($entityId);
}

function validate_identity(array $payload): array {
    $companyId = trim((string)($payload['companyId'] ?? ''));
    $entityType = trim((string)($payload['entityType'] ?? ''));
    $entityId = trim((string)($payload['entityId'] ?? ''));
    if ($companyId === '' || $entityType === '' || $entityId === '') {
        respond(['ok' => false, 'message' => 'Empresa ou mídia não identificada.'], 400);
    }
    if (strlen($companyId) > 200 || strlen($entityType) > 80 || strlen($entityId) > 200) {
        respond(['ok' => false, 'message' => 'Identificador inválido.'], 400);
    }
    return [$companyId, $entityType, $entityId];
}

$config = read_config();
$payload = request_payload();
$action = strtolower(trim((string)($payload['action'] ?? '')));

if ($action === 'health') {
    respond([
        'ok' => true,
        'service' => 'Auditar SST Media Storage',
        'version' => API_VERSION,
        'configured' => trim((string)($config['api_key'] ?? '')) !== ''
            && trim((string)($config['storage_dir'] ?? '')) !== '',
    ]);
}

require_api_key($config, $payload);
$root = storage_root($config);
$maxBytes = (int)($config['max_bytes'] ?? DEFAULT_MAX_BYTES);
if ($maxBytes <= 0) $maxBytes = DEFAULT_MAX_BYTES;

if ($action === 'upload') {
    [$companyId, $entityType, $entityId] = validate_identity($payload);
    $encoded = trim((string)($payload['contentBase64'] ?? ''));
    if ($encoded === '') respond(['ok' => false, 'message' => 'Arquivo vazio.'], 400);
    $bytes = base64_decode($encoded, true);
    if ($bytes === false || $bytes === '') respond(['ok' => false, 'message' => 'Arquivo inválido.'], 400);
    $size = strlen($bytes);
    if ($size > $maxBytes) respond(['ok' => false, 'message' => 'Arquivo acima do limite permitido.'], 413);

    $mime = strtolower(trim((string)($payload['mimeType'] ?? 'application/octet-stream')));
    $allowed = ['image/jpeg', 'image/png', 'image/webp'];
    if (!in_array($mime, $allowed, true)) {
        respond(['ok' => false, 'message' => 'Formato de mídia não permitido.'], 415);
    }

    $name = safe_filename((string)($payload['fileName'] ?? 'midia'));
    $sha = hash('sha256', $bytes);
    $clientSha = strtolower(trim((string)($payload['sha256'] ?? '')));
    if ($clientSha !== '' && !hash_equals($sha, $clientSha)) {
        respond(['ok' => false, 'message' => 'Integridade da mídia não confere.'], 400);
    }

    $dir = asset_dir($root, $companyId, $entityType, $entityId);
    if (!is_dir($dir) && !mkdir($dir, 0750, true) && !is_dir($dir)) {
        respond(['ok' => false, 'message' => 'Não foi possível criar a pasta da mídia.'], 500);
    }
    $dataPath = $dir . DIRECTORY_SEPARATOR . 'current.bin';
    $metaPath = $dir . DIRECTORY_SEPARATOR . 'metadata.json';
    $tmp = $dataPath . '.tmp-' . bin2hex(random_bytes(6));
    if (file_put_contents($tmp, $bytes, LOCK_EX) === false || !rename($tmp, $dataPath)) {
        @unlink($tmp);
        respond(['ok' => false, 'message' => 'Falha ao gravar a mídia.'], 500);
    }
    $metadata = [
        'companyId' => $companyId,
        'entityType' => $entityType,
        'entityId' => $entityId,
        'fileName' => $name,
        'mimeType' => $mime,
        'bytes' => $size,
        'sha256' => $sha,
        'updatedAt' => gmdate('c'),
    ];
    file_put_contents($metaPath, json_encode($metadata, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES), LOCK_EX);
    respond([
        'ok' => true,
        'storageId' => substr(hash('sha256', $companyId . '|' . $entityType . '|' . $entityId), 0, 32),
        'fileName' => $name,
        'mimeType' => $mime,
        'bytes' => $size,
        'sha256' => $sha,
        'message' => 'Mídia protegida na Hostinger.',
    ]);
}

if ($action === 'download' || $action === 'stat') {
    [$companyId, $entityType, $entityId] = validate_identity($payload);
    $dir = asset_dir($root, $companyId, $entityType, $entityId);
    $dataPath = $dir . DIRECTORY_SEPARATOR . 'current.bin';
    $metaPath = $dir . DIRECTORY_SEPARATOR . 'metadata.json';
    if (!is_file($dataPath) || !is_file($metaPath)) {
        respond(['ok' => false, 'code' => 'NOT_FOUND', 'message' => 'Mídia não encontrada.'], 404);
    }
    $metadata = json_decode((string)file_get_contents($metaPath), true);
    if (!is_array($metadata)) respond(['ok' => false, 'message' => 'Metadados da mídia inválidos.'], 500);
    if ($action === 'stat') respond(['ok' => true] + $metadata);

    $bytes = file_get_contents($dataPath);
    if ($bytes === false || $bytes === '') respond(['ok' => false, 'message' => 'Mídia vazia.'], 500);
    if (strlen($bytes) > $maxBytes) respond(['ok' => false, 'message' => 'Mídia acima do limite permitido.'], 413);
    $sha = hash('sha256', $bytes);
    if (!hash_equals((string)($metadata['sha256'] ?? ''), $sha)) {
        respond(['ok' => false, 'message' => 'Falha de integridade da mídia armazenada.'], 500);
    }
    respond([
        'ok' => true,
        'fileName' => (string)($metadata['fileName'] ?? 'midia'),
        'mimeType' => (string)($metadata['mimeType'] ?? 'image/jpeg'),
        'contentBase64' => base64_encode($bytes),
        'bytes' => strlen($bytes),
        'sha256' => $sha,
        'source' => 'hostinger',
    ]);
}

if ($action === 'delete') {
    [$companyId, $entityType, $entityId] = validate_identity($payload);
    $dir = asset_dir($root, $companyId, $entityType, $entityId);
    foreach (['current.bin', 'metadata.json'] as $name) {
        $path = $dir . DIRECTORY_SEPARATOR . $name;
        if (is_file($path)) @unlink($path);
    }
    @rmdir($dir);
    respond(['ok' => true, 'message' => 'Mídia removida da Hostinger.']);
}

respond(['ok' => false, 'message' => 'Ação inválida.'], 400);
