-- AUDITAR SST: atendimento cliente e visao gerencial WEB, apenas homologacao nova.
-- Nao acessar Central Online, Apps Script, Drive nem dados de clientes existentes.
BEGIN;
DO $$
BEGIN
  IF (SELECT count(*) FROM sst.schema_migrations WHERE version IN (1,2,3,4,5)) <> 5 THEN
    RAISE EXCEPTION 'Migracoes 001 a 005 necessarias antes da 006';
  END IF;
  IF EXISTS(SELECT 1 FROM sst.schema_migrations WHERE version=6) THEN
    RAISE EXCEPTION 'SST migration 006 ja aplicada';
  END IF;
END $$;

CREATE TABLE sst.support_thread (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id uuid NOT NULL REFERENCES sst.company(id),
  subject varchar(160) NOT NULL CHECK(length(btrim(subject))>0),
  status varchar(16) NOT NULL DEFAULT 'aberta' CHECK(status IN ('aberta','encerrada')),
  created_by uuid NOT NULL,
  client_request_id uuid NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(company_id,id),
  UNIQUE(company_id,client_request_id),
  FOREIGN KEY(company_id,created_by) REFERENCES sst.user_company_role(company_id,user_id)
);

CREATE TABLE sst.support_message (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id uuid NOT NULL REFERENCES sst.company(id),
  thread_id uuid NOT NULL,
  message varchar(1500) NOT NULL CHECK(length(btrim(message))>0),
  kind varchar(24) NOT NULL DEFAULT 'mensagem'
    CHECK(kind IN ('mensagem','encerramento','reabertura')),
  client_request_id uuid NOT NULL,
  created_by uuid NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(company_id,client_request_id),
  FOREIGN KEY(company_id,thread_id) REFERENCES sst.support_thread(company_id,id),
  FOREIGN KEY(company_id,created_by) REFERENCES sst.user_company_role(company_id,user_id)
);

-- Presenca e uma aproximacao baseada SOMENTE no uso da interface Web NOVA.
-- Nunca indicar atividade real do app Flutter; isso exigira adaptador separado.
CREATE TABLE sst.web_user_activity (
  company_id uuid NOT NULL REFERENCES sst.company(id),
  user_id uuid NOT NULL,
  last_seen timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY(company_id,user_id),
  FOREIGN KEY(company_id,user_id) REFERENCES sst.user_company_role(company_id,user_id)
);

CREATE INDEX support_thread_company_status_idx
  ON sst.support_thread(company_id,status,updated_at DESC);
CREATE INDEX support_message_company_thread_idx
  ON sst.support_message(company_id,thread_id,created_at,id);
CREATE INDEX web_user_activity_company_seen_idx
  ON sst.web_user_activity(company_id,last_seen DESC);

GRANT SELECT,INSERT,UPDATE ON sst.support_thread,sst.web_user_activity TO sst_app_runtime;
GRANT SELECT,INSERT ON sst.support_message TO sst_app_runtime;
ALTER TABLE sst.support_thread ENABLE ROW LEVEL SECURITY;
ALTER TABLE sst.support_thread FORCE ROW LEVEL SECURITY;
CREATE POLICY support_thread_company_scope ON sst.support_thread TO sst_app_runtime
  USING(company_id = NULLIF(current_setting('app.company_id',true),'')::uuid)
  WITH CHECK(company_id = NULLIF(current_setting('app.company_id',true),'')::uuid);
ALTER TABLE sst.support_message ENABLE ROW LEVEL SECURITY;
ALTER TABLE sst.support_message FORCE ROW LEVEL SECURITY;
CREATE POLICY support_message_company_scope ON sst.support_message TO sst_app_runtime
  USING(company_id = NULLIF(current_setting('app.company_id',true),'')::uuid)
  WITH CHECK(company_id = NULLIF(current_setting('app.company_id',true),'')::uuid);
ALTER TABLE sst.web_user_activity ENABLE ROW LEVEL SECURITY;
ALTER TABLE sst.web_user_activity FORCE ROW LEVEL SECURITY;
CREATE POLICY web_activity_company_scope ON sst.web_user_activity TO sst_app_runtime
  USING(company_id = NULLIF(current_setting('app.company_id',true),'')::uuid)
  WITH CHECK(company_id = NULLIF(current_setting('app.company_id',true),'')::uuid);

INSERT INTO sst.schema_migrations(version,description)
VALUES(6,'Portal do cliente, conversas de apoio e visao gerencial web isolada');
COMMIT;
