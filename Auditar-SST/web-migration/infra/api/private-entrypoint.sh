#!/bin/sh
# Apenas bootstrap de homologacao: copia segredos root-only para tmpfs e
# reduz privilegios ANTES de executar o Node. Nunca imprime credenciais.
set -eu
if [ "$(id -u)" != "0" ]; then
  echo "Bootstrap deve iniciar como root apenas para preparar segredos" >&2
  exit 1
fi
if [ ! -d /run/auditar-private ]; then
  echo "tmpfs privado obrigatorio, nao use disco persistente" >&2
  exit 1
fi
chmod 0700 /run/auditar-private
chown node:node /run/auditar-private
umask 077
for name in data_db_password auth_db_password; do
  if [ ! -r "/run/secrets/$name" ]; then
    echo "Credencial de homologacao ausente" >&2
    exit 1
  fi
  cp "/run/secrets/$name" "/run/auditar-private/$name"
  chown node:node "/run/auditar-private/$name"
  chmod 0400 "/run/auditar-private/$name"
done
if [ "${AUDITAR_EVIDENCE_DIR:-}" != "/var/lib/auditar-staging/evidence" ] ||
   [ ! -d "$AUDITAR_EVIDENCE_DIR" ] || [ -L "$AUDITAR_EVIDENCE_DIR" ]; then
  echo "Volume privado de fotos da homologacao ausente" >&2
  exit 1
fi
chown node:node "$AUDITAR_EVIDENCE_DIR"
chmod 0700 "$AUDITAR_EVIDENCE_DIR"
exec su-exec node node /srv/auditar/server.bootstrap.mjs
