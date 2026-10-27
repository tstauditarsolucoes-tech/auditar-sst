-- 002: NOVA autenticacao WEB, SOMENTE BANCO DE HOMOLOGACAO ISOLADO.
-- NAO importa conta, senha ou sessao da Central Online/Apps Script.
BEGIN;
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM sst.schema_migrations WHERE version=1)
     OR EXISTS (SELECT 1 FROM sst.schema_migrations WHERE version=2) THEN
    RAISE EXCEPTION 'Aplicar 001 antes de 002 e nunca repetir 002';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='sst_auth_runtime') THEN
    CREATE ROLE sst_auth_runtime NOLOGIN;
  END IF;
END $$;

CREATE TABLE sst.auth_credential (
  user_id uuid PRIMARY KEY REFERENCES sst.app_user(id),
  password_verifier text NOT NULL CHECK (length(password_verifier) BETWEEN 120 AND 260),
  changed_at timestamptz NOT NULL DEFAULT now()
);

-- Somente hashes SHA-256 de tokens aleatorios, jamais cookie/token bruto.
CREATE TABLE sst.auth_session (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  token_hash char(64) NOT NULL UNIQUE CHECK (token_hash ~ '^[0-9a-f]{64}$'),
  user_id uuid NOT NULL REFERENCES sst.app_user(id),
  company_id uuid NOT NULL REFERENCES sst.company(id),
  issued_at timestamptz NOT NULL DEFAULT now(),
  expires_at timestamptz NOT NULL,
  revoked_at timestamptz,
  FOREIGN KEY (company_id,user_id) REFERENCES sst.user_company_role(company_id,user_id),
  CHECK (expires_at > issued_at)
);
CREATE INDEX auth_session_user_active_idx ON sst.auth_session(user_id,expires_at DESC)
  WHERE revoked_at IS NULL;
CREATE INDEX auth_session_expiry_idx ON sst.auth_session(expires_at);

GRANT USAGE ON SCHEMA sst TO sst_auth_runtime;
GRANT SELECT ON sst.app_user,sst.user_company_role,sst.company,sst.auth_credential TO sst_auth_runtime;
GRANT SELECT,INSERT,UPDATE ON sst.auth_session TO sst_auth_runtime;

-- O role de autenticacao consulta empresas ativas, mas nao recebe permissoes
-- para vistorias/NC/evidencias. A API de negocio usa OUTRO pool e outro role.
CREATE POLICY company_auth_read ON sst.company FOR SELECT TO sst_auth_runtime USING (true);

INSERT INTO sst.schema_migrations(version,description)
VALUES (2,'Credenciais de nova web e sessoes por cookie HttpOnly, staging');
COMMIT;
