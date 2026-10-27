#!/usr/bin/env bash
# Inicializar SOMENTE um banco NOVO de homologacao com uma conta ficticia.
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ "${AUDITAR_PROVISION_FIRST_ADMIN:-}" != "CONFIRM_PRIVATE_STAGING" ]]; then
  echo "ABORTADO: precisa de confirmacao para criar apenas conta ficticia" >&2
  exit 1
fi
echo "ATENCAO: somente homologacao, e-mail @example.invalid, base vazia."
read -r -p "Empresa de teste (inicie por TESTE): " company_name
read -r -p "Nome de usuario ficticio: " display_name
read -r -p "Email ficticio (@example.invalid): " email
if [[ ! "$company_name" =~ ^TESTE[[:space:]].{3,130}$ ||
      -z "$display_name" || "${#display_name}" -gt 150 ||
      ! "$email" =~ ^[A-Za-z0-9._+-]+@example\.invalid$ ]]; then
  echo "ABORTADO: use somente identidades inteiramente ficticias." >&2
  exit 1
fi
read -r -s -p "Senha NOVA de homologacao (16+ caracteres): " password
echo
read -r -s -p "Repita a senha: " repeat_password
echo
if [[ "${#password}" -lt 16 || "$password" != "$repeat_password" ]]; then
  unset password repeat_password
  echo "Senha curta ou divergente." >&2
  exit 1
fi
unset repeat_password
files=(-f compose.staging.yml -f compose.private-auth.example.yml)
verifier=$(printf '%s' "$password" |
  docker compose -p auditar-sst-web-hml "${files[@]}" exec -T api node hash-password-stdin.mjs)
unset password
if [[ ! "$verifier" =~ ^scrypt\$131072\$8\$1\$[0-9a-f]{32}\$[0-9a-f]{128}$ ]]; then
  echo "Hash nao confirmado. Nao foi criado usuario." >&2
  exit 1
fi
{
  printf '\\set verifier %s\n' "$verifier"
  sed -n '1,$p' db/scripts/provision_first_admin.sql
} | docker compose -p auditar-sst-web-hml "${files[@]}" exec -T db \
  psql -X -q -v ON_ERROR_STOP=1 -U auditar_web_hml -d auditar_web_hml \
  -v company_name="$company_name" -v display_name="$display_name" -v email="$email"
unset verifier
echo "Conta de homologacao criada. Use apenas o URL privado e o email ficticio."
