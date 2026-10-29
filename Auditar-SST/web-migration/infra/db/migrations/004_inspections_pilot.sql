-- AUDITAR SST: vistorias da API WEB, somente banco NOVO de homologacao.
-- Nao importar dados legados; nao executar no servidor de producao atual.
BEGIN;
DO $$
BEGIN
  IF (SELECT count(*) FROM sst.schema_migrations WHERE version IN (1,2,3)) <> 3 THEN
    RAISE EXCEPTION 'Migrações SST 001, 002 e 003 obrigatórias';
  END IF;
  IF EXISTS (SELECT 1 FROM sst.schema_migrations WHERE version=4) THEN
    RAISE EXCEPTION 'SST migration 004 already applied';
  END IF;
END $$;

ALTER TABLE sst.inspection
  ADD COLUMN sector varchar(180) NOT NULL DEFAULT '',
  ADD COLUMN location varchar(180) NOT NULL DEFAULT '',
  ADD COLUMN client_request_id uuid,
  ADD COLUMN revision integer NOT NULL DEFAULT 1 CHECK (revision >= 1),
  ADD COLUMN completed_at timestamptz;
CREATE UNIQUE INDEX inspection_request_dedupe_idx
  ON sst.inspection(company_id,client_request_id)
  WHERE client_request_id IS NOT NULL;

ALTER TABLE sst.non_conformity
  ADD COLUMN short_title varchar(140) NOT NULL DEFAULT '',
  ADD COLUMN client_request_id uuid;
CREATE UNIQUE INDEX nc_request_dedupe_idx
  ON sst.non_conformity(company_id,client_request_id)
  WHERE client_request_id IS NOT NULL;

CREATE TABLE sst.inspection_event (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id uuid NOT NULL REFERENCES sst.company(id),
  inspection_id uuid NOT NULL,
  kind varchar(32) NOT NULL CHECK(kind IN ('criada','editada','achado_incluido','concluida')),
  message varchar(1200) NOT NULL DEFAULT '',
  non_conformity_id uuid,
  created_by uuid,
  created_at timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY(company_id,inspection_id) REFERENCES sst.inspection(company_id,id),
  FOREIGN KEY(company_id,non_conformity_id) REFERENCES sst.non_conformity(company_id,id),
  FOREIGN KEY(company_id,created_by) REFERENCES sst.user_company_role(company_id,user_id)
);
CREATE INDEX inspection_events_timeline_idx
  ON sst.inspection_event(company_id,inspection_id,created_at,id);
GRANT SELECT, INSERT ON sst.inspection_event TO sst_app_runtime;
ALTER TABLE sst.inspection_event ENABLE ROW LEVEL SECURITY;
ALTER TABLE sst.inspection_event FORCE ROW LEVEL SECURITY;
CREATE POLICY inspection_event_company_scope ON sst.inspection_event
  TO sst_app_runtime
  USING(company_id = NULLIF(current_setting('app.company_id',true),'')::uuid)
  WITH CHECK(company_id = NULLIF(current_setting('app.company_id',true),'')::uuid);

INSERT INTO sst.schema_migrations(version,description)
VALUES (4,'Rascunhos, achados, eventos e deduplicacao de vistorias web em homologacao');
COMMIT;
