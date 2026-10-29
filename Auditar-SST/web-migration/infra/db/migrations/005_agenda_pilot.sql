-- AUDITAR SST: Agenda SST piloto, apenas PostgreSQL NOVO de homologacao.
-- Nao instalar em base de clientes ou sobre o antigo site em producao.
BEGIN;
DO $$
BEGIN
  IF (SELECT count(*) FROM sst.schema_migrations WHERE version IN (1,2,3,4)) <> 4 THEN
    RAISE EXCEPTION 'Migracoes 001..004 obrigatorias antes da agenda';
  END IF;
  IF EXISTS (SELECT 1 FROM sst.schema_migrations WHERE version=5) THEN
    RAISE EXCEPTION 'SST migration 005 already applied';
  END IF;
END $$;

ALTER TABLE sst.task
  ADD COLUMN priority varchar(12) NOT NULL DEFAULT 'media'
    CHECK(priority IN ('baixa','media','alta','critica')),
  ADD COLUMN client_request_id uuid,
  ADD COLUMN revision integer NOT NULL DEFAULT 1 CHECK(revision>=1),
  ADD COLUMN completed_at timestamptz;
CREATE UNIQUE INDEX task_request_dedupe_idx
  ON sst.task(company_id,client_request_id)
  WHERE client_request_id IS NOT NULL;

-- A API de tarefas precisa validar a pessoa designada SEM abrir usuarios de outras
-- empresas. O role do aplicativo enxerga apenas vinculos/nomes da empresa da sessao.
-- Autenticador separado continua com leitura global para validar login/vinculos.
-- Nao usar FORCE: o usuario migrador do banco novo precisa provisionar a conta inicial.
ALTER TABLE sst.user_company_role ENABLE ROW LEVEL SECURITY;
CREATE POLICY user_company_auth_read ON sst.user_company_role
  FOR SELECT TO sst_auth_runtime USING (true);
CREATE POLICY user_company_app_tenant_read ON sst.user_company_role
  FOR SELECT TO sst_app_runtime
  USING(company_id = NULLIF(current_setting('app.company_id',true),'')::uuid);
GRANT SELECT ON sst.user_company_role TO sst_app_runtime;

ALTER TABLE sst.app_user ENABLE ROW LEVEL SECURITY;
CREATE POLICY app_user_auth_read ON sst.app_user
  FOR SELECT TO sst_auth_runtime USING (true);
CREATE POLICY app_user_app_tenant_read ON sst.app_user
  FOR SELECT TO sst_app_runtime USING (
    EXISTS (
      SELECT 1 FROM sst.user_company_role r
      WHERE r.company_id = NULLIF(current_setting('app.company_id',true),'')::uuid
        AND r.user_id = sst.app_user.id AND r.active
    )
  );
GRANT SELECT(id,display_name,active) ON sst.app_user TO sst_app_runtime;
CREATE INDEX task_company_assignee_idx ON sst.task(company_id,assigned_to,due_at);
CREATE INDEX task_event_company_idx ON sst.task_event(company_id,task_id,created_at,id);

INSERT INTO sst.schema_migrations(version,description)
VALUES (5,'Agenda SST, designacao, prioridades, revisoes e escopo de membros');
COMMIT;
