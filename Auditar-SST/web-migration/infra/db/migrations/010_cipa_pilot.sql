-- AUDITAR SST: piloto CIPA separado e somente em banco NOVO de homologacao.
-- Sem certificacao NR-5, voto, atas assinadas, dados pessoais reais ou migracao legada.
BEGIN;
DO $$
BEGIN
  IF (SELECT count(*) FROM sst.schema_migrations WHERE version BETWEEN 1 AND 9) <> 9 THEN
    RAISE EXCEPTION 'Migracoes SST 001 a 009 obrigatorias';
  END IF;
  IF EXISTS (SELECT 1 FROM sst.schema_migrations WHERE version=10) THEN
    RAISE EXCEPTION 'Migracao SST 010 ja aplicada';
  END IF;
END $$;
CREATE TABLE sst.cipa_mandate (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id uuid NOT NULL REFERENCES sst.company(id),
  name varchar(180) NOT NULL CHECK(length(btrim(name))>0),
  starts_on date NOT NULL,
  ends_on date NOT NULL,
  election_on date,
  status varchar(20) NOT NULL DEFAULT 'preparacao'
    CHECK(status IN ('preparacao','ativo','encerrado')),
  revision integer NOT NULL DEFAULT 1 CHECK(revision>0),
  created_by uuid NOT NULL,
  client_request_id uuid NOT NULL,
  request_fingerprint char(64) NOT NULL CHECK(request_fingerprint ~ '^[0-9a-f]{64}$'),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(company_id,id),
  UNIQUE(company_id,client_request_id),
  CHECK(ends_on >= starts_on),
  FOREIGN KEY(company_id,created_by) REFERENCES sst.user_company_role(company_id,user_id)
);
CREATE TABLE sst.cipa_member (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id uuid NOT NULL REFERENCES sst.company(id),
  mandate_id uuid NOT NULL,
  display_name varchar(180) NOT NULL CHECK(length(btrim(display_name))>0),
  representation varchar(20) NOT NULL CHECK(representation IN ('empregados','empregador','designado')),
  seat varchar(20) NOT NULL CHECK(seat IN ('titular','suplente','designado')),
  created_by uuid NOT NULL,
  client_request_id uuid NOT NULL,
  request_fingerprint char(64) NOT NULL CHECK(request_fingerprint ~ '^[0-9a-f]{64}$'),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(company_id,id),
  UNIQUE(company_id,client_request_id),
  CHECK(
    (representation='designado' AND seat='designado') OR
    (representation<>'designado' AND seat<>'designado')
  ),
  FOREIGN KEY(company_id,mandate_id) REFERENCES sst.cipa_mandate(company_id,id),
  FOREIGN KEY(company_id,created_by) REFERENCES sst.user_company_role(company_id,user_id)
);
CREATE TABLE sst.cipa_meeting (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id uuid NOT NULL REFERENCES sst.company(id),
  mandate_id uuid NOT NULL,
  title varchar(200) NOT NULL CHECK(length(btrim(title))>0),
  scheduled_at timestamptz NOT NULL,
  summary varchar(4000) NOT NULL DEFAULT '',
  status varchar(20) NOT NULL DEFAULT 'planejada'
    CHECK(status IN ('planejada','realizada','cancelada')),
  revision integer NOT NULL DEFAULT 1 CHECK(revision>0),
  created_by uuid NOT NULL,
  client_request_id uuid NOT NULL,
  request_fingerprint char(64) NOT NULL CHECK(request_fingerprint ~ '^[0-9a-f]{64}$'),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(company_id,id),
  UNIQUE(company_id,client_request_id),
  FOREIGN KEY(company_id,mandate_id) REFERENCES sst.cipa_mandate(company_id,id),
  FOREIGN KEY(company_id,created_by) REFERENCES sst.user_company_role(company_id,user_id)
);
CREATE TABLE sst.cipa_event (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id uuid NOT NULL REFERENCES sst.company(id),
  mandate_id uuid NOT NULL,
  kind varchar(30) NOT NULL CHECK(kind IN (
    'mandato_criado','mandato_ativo','mandato_encerrado',
    'membro_adicionado','reuniao_agendada','reuniao_realizada','reuniao_cancelada'
  )),
  message varchar(1200) NOT NULL DEFAULT '',
  source_id uuid,
  created_by uuid NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY(company_id,mandate_id) REFERENCES sst.cipa_mandate(company_id,id),
  FOREIGN KEY(company_id,created_by) REFERENCES sst.user_company_role(company_id,user_id)
);
CREATE INDEX cipa_mandate_company_idx ON sst.cipa_mandate(company_id,status,starts_on DESC);
CREATE INDEX cipa_member_mandate_idx ON sst.cipa_member(company_id,mandate_id,created_at);
CREATE INDEX cipa_meeting_mandate_idx ON sst.cipa_meeting(company_id,mandate_id,scheduled_at);
CREATE INDEX cipa_event_mandate_idx ON sst.cipa_event(company_id,mandate_id,created_at,id);
GRANT SELECT,INSERT,UPDATE ON sst.cipa_mandate TO sst_app_runtime;
GRANT SELECT,INSERT ON sst.cipa_member TO sst_app_runtime;
GRANT SELECT,INSERT,UPDATE ON sst.cipa_meeting TO sst_app_runtime;
GRANT SELECT,INSERT ON sst.cipa_event TO sst_app_runtime;
ALTER TABLE sst.cipa_mandate ENABLE ROW LEVEL SECURITY;
ALTER TABLE sst.cipa_mandate FORCE ROW LEVEL SECURITY;
CREATE POLICY cipa_mandate_company_scope ON sst.cipa_mandate TO sst_app_runtime
  USING(company_id=NULLIF(current_setting('app.company_id',true),'')::uuid)
  WITH CHECK(company_id=NULLIF(current_setting('app.company_id',true),'')::uuid);
ALTER TABLE sst.cipa_member ENABLE ROW LEVEL SECURITY;
ALTER TABLE sst.cipa_member FORCE ROW LEVEL SECURITY;
CREATE POLICY cipa_member_company_scope ON sst.cipa_member TO sst_app_runtime
  USING(company_id=NULLIF(current_setting('app.company_id',true),'')::uuid)
  WITH CHECK(company_id=NULLIF(current_setting('app.company_id',true),'')::uuid);
ALTER TABLE sst.cipa_meeting ENABLE ROW LEVEL SECURITY;
ALTER TABLE sst.cipa_meeting FORCE ROW LEVEL SECURITY;
CREATE POLICY cipa_meeting_company_scope ON sst.cipa_meeting TO sst_app_runtime
  USING(company_id=NULLIF(current_setting('app.company_id',true),'')::uuid)
  WITH CHECK(company_id=NULLIF(current_setting('app.company_id',true),'')::uuid);
ALTER TABLE sst.cipa_event ENABLE ROW LEVEL SECURITY;
ALTER TABLE sst.cipa_event FORCE ROW LEVEL SECURITY;
CREATE POLICY cipa_event_company_scope ON sst.cipa_event TO sst_app_runtime
  USING(company_id=NULLIF(current_setting('app.company_id',true),'')::uuid)
  WITH CHECK(company_id=NULLIF(current_setting('app.company_id',true),'')::uuid);
INSERT INTO sst.schema_migrations(version,description)
VALUES(10,'CIPA Web: mandato, composicao, reunioes e linha do tempo com RLS');
COMMIT;
