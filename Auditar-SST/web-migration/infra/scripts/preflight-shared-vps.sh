#!/usr/bin/env bash
# Auditar SST: INSPECAO READ-ONLY da VPS Docker compartilhada.
# Nao criar/modificar containers, volumes, redes, dominio, NPM nem certificados.
set -euo pipefail
cd "$(dirname "$0")/.."

PROJECT="auditar-sst-web-hml"
DOMAIN="tst.auditarsolucoes.com.br"
NET="${AUDITAR_NPM_NETWORK:-}"
ORIGIN="${AUDITAR_ALLOWED_ORIGIN:-}"

fail() { printf 'BLOQUEADO: %s\n' "$1" >&2; exit 1; }
note() { printf 'VERIFICACAO: %s\n' "$1"; }

command -v docker >/dev/null 2>&1 || fail 'Docker nao instalado'
docker compose version >/dev/null 2>&1 || fail 'Docker Compose v2 indisponivel'
docker info >/dev/null 2>&1 || fail 'Sem acesso de leitura ao daemon Docker'
[[ -n "$NET" ]] || fail 'Defina AUDITAR_NPM_NETWORK com a rede REAL do NPM (sem segredo)'
[[ -n "$ORIGIN" ]] || fail 'Defina AUDITAR_ALLOWED_ORIGIN para hostname PRIVADO de teste'
[[ "$ORIGIN" =~ ^https://[a-zA-Z0-9.-]+$ ]] || fail 'A origem deve usar HTTPS sem caminho/query/porta'
[[ "$ORIGIN" != "https://$DOMAIN" ]] || fail 'Dominio principal ocupado: nao usar para homologacao'
[[ "$NET" != "backend" && "$NET" != "bridge" && "$NET" != "host" && "$NET" != "none" ]] ||
  fail 'Rede Docker generica ou isolada, informe a rede especifica do NPM'

docker network inspect "$NET" >/dev/null 2>&1 || fail 'Rede do NPM inexistente ou inacessivel'
note 'Rede externa do NPM existe; confirmar MANUALMENTE a quem pertence'

# Nao reutilizar projetos, volumes ou nomes ja presentes em VPS compartilhada.
if [[ -n "$(docker ps -aq --filter "label=com.docker.compose.project=$PROJECT")" ]]; then
  fail 'Ja existem containers deste projeto: inventariar antes de qualquer novo deploy'
fi
if [[ -n "$(docker volume ls -q --filter "label=com.docker.compose.project=$PROJECT")" ]]; then
  fail 'Ja existem volumes deste projeto: preserva-los e inventariar'
fi
if [[ -n "$(docker network ls -q --filter "label=com.docker.compose.project=$PROJECT")" ]]; then
  fail 'Ja existem redes deste projeto: revisar antes de qualquer novo deploy'
fi
if [[ -n "$(docker ps -aq --filter 'name=^/auditar-sst-web-hml$')" ]]; then
  fail 'Hostname/container auditar-sst-web-hml em uso'
fi
if docker network inspect "$NET" --format '{{range .Containers}}{{.Name}}{{"\n"}}{{end}}' |
  grep -Eq '^auditar-sst-web-hml$'; then
  fail 'Alias do frontend na rede NPM ocupado'
fi

# Config apenas: nao deve criar nenhum recurso. A API e DB permanecem privados.
docker compose -p "$PROJECT" -f compose.staging.yml \
  -f compose.private-auth.example.yml -f compose.npm.example.yml \
  config --quiet || fail 'Arquivos Compose nao passaram na validacao'
# Inspecao estrutural sem imprimir senhas; exige jq para avaliar TODAS as services.
command -v jq >/dev/null 2>&1 || fail 'Instale jq para inspecao completa do compose'
docker compose -p "$PROJECT" -f compose.staging.yml \
  -f compose.private-auth.example.yml -f compose.npm.example.yml \
  config --format json |
  jq -e 'all(.services[]; (.ports // []) | length == 0)' >/dev/null ||
  fail 'Portas de containers publicadas no host: nao usar na VPS compartilhada'

note 'Composicao isolada sem portas publicadas'
note 'Roteamento NPM/DNS/SSL e uso atual de tst.auditarsolucoes.com.br EXIGEM auditoria manual'
note 'Sem acesso a dados legados, sem deploy, sem alterar volumes ou sistema existente'
printf 'PREFLIGHT_SHARED_VPS_READ_ONLY_OK\n'
