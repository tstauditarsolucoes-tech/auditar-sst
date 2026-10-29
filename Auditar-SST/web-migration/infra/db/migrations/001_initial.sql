-- AUDITAR SST: migration 001, SOMENTE banco NOVO/homologacao.
-- Nao aponta para Central/Sheets/Drive nem importa registros reais.
-- Exige PostgreSQL 17. Executar usando conta de migracao privilegiada.
BEGIN;
CREATE SCHEMA IF NOT EXISTS sst;
CREATE TABLE IF NOT EXISTS sst.schema_migrations (
  version integer PRIMARY KEY,
  description text NOT NULL,
  applied_at timestamptz NOT NULL DEFAULT now()
);
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM sst.schema_migrations WHERE version = 1) THEN
    RAISE EXCEPTION 'SST migration 001 already applied';
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sst_app_runtime') THEN
    CREATE ROLE sst_app_runtime NOLOGIN;
  END IF;
END $$;

CREATE TABLE sst.company (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name varchar(180) NOT NULL CHECK (length(btrim(name)) > 0),
  status varchar(16) NOT NULL DEFAULT 'ativa'
    CHECK (status IN ('ativa','arquivada')),
  created_at timestamptz NOT NULL DEFAULT now()
);

-- Identidade global: sem senha/login neste esquema inicial.
-- Credenciais e sessao web somente numa etapa posterior de autenticacao.
CREATE TABLE sst.app_user (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  display_name varchar(180) NOT NULL CHECK (length(btrim(display_name)) > 0),
  email varchar(254) NOT NULL,
  active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX app_user_email_lower_unique ON sst.app_user (lower(email));

CREATE TABLE sst.user_company_role (
  company_id uuid NOT NULL REFERENCES sst.company(id),
  user_id uuid NOT NULL REFERENCES sst.app_user(id),
  role varchar(16) NOT NULL CHECK (role IN ('adm','gestor','tecnico','cliente')),
  active boolean NOT NULL DEFAULT true,
  assigned_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (company_id, user_id)
);

CREATE TABLE sst.inspection (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id uuid NOT NULL REFERENCES sst.company(id),
  inspection_type varchar(24) NOT NULL
    CHECK (inspection_type IN ('vistoria','ronda_expressa','checklist')),
  status varchar(20) NOT NULL DEFAULT 'rascunho'
    CHECK (status IN ('rascunho','concluida','arquivada')),
  title varchar(200) NOT NULL DEFAULT '',
  description text NOT NULL DEFAULT '',
  created_by uuid,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(company_id, id),
  FOREIGN KEY (company_id, created_by) REFERENCES sst.user_company_role(company_id, user_id)
);

CREATE TABLE sst.non_conformity (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id uuid NOT NULL REFERENCES sst.company(id),
  inspection_id uuid,
  description text NOT NULL CHECK(length(btrim(description)) > 0),
  probability smallint NOT NULL CHECK(probability BETWEEN 1 AND 5),
  severity smallint NOT NULL CHECK(severity BETWEEN 1 AND 5),
  recurring boolean NOT NULL DEFAULT false,
  status varchar(25) NOT NULL DEFAULT 'aberta'
    CHECK(status IN ('aberta','correcao_informada','validada','rejeitada')),
  created_by uuid,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(company_id,id),
  FOREIGN KEY(company_id,inspection_id) REFERENCES sst.inspection(company_id,id),
  FOREIGN KEY(company_id,created_by) REFERENCES sst.user_company_role(company_id,user_id)
);

-- Tratativas imutaveis: jamais substituir evento anterior pela ultima resposta.
CREATE TABLE sst.nc_treatment_event (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id uuid NOT NULL REFERENCES sst.company(id),
  non_conformity_id uuid NOT NULL,
  kind varchar(30) NOT NULL CHECK(kind IN (
    'identificada','correcao_informada','validada','rejeitada','comentario'
  )),
  message text NOT NULL DEFAULT '',
  created_by uuid,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(company_id,id),
  FOREIGN KEY(company_id,non_conformity_id) REFERENCES sst.non_conformity(company_id,id),
  FOREIGN KEY(company_id,created_by) REFERENCES sst.user_company_role(company_id,user_id),
  CONSTRAINT reason_when_rejected CHECK(kind <> 'rejeitada' OR length(btrim(message)) > 0)
);

-- Apenas METADADOS, nao armazena os bytes nem link publico.
CREATE TABLE sst.evidence (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id uuid NOT NULL REFERENCES sst.company(id),
  inspection_id uuid,
  non_conformity_id uuid,
  object_key text NOT NULL CHECK(length(object_key) > 0),
  sha256 char(64) NOT NULL CHECK(sha256 ~ '^[0-9a-f]{64}$'),
  mime_type varchar(120) NOT NULL,
  size_bytes bigint NOT NULL CHECK(size_bytes > 0),
  kind varchar(20) NOT NULL CHECK(kind IN ('foto','assinatura','pdf','outro')),
  created_by uuid,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(company_id,id),
  FOREIGN KEY(company_id,inspection_id) REFERENCES sst.inspection(company_id,id),
  FOREIGN KEY(company_id,non_conformity_id) REFERENCES sst.non_conformity(company_id,id),
  FOREIGN KEY(company_id,created_by) REFERENCES sst.user_company_role(company_id,user_id),
  CHECK(inspection_id IS NOT NULL OR non_conformity_id IS NOT NULL)
);

CREATE TABLE sst.task (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id uuid NOT NULL REFERENCES sst.company(id),
  title varchar(200) NOT NULL CHECK(length(btrim(title)) > 0),
  description text NOT NULL DEFAULT '',
  assigned_to uuid,
  assigned_by uuid,
  status varchar(20) NOT NULL DEFAULT 'aberta'
    CHECK(status IN ('aberta','em_andamento','concluida','cancelada')),
  due_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(company_id,id),
  FOREIGN KEY(company_id,assigned_to) REFERENCES sst.user_company_role(company_id,user_id),
  FOREIGN KEY(company_id,assigned_by) REFERENCES sst.user_company_role(company_id,user_id)
);

CREATE TABLE sst.task_event (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id uuid NOT NULL REFERENCES sst.company(id),
  task_id uuid NOT NULL,
  kind varchar(30) NOT NULL,
  message text NOT NULL DEFAULT '',
  created_by uuid,
  created_at timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY(company_id,task_id) REFERENCES sst.task(company_id,id),
  FOREIGN KEY(company_id,created_by) REFERENCES sst.user_company_role(company_id,user_id)
);

CREATE TABLE sst.audit_event (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id uuid NOT NULL REFERENCES sst.company(id),
  actor_id uuid,
  event_type varchar(100) NOT NULL,
  resource_type varchar(60) NOT NULL,
  resource_id uuid,
  detail jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY(company_id,actor_id) REFERENCES sst.user_company_role(company_id,user_id)
);

CREATE INDEX inspection_company_created_at_idx ON sst.inspection(company_id,created_at DESC);
CREATE INDEX nc_company_status_idx ON sst.non_conformity(company_id,status,updated_at DESC);
CREATE INDEX nc_treatment_timeline_idx ON sst.nc_treatment_event(company_id,non_conformity_id,created_at);
CREATE INDEX evidence_company_nc_idx ON sst.evidence(company_id,non_conformity_id);
CREATE INDEX task_company_status_idx ON sst.task(company_id,status,due_at);
CREATE INDEX audit_company_created_idx ON sst.audit_event(company_id,created_at DESC);

-- O runtime nao recebe acesso a usuarios/sessoes de autenticacao.
GRANT USAGE ON SCHEMA sst TO sst_app_runtime;
GRANT SELECT ON sst.company TO sst_app_runtime;
GRANT SELECT, INSERT, UPDATE ON sst.inspection, sst.non_conformity, sst.task TO sst_app_runtime;
GRANT SELECT, INSERT ON sst.nc_treatment_event, sst.evidence, sst.task_event, sst.audit_event TO sst_app_runtime;

-- Defesa em profundidade: filtro de empresa tambem no banco.
-- A API autenticada devera SET LOCAL app.company_id num BEGIN/COMMIT por requisicao.
-- Nao conceder credenciais deste role a clientes/dispositivos; nao e sistema auth.
ALTER TABLE sst.company ENABLE ROW LEVEL SECURITY;
ALTER TABLE sst.company FORCE ROW LEVEL SECURITY;
CREATE POLICY company_scope ON sst.company TO sst_app_runtime
  USING(id = NULLIF(current_setting('app.company_id',true),'')::uuid);

ALTER TABLE sst.inspection ENABLE ROW LEVEL SECURITY;
ALTER TABLE sst.inspection FORCE ROW LEVEL SECURITY;
CREATE POLICY inspection_scope ON sst.inspection TO sst_app_runtime
  USING(company_id = NULLIF(current_setting('app.company_id',true),'')::uuid)
  WITH CHECK(company_id = NULLIF(current_setting('app.company_id',true),'')::uuid);

ALTER TABLE sst.non_conformity ENABLE ROW LEVEL SECURITY;
ALTER TABLE sst.non_conformity FORCE ROW LEVEL SECURITY;
CREATE POLICY nc_scope ON sst.non_conformity TO sst_app_runtime
  USING(company_id = NULLIF(current_setting('app.company_id',true),'')::uuid)
  WITH CHECK(company_id = NULLIF(current_setting('app.company_id',true),'')::uuid);

ALTER TABLE sst.nc_treatment_event ENABLE ROW LEVEL SECURITY;
ALTER TABLE sst.nc_treatment_event FORCE ROW LEVEL SECURITY;
CREATE POLICY nc_events_scope ON sst.nc_treatment_event TO sst_app_runtime
  USING(company_id = NULLIF(current_setting('app.company_id',true),'')::uuid)
  WITH CHECK(company_id = NULLIF(current_setting('app.company_id',true),'')::uuid);

ALTER TABLE sst.evidence ENABLE ROW LEVEL SECURITY;
ALTER TABLE sst.evidence FORCE ROW LEVEL SECURITY;
CREATE POLICY evidence_scope ON sst.evidence TO sst_app_runtime
  USING(company_id = NULLIF(current_setting('app.company_id',true),'')::uuid)
  WITH CHECK(company_id = NULLIF(current_setting('app.company_id',true),'')::uuid);

ALTER TABLE sst.task ENABLE ROW LEVEL SECURITY;
ALTER TABLE sst.task FORCE ROW LEVEL SECURITY;
CREATE POLICY task_scope ON sst.task TO sst_app_runtime
  USING(company_id = NULLIF(current_setting('app.company_id',true),'')::uuid)
  WITH CHECK(company_id = NULLIF(current_setting('app.company_id',true),'')::uuid);

ALTER TABLE sst.task_event ENABLE ROW LEVEL SECURITY;
ALTER TABLE sst.task_event FORCE ROW LEVEL SECURITY;
CREATE POLICY task_events_scope ON sst.task_event TO sst_app_runtime
  USING(company_id = NULLIF(current_setting('app.company_id',true),'')::uuid)
  WITH CHECK(company_id = NULLIF(current_setting('app.company_id',true),'')::uuid);

ALTER TABLE sst.audit_event ENABLE ROW LEVEL SECURITY;
ALTER TABLE sst.audit_event FORCE ROW LEVEL SECURITY;
CREATE POLICY audit_scope ON sst.audit_event TO sst_app_runtime
  USING(company_id = NULLIF(current_setting('app.company_id',true),'')::uuid)
  WITH CHECK(company_id = NULLIF(current_setting('app.company_id',true),'')::uuid);

INSERT INTO sst.schema_migrations(version,description)
VALUES (1, 'Empresas, usuarios, vistorias, NC, tratativas, evidencia, agenda e auditoria (staging)');
COMMIT;
