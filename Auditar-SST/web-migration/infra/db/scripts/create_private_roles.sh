#!/bin/sh
# SOMENTE container postgres de homologacao NOVO. Comando 1x, sem sobrescrever roles.
set -eu
if [ "${POSTGRES_DB:-}" != "auditar_web_hml" ] || [ "${POSTGRES_USER:-}" != "auditar_web_hml" ]; then
  echo "ABORTADO: banco divergente da homologacao SST" >&2
  exit 1
fi
for name in data_db_password auth_db_password; do
  if [ ! -s "/run/secrets/$name" ]; then
    echo "ABORTADO: segredo de banco ausente" >&2
    exit 1
  fi
done
DATA_PASS=$(tr -d '\r\n' </run/secrets/data_db_password)
AUTH_PASS=$(tr -d '\r\n' </run/secrets/auth_db_password)
if ! printf '%s' "$DATA_PASS" | grep -Eq '^[A-Za-z0-9+/=]{40,}$' ||
   ! printf '%s' "$AUTH_PASS" | grep -Eq '^[A-Za-z0-9+/=]{40,}$'; then
  echo "ABORTADO: credenciais devem ser geradas com openssl rand -base64 48" >&2
  exit 1
fi
psql -X -q -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 <<'SQL'
DO $$
BEGIN
  IF (SELECT count(*) FROM sst.schema_migrations WHERE version IN (1,2,3,4)) <> 4 THEN
    RAISE EXCEPTION 'Migracoes SST 001,002,003,004 necessarias';
  END IF;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname IN ('sst_web_data_hml','sst_web_auth_hml')) THEN
    RAISE EXCEPTION 'Roles de homologacao ja existem; nao redefinir credenciais automaticamente';
  END IF;
END $$;
SQL
{
  printf '\\set data_pwd %s\n' "$DATA_PASS"
  printf '\\set auth_pwd %s\n' "$AUTH_PASS"
  printf 'BEGIN;\n'
  printf "CREATE ROLE sst_web_data_hml LOGIN NOINHERIT PASSWORD :'data_pwd';\n"
  printf "CREATE ROLE sst_web_auth_hml LOGIN NOINHERIT PASSWORD :'auth_pwd';\n"
  printf 'GRANT sst_app_runtime TO sst_web_data_hml WITH INHERIT FALSE, SET TRUE;\n'
  printf 'GRANT sst_auth_runtime TO sst_web_auth_hml WITH INHERIT FALSE, SET TRUE;\n'
  printf 'COMMIT;\n'
} | psql -X -q -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1
unset DATA_PASS AUTH_PASS
echo "Roles de homologacao criados sem publicar senhas. Nao e producao."
