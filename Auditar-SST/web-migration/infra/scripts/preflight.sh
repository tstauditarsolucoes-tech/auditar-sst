#!/usr/bin/env bash
# Somente verificacoes locais de homologacao. NAO sobe containers nem altera o NPM.
set -euo pipefail
cd "$(dirname "$0")/.."

if ! command -v docker >/dev/null 2>&1; then
  echo "ERRO: Docker nao encontrado." >&2
  exit 1
fi
if ! docker compose version >/dev/null 2>&1; then
  echo "ERRO: Docker Compose v2 indisponivel." >&2
  exit 1
fi

if [[ ! -r secrets/postgres_password || ! -s secrets/postgres_password ]]; then
  echo "ERRO: crie secrets/postgres_password com senha de teste forte, fora do Git." >&2
  exit 1
fi

files=(-f compose.staging.yml)
if [[ "${1:-}" == "--npm" ]]; then
  if [[ -z "${AUDITAR_NPM_NETWORK:-}" ]]; then
    echo "ERRO: informe AUDITAR_NPM_NETWORK somente na VPS." >&2
    exit 1
  fi
  docker network inspect "${AUDITAR_NPM_NETWORK}" >/dev/null
  files+=(-f compose.npm.example.yml)
elif [[ $# -ne 0 ]]; then
  echo "Uso: ./scripts/preflight.sh [--npm]" >&2
  exit 2
fi

docker compose -p auditar-sst-web-hml "${files[@]}" config --quiet
if docker compose -p auditar-sst-web-hml "${files[@]}" config --format json | grep -Eq '"ports"[[:space:]]*:'; then
  echo "ERRO: ha portas publicadas no host; abortando." >&2
  exit 1
fi
echo "PREFLIGHT_OK: composicao valida, sem portas publicadas."
echo "Nao foi feito deploy, alteracao no dominio ou acesso a dados reais."
