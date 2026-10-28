-- New private server only. No legacy import, no change to staff roles or cookies.
BEGIN;
DO $$ BEGIN
  IF (SELECT count(*) FROM sst.schema_migrations WHERE version BETWEEN 1 AND 13) <> 13
    OR EXISTS(SELECT 1 FROM sst.schema_migrations WHERE version=14) THEN
    RAISE EXCEPTION 'Portal CIPA requires migrations 001-013 and must not be reapplied';
  END IF;
  CREATE ROLE sst_cipa_runtime NOLOGIN;
END $$;
GRANT USAGE ON SCHEMA sst TO sst_cipa_runtime;
GRANT sst_cipa_runtime TO sst_app_runtime WITH INHERIT FALSE, SET TRUE;
ALTER TABLE sst.cipa_member ADD UNIQUE(company_id,mandate_id,id);
ALTER TABLE sst.cipa_meeting ADD UNIQUE(company_id,mandate_id,id);

CREATE TABLE sst.cipa_portal_account (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id uuid NOT NULL REFERENCES sst.company(id),
  display_name varchar(180) NOT NULL,
  email varchar(254) NOT NULL CHECK(email=lower(email)),
  password_verifier text NOT NULL,
  must_change_password boolean NOT NULL DEFAULT true,
  active boolean NOT NULL DEFAULT true,
  credential_changed_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  created_by uuid NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(company_id,id), UNIQUE(company_id,email),
  FOREIGN KEY(company_id,created_by) REFERENCES sst.user_company_role(company_id,user_id)
);
CREATE TABLE sst.cipa_portal_grant (
  company_id uuid NOT NULL,
  mandate_id uuid NOT NULL,
  account_id uuid NOT NULL,
  member_id uuid NOT NULL,
  active boolean NOT NULL DEFAULT true,
  PRIMARY KEY(company_id,mandate_id,account_id),
  UNIQUE(company_id,member_id),
  FOREIGN KEY(company_id,account_id) REFERENCES sst.cipa_portal_account(company_id,id),
  FOREIGN KEY(company_id,mandate_id) REFERENCES sst.cipa_mandate(company_id,id),
  FOREIGN KEY(company_id,mandate_id,member_id) REFERENCES sst.cipa_member(company_id,mandate_id,id)
);
CREATE TABLE sst.cipa_portal_session (
  token_hash char(64) PRIMARY KEY CHECK(token_hash ~ '^[0-9a-f]{64}$'),
  company_id uuid NOT NULL,
  account_id uuid NOT NULL,
  issued_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  expires_at timestamptz NOT NULL DEFAULT now()+interval '2 hours',
  revoked_at timestamptz,
  FOREIGN KEY(company_id,account_id) REFERENCES sst.cipa_portal_account(company_id,id)
);
CREATE TABLE sst.cipa_portal_action (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id uuid NOT NULL,
  mandate_id uuid NOT NULL,
  assigned_to uuid NOT NULL,
  title varchar(200) NOT NULL CHECK(length(btrim(title))>0),
  description varchar(2000) NOT NULL DEFAULT '',
  due_on date NOT NULL,
  priority varchar(15) NOT NULL CHECK(priority IN ('baixa','media','alta','critica')),
  status varchar(25) NOT NULL DEFAULT 'aberta' CHECK(status IN ('aberta','andamento','aguardando_validacao','concluida')),
  revision integer NOT NULL DEFAULT 1,
  client_request_id uuid NOT NULL,
  request_fingerprint char(64) NOT NULL,
  created_by uuid NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(company_id,id), UNIQUE(company_id,mandate_id,id), UNIQUE(company_id,client_request_id),
  FOREIGN KEY(company_id,mandate_id,assigned_to) REFERENCES sst.cipa_portal_grant(company_id,mandate_id,account_id),
  FOREIGN KEY(company_id,created_by) REFERENCES sst.user_company_role(company_id,user_id)
);
CREATE TABLE sst.cipa_portal_entry (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id uuid NOT NULL,
  mandate_id uuid NOT NULL,
  action_id uuid,
  meeting_id uuid,
  author_account_id uuid,
  author_staff_id uuid,
  kind varchar(30) NOT NULL CHECK(kind IN ('sugestao','apoio','atualizacao','decisao','orientacao','aviso','ciencia_reuniao','acesso')),
  message varchar(2000) NOT NULL CHECK(length(btrim(message))>0),
  client_request_id uuid NOT NULL,
  request_fingerprint char(64) NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  CHECK((author_account_id IS NULL) <> (author_staff_id IS NULL)),
  UNIQUE(company_id,id), UNIQUE(company_id,client_request_id),
  FOREIGN KEY(company_id,mandate_id) REFERENCES sst.cipa_mandate(company_id,id),
  FOREIGN KEY(company_id,mandate_id,action_id) REFERENCES sst.cipa_portal_action(company_id,mandate_id,id),
  FOREIGN KEY(company_id,mandate_id,meeting_id) REFERENCES sst.cipa_meeting(company_id,mandate_id,id),
  FOREIGN KEY(company_id,author_account_id) REFERENCES sst.cipa_portal_account(company_id,id),
  FOREIGN KEY(company_id,author_staff_id) REFERENCES sst.user_company_role(company_id,user_id)
);
CREATE INDEX cipa_portal_action_due ON sst.cipa_portal_action(company_id,assigned_to,due_on);
CREATE INDEX cipa_portal_entry_mandate ON sst.cipa_portal_entry(company_id,mandate_id,created_at DESC);
CREATE INDEX cipa_portal_session_account ON sst.cipa_portal_session(company_id,account_id);
GRANT SELECT,INSERT,UPDATE ON sst.cipa_portal_account,sst.cipa_portal_grant,sst.cipa_portal_action TO sst_app_runtime;
GRANT SELECT,INSERT ON sst.cipa_portal_entry TO sst_app_runtime;
GRANT UPDATE ON sst.cipa_portal_session TO sst_app_runtime;
GRANT SELECT(company_id,account_id,token_hash,revoked_at) ON sst.cipa_portal_session TO sst_app_runtime;
GRANT SELECT,UPDATE ON sst.cipa_portal_account TO sst_auth_runtime;
GRANT SELECT ON sst.cipa_portal_grant TO sst_auth_runtime;
GRANT SELECT,INSERT,UPDATE ON sst.cipa_portal_session TO sst_auth_runtime;
GRANT SELECT ON sst.cipa_portal_grant,sst.cipa_portal_action,sst.cipa_mandate,sst.cipa_meeting TO sst_cipa_runtime;
GRANT UPDATE(status,revision,updated_at) ON sst.cipa_portal_action TO sst_cipa_runtime;
GRANT SELECT,INSERT ON sst.cipa_portal_entry TO sst_cipa_runtime;

