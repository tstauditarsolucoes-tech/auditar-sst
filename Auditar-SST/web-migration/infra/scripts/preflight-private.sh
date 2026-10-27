#!/usr/bin/env bash
# Somente diagnostico: nenhum docker up, nenhuma troca de host, nenhum dado apagado.
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ ! "${AUDITAR_ALLOWED_ORIGIN:-}" =~ ^https://[a-zA-Z0-9.-]+$ ]] ||
   [[ "${AUDITAR_ALLOWED_ORIGIN}" == "https://tst.auditarsolucoes.com.br" ]]; then
  echo "ERRO: use HTTPS em subdominio PRIVADO de homologacao, nao o final." >&2
  exit 1
fi
if [[ -z "${AUDITAR_NPM_NETWORK:-}" ]]; then
  echo "ERRO: informe a rede Docker do Nginx Proxy Manager existente." >&2
  exit 1
fi
for path in postgres_password data_db_password auth_db_password; do
  file="secrets/$path"
  if [[ ! -s "$file" || ! -r "$file" ]]; then
    echo "ERRO: segredo de homologacao ausente: $file" >&2
    exit 1
  fi
  mode=$(stat -c %a "$file")
  if [[ "$mode" != 600 && "$mode" != 400 ]]; then
    echo "ERRO: segredo $file precisa ter chmod 600 ou 400" >&2
    exit 1
  fi
done
docker network inspect "$AUDITAR_NPM_NETWORK" >/dev/null
docker compose -p auditar-sst-web-hml \
 -f compose.staging.yml -f compose.private-auth.example.yml \
 -f compose.npm.example.yml config --quiet
if docker compose -p auditar-sst-web-hml \
 -f compose.staging.yml -f compose.private-auth.example.yml \
 -f compose.npm.example.yml config --format json |
 grep -Eq '"ports"[[:space:]]*:'; then
  echo "ERRO: portas publicadas no host. Abortando." >&2
  exit 1
fi
echo "PREFLIGHT_PRIVATE_OK: sem portas publicadas e nenhum deploy feito."
echo "ATENCAO: revisar manualmente NPM Access List (IP/autenticacao), TLS, backup e rede."
