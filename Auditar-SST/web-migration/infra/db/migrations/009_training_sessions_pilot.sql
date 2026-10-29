-- Apenas para banco NOVO e PRIVADO de homologacao SST. Nunca executar na Central Online.
BEGIN;
DO $$
BEGIN
  IF (SELECT count(*) FROM sst.schema_migrations WHERE version BETWEEN 1 AND 8) <> 8 THEN
    RAISE EXCEPTION 'Aplicar migracoes SST 001 a 008 antes da 009';
  END IF;
  IF EXISTS (SELECT 1 FROM sst.schema_migrations WHERE version=9) THEN
    RAISE EXCEPTION 'Migracao SST 009 ja aplicada';
  END IF;
END $$;

CREATE TABLE sst.training_session (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id uuid NOT NULL REFERENCES sst.company(id),
  kind varchar(20) NOT NULL CHECK(kind IN ('treinamento','dds','integracao')),
  title varchar(200) NOT NULL CHECK(length(btrim(title))>0),
  sector varchar(180) NOT NULL DEFAULT '',
  nr_reference varchar(100) NOT NULL DEFAULT '',
  instructor varchar(180) NOT NULL DEFAULT '',
  planned_at timestamptz,
  duration_minutes integer CHECK(duration_minutes IS NULL OR duration_minutes BETWEEN 1 AND 1440),
  participants_count integer CHECK(participants_count IS NULL OR participants_count BETWEEN 0 AND 10000),
  status varchar(16) NOT NULL DEFAULT 'planejado'
    CHECK(status IN ('planejado','realizado','cancelado')),
  revision integer NOT NULL DEFAULT 1 CHECK(revision>0),
  created_by uuid NOT NULL,
  client_request_id uuid NOT NULL,
  request_fingerprint char(64) NOT NULL CHECK(request_fingerprint ~ '^[0-9a-f]{64}$'),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  completed_at timestamptz,
  UNIQUE(company_id,id),
  UNIQUE(company_id,client_request_id),
  FOREIGN KEY(company_id,created_by) REFERENCES sst.user_company_role(company_id,user_id)
);
CREATE TABLE sst.training_event (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id uuid NOT NULL REFERENCES sst.company(id),
  training_id uuid NOT NULL,
  kind varchar(24) NOT NULL CHECK(kind IN ('criada','editada','realizado','cancelado')),
  message varchar(1200) NOT NULL DEFAULT '',
  resulting_revision integer NOT NULL CHECK(resulting_revision>0),
  client_request_id uuid,
  created_by uuid NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(company_id,client_request_id),
  FOREIGN KEY(company_id,training_id) REFERENCES sst.training_session(company_id,id),
  FOREIGN KEY(company_id,created_by) REFERENCES sst.user_company_role(company_id,user_id)
);
CREATE INDEX training_company_status_idx ON sst.training_session(company_id,status,planned_at,id);
CREATE INDEX training_company_kind_idx ON sst.training_session(company_id,kind,updated_at DESC);
CREATE INDEX training_event_history_idx ON sst.training_event(company_id,training_id,created_at,id);
GRANT SELECT,INSERT,UPDATE ON sst.training_session TO sst_app_runtime;
GRANT SELECT,INSERT ON sst.training_event TO sst_app_runtime;
ALTER TABLE sst.training_session ENABLE ROW LEVEL SECURITY;
ALTER TABLE sst.training_session FORCE ROW LEVEL SECURITY;
CREATE POLICY training_company_scope ON sst.training_session TO sst_app_runtime
  USING(company_id=NULLIF(current_setting('app.company_id',true),'')::uuid)
  WITH CHECK(company_id=NULLIF(current_setting('app.company_id',true),'')::uuid);
ALTER TABLE sst.training_event ENABLE ROW LEVEL SECURITY;
ALTER TABLE sst.training_event FORCE ROW LEVEL SECURITY;
CREATE POLICY training_event_company_scope ON sst.training_event TO sst_app_runtime
  USING(company_id=NULLIF(current_setting('app.company_id',true),'')::uuid)
  WITH CHECK(company_id=NULLIF(current_setting('app.company_id',true),'')::uuid);
INSERT INTO sst.schema_migrations(version,description)
VALUES(9,'Treinamentos, DDS e integracao Web: registros de planejamento e eventos RLS');
COMMIT;
