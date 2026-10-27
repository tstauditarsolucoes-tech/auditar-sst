-- 012: lista de presenca DECLARADA, SOMENTE em banco NOVO de homologacao.
-- Nao migrar nomes reais nem utilizar como assinatura ou comprovante NR.
BEGIN;
DO $$
BEGIN
 IF (SELECT count(*) FROM sst.schema_migrations WHERE version BETWEEN 1 AND 11) <> 11
   THEN RAISE EXCEPTION 'Aplicar migracoes SST 001 a 011 antes da 012'; END IF;
 IF EXISTS(SELECT 1 FROM sst.schema_migrations WHERE version=12)
   THEN RAISE EXCEPTION 'Migracao 012 ja aplicada'; END IF;
END $$;
CREATE TABLE sst.training_attendance (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 company_id uuid NOT NULL REFERENCES sst.company(id),
 training_id uuid NOT NULL,
 display_name varchar(180) NOT NULL CHECK(length(btrim(display_name))>0),
 presence varchar(20) NOT NULL DEFAULT 'declarada'
   CHECK(presence IN ('declarada','nao_confirmada')),
 note varchar(500) NOT NULL DEFAULT '',
 created_by uuid NOT NULL,
 client_request_id uuid NOT NULL,
 request_fingerprint char(64) NOT NULL CHECK(request_fingerprint ~ '^[0-9a-f]{64}$'),
 created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(company_id,id),
 UNIQUE(company_id,client_request_id),
 FOREIGN KEY(company_id,training_id) REFERENCES sst.training_session(company_id,id),
 FOREIGN KEY(company_id,created_by) REFERENCES sst.user_company_role(company_id,user_id)
);
CREATE INDEX training_attendance_scope_idx
 ON sst.training_attendance(company_id,training_id,created_at,id);
GRANT SELECT,INSERT ON sst.training_attendance TO sst_app_runtime;
ALTER TABLE sst.training_attendance ENABLE ROW LEVEL SECURITY;
ALTER TABLE sst.training_attendance FORCE ROW LEVEL SECURITY;
CREATE POLICY training_attendance_company_scope ON sst.training_attendance TO sst_app_runtime
 USING(company_id=NULLIF(current_setting('app.company_id',true),'')::uuid)
 WITH CHECK(company_id=NULLIF(current_setting('app.company_id',true),'')::uuid);
INSERT INTO sst.schema_migrations(version,description)
VALUES(12,'Participantes declarados de treinamento, sem assinatura, tenant RLS');
COMMIT;
