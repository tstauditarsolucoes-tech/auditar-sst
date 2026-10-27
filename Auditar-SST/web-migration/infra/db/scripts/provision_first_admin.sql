-- Invocado SOMENTE por scripts/provision-first-admin.sh em banco SST novo.
\set ON_ERROR_STOP on
BEGIN;
DO $$
BEGIN
  IF current_database() <> 'auditar_web_hml'
     OR (SELECT count(*) FROM sst.schema_migrations WHERE version IN (1,2,3)) <> 3
     OR EXISTS(SELECT 1 FROM sst.company)
     OR EXISTS(SELECT 1 FROM sst.app_user)
     OR EXISTS(SELECT 1 FROM sst.auth_credential) THEN
    RAISE EXCEPTION 'Provisionamento exige banco de homologacao SST vazio com migracoes 001-003';
  END IF;
END $$;
INSERT INTO sst.company(name) VALUES (:'company_name') RETURNING id AS sst_company_id \gset
INSERT INTO sst.app_user(display_name,email)
VALUES (:'display_name',:'email') RETURNING id AS sst_user_id \gset
INSERT INTO sst.user_company_role(company_id,user_id,role)
VALUES (:'sst_company_id'::uuid,:'sst_user_id'::uuid,'adm');
INSERT INTO sst.auth_credential(user_id,password_verifier)
VALUES (:'sst_user_id'::uuid,:'verifier');
COMMIT;
