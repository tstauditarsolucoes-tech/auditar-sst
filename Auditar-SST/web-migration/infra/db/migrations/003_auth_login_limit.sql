-- 003: limitar tentativas de login NOVO da web; somente banco de homologacao.
BEGIN;
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM sst.schema_migrations WHERE version=2)
     OR EXISTS (SELECT 1 FROM sst.schema_migrations WHERE version=3) THEN
    RAISE EXCEPTION 'Migracao 003 exige 002 e so pode ser aplicada uma vez';
  END IF;
END $$;

-- Somente hash da identidade, sem armazenar o e-mail em claro.
CREATE TABLE sst.auth_login_counter (
  identity_hash char(64) PRIMARY KEY CHECK(identity_hash ~ '^[0-9a-f]{64}$'),
  attempt_count integer NOT NULL DEFAULT 0 CHECK(attempt_count BETWEEN 0 AND 1000),
  window_start timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX auth_login_counter_updated_idx ON sst.auth_login_counter(updated_at);
GRANT SELECT,INSERT,UPDATE,DELETE ON sst.auth_login_counter TO sst_auth_runtime;
INSERT INTO sst.schema_migrations(version,description)
VALUES (3,'Limitacao de tentativas de login em janela por identidade, web staging');
COMMIT;
