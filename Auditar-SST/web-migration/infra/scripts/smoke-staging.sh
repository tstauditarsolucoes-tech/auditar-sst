#!/usr/bin/env bash
# Verificacoes de containers JA iniciados. Somente leitura; nao faz deploy.
set -euo pipefail
cd "$(dirname "$0")/.."
args=(-p auditar-sst-web-hml -f compose.staging.yml)
if [[ "${1:-}" == "--npm" ]]; then
  args+=(-f compose.npm.example.yml)
elif [[ $# -ne 0 ]]; then
  echo "Uso: ./scripts/smoke-staging.sh [--npm]" >&2
  exit 2
fi

docker compose "${args[@]}" exec -T api node -e "fetch('http://127.0.0.1:3000/api/v1/health').then(async r => { const j=await r.json(); if (!r.ok || j.productionDataConnected !== false) process.exit(1); console.log('API_HEALTH_OK'); }).catch(()=>process.exit(1))"
docker compose "${args[@]}" exec -T web sh -c 'wget -qO- http://127.0.0.1:8080/ | grep -q "Auditar SST Web"'
docker compose "${args[@]}" exec -T web sh -c 'wget -qO- http://127.0.0.1:8080/api/v1/health | grep -q productionDataConnected'
echo "SMOKE_OK: React servido no Nginx e API de saude pelo proxy interno."
echo "Isto NAO valida login, NC real, banco, fotos ou prontidao de producao."
