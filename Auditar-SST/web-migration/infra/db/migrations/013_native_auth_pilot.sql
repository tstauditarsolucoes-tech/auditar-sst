-- 013: autenticacao NATIVA independente, SOMENTE na NOVA homologacao SST.
-- Nenhum dado, senha, token ou cursor e copiado de Flutter/Apps Script.
BEGIN;
DO $$
BEGIN
 IF (SELECT count(*) FROM sst.schema_migrations WHERE version BETWEEN 1 AND 12)<>12
    THEN RAISE EXCEPTION 'Migracoes SST 001 a 012 obrigatorias'; END IF;
 IF EXISTS(SELECT 1 FROM sst.schema_migrations WHERE version=13)
    THEN RAISE EXCEPTION 'Migracao 013 ja aplicada'; END IF;
END $$;
CREATE TABLE sst.native_session (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 token_hash char(64) NOT NULL UNIQUE CHECK(token_hash ~ '^[0-9a-f]{64}$'),
 user_id uuid NOT NULL REFERENCES sst.app_user(id),
 company_id uuid NOT NULL REFERENCES sst.company(id),
 issued_at timestamptz NOT NULL DEFAULT now(),
 expires_at timestamptz NOT NULL,
 revoked_at timestamptz,
 FOREIGN KEY(company_id,user_id) REFERENCES sst.user_company_role(company_id,user_id),
 CHECK(expires_at>issued_at)
);
CREATE INDEX native_session_active_idx ON sst.native_session(user_id,expires_at DESC)
 WHERE revoked_at IS NULL;
CREATE INDEX native_session_expire_idx ON sst.native_session(expires_at);
-- Somente a conta do subsistema de autenticacao, NUNCA o sst_app_runtime.
GRANT SELECT,INSERT,UPDATE ON sst.native_session TO sst_auth_runtime;
INSERT INTO sst.schema_migrations(version,description)
VALUES(13,'Sessao nativa separada com bearer SHA-256 e revogacao, sem sync');
COMMIT;