DO $$ DECLARE t text; BEGIN
  FOREACH t IN ARRAY ARRAY['cipa_portal_account','cipa_portal_grant','cipa_portal_session','cipa_portal_action','cipa_portal_entry'] LOOP
    EXECUTE format('ALTER TABLE sst.%I ENABLE ROW LEVEL SECURITY',t);
    EXECUTE format('ALTER TABLE sst.%I FORCE ROW LEVEL SECURITY',t);
    EXECUTE format('CREATE POLICY staff_company ON sst.%I TO sst_app_runtime USING (company_id=NULLIF(current_setting(''app.company_id'',true),'''')::uuid) WITH CHECK (company_id=NULLIF(current_setting(''app.company_id'',true),'''')::uuid)',t);
  END LOOP;
  FOREACH t IN ARRAY ARRAY['cipa_portal_account','cipa_portal_grant','cipa_portal_session'] LOOP
    EXECUTE format('CREATE POLICY private_auth ON sst.%I TO sst_auth_runtime USING(true) WITH CHECK(true)',t);
  END LOOP;
END $$;
CREATE POLICY member_grants ON sst.cipa_portal_grant TO sst_cipa_runtime
 USING(company_id=NULLIF(current_setting('app.company_id',true),'')::uuid AND
       account_id=NULLIF(current_setting('app.cipa_account_id',true),'')::uuid AND active);
CREATE POLICY member_mandates ON sst.cipa_mandate TO sst_cipa_runtime
 USING(EXISTS(SELECT 1 FROM sst.cipa_portal_grant g WHERE g.company_id=cipa_mandate.company_id AND g.mandate_id=cipa_mandate.id));
CREATE POLICY member_meetings ON sst.cipa_meeting TO sst_cipa_runtime
 USING(EXISTS(SELECT 1 FROM sst.cipa_portal_grant g WHERE g.company_id=cipa_meeting.company_id AND g.mandate_id=cipa_meeting.mandate_id));
CREATE POLICY member_actions ON sst.cipa_portal_action TO sst_cipa_runtime
 USING(company_id=NULLIF(current_setting('app.company_id',true),'')::uuid AND
       assigned_to=NULLIF(current_setting('app.cipa_account_id',true),'')::uuid AND
       EXISTS(SELECT 1 FROM sst.cipa_portal_grant g WHERE g.company_id=cipa_portal_action.company_id AND g.mandate_id=cipa_portal_action.mandate_id));
CREATE POLICY member_read_entries ON sst.cipa_portal_entry FOR SELECT TO sst_cipa_runtime
 USING(EXISTS(SELECT 1 FROM sst.cipa_portal_grant g WHERE g.company_id=cipa_portal_entry.company_id AND g.mandate_id=cipa_portal_entry.mandate_id) AND
   (kind='aviso' OR author_account_id=NULLIF(current_setting('app.cipa_account_id',true),'')::uuid OR
    EXISTS(SELECT 1 FROM sst.cipa_portal_action a WHERE a.company_id=cipa_portal_entry.company_id AND a.id=cipa_portal_entry.action_id)));
CREATE POLICY member_write_entries ON sst.cipa_portal_entry FOR INSERT TO sst_cipa_runtime
 WITH CHECK(author_account_id=NULLIF(current_setting('app.cipa_account_id',true),'')::uuid AND author_staff_id IS NULL AND
   kind IN ('sugestao','apoio','atualizacao','ciencia_reuniao') AND
   EXISTS(SELECT 1 FROM sst.cipa_portal_grant g WHERE g.company_id=cipa_portal_entry.company_id AND g.mandate_id=cipa_portal_entry.mandate_id) AND
   (action_id IS NULL OR EXISTS(SELECT 1 FROM sst.cipa_portal_action a WHERE a.company_id=cipa_portal_entry.company_id AND a.id=cipa_portal_entry.action_id)));
INSERT INTO sst.schema_migrations(version,description) VALUES(14,'Portal individual CIPA: credenciais separadas, RLS, acoes e participacao');
COMMIT;
