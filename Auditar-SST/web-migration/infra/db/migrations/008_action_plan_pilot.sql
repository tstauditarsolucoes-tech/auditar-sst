-- AUDITAR SST: Plano de Acao WEB, SOMENTE banco NOVO de homologacao.
-- Nao importa planilha, SQLite, Apps Script ou foto de cliente.
BEGIN;
DO $$
BEGIN
  IF (SELECT count(*) FROM sst.schema_migrations WHERE version BETWEEN 1 AND 7) <> 7 THEN
    RAISE EXCEPTION 'SST migrations 001 a 007 obrigatorias';
  END IF;
  IF EXISTS (SELECT 1 FROM sst.schema_migrations WHERE version=8) THEN
    RAISE EXCEPTION 'SST migration 008 ja aplicada';
  END IF;
END $$;

CREATE TABLE sst.action_plan (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id uuid NOT NULL REFERENCES sst.company(id),
  non_conformity_id uuid NOT NULL,
  title varchar(180) NOT NULL CHECK(length(btrim(title))>0),
  description varchar(4000) NOT NULL CHECK(length(btrim(description))>0),
  assigned_to uuid NOT NULL,
  created_by uuid NOT NULL,
  due_at timestamptz,
  status varchar(20) NOT NULL DEFAULT 'aberta'
    CHECK(status IN ('aberta','em_andamento','concluida','cancelada')),
  revision integer NOT NULL DEFAULT 1 CHECK(revision>0),
  client_request_id uuid NOT NULL,
  request_fingerprint char(64) NOT NULL CHECK(request_fingerprint ~ '^[0-9a-f]{64}$'),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  completed_at timestamptz,
  UNIQUE(company_id,id),
  UNIQUE(company_id,client_request_id),
  FOREIGN KEY(company_id,non_conformity_id) REFERENCES sst.non_conformity(company_id,id),
  FOREIGN KEY(company_id,assigned_to) REFERENCES sst.user_company_role(company_id,user_id),
  FOREIGN KEY(company_id,created_by) REFERENCES sst.user_company_role(company_id,user_id)
);
CREATE TABLE sst.action_plan_event (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id uuid NOT NULL REFERENCES sst.company(id),
  action_plan_id uuid NOT NULL,
  kind varchar(24) NOT NULL CHECK(kind IN ('criada','editada','em_andamento','concluida','cancelada')),
  message varchar(1200) NOT NULL DEFAULT '',
  client_request_id uuid,
  resulting_revision integer NOT NULL CHECK(resulting_revision>0),
  created_by uuid NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(company_id,client_request_id),
  FOREIGN KEY(company_id,action_plan_id) REFERENCES sst.action_plan(company_id,id),
  FOREIGN KEY(company_id,created_by) REFERENCES sst.user_company_role(company_id,user_id)
);
CREATE INDEX action_plan_due_idx ON sst.action_plan(company_id,status,due_at,id);
CREATE INDEX action_plan_nc_idx ON sst.action_plan(company_id,non_conformity_id);
CREATE INDEX action_plan_event_idx ON sst.action_plan_event(company_id,action_plan_id,created_at,id);

GRANT SELECT,INSERT,UPDATE ON sst.action_plan TO sst_app_runtime;
GRANT SELECT,INSERT ON sst.action_plan_event TO sst_app_runtime;
ALTER TABLE sst.action_plan ENABLE ROW LEVEL SECURITY;
ALTER TABLE sst.action_plan FORCE ROW LEVEL SECURITY;
CREATE POLICY action_plan_company_scope ON sst.action_plan TO sst_app_runtime
  USING(company_id=NULLIF(current_setting('app.company_id',true),'')::uuid)
  WITH CHECK(company_id=NULLIF(current_setting('app.company_id',true),'')::uuid);
ALTER TABLE sst.action_plan_event ENABLE ROW LEVEL SECURITY;
ALTER TABLE sst.action_plan_event FORCE ROW LEVEL SECURITY;
CREATE POLICY action_plan_event_company_scope ON sst.action_plan_event TO sst_app_runtime
  USING(company_id=NULLIF(current_setting('app.company_id',true),'')::uuid)
  WITH CHECK(company_id=NULLIF(current_setting('app.company_id',true),'')::uuid);

INSERT INTO sst.schema_migrations(version,description)
VALUES(8,'Plano de acao WEB: NC vinculada, responsavel, prazo, status, eventos e RLS');
COMMIT;
