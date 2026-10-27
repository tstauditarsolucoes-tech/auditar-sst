-- Login ficticio somente CI. Nao aplicar em VPS ou qualquer banco com usuarios reais.
\set ON_ERROR_STOP on
\if :{?AUDITAR_INTEGRATION_CI}
\else
  SELECT 1/0 AS erro_seed_auth_apenas_ci;
\endif
DO $$
BEGIN
  IF current_database() IS DISTINCT FROM 'auditar_web_hml' THEN
    RAISE EXCEPTION 'Seed de auth bloqueada: banco diferente de CI';
  END IF;
  IF (SELECT name FROM sst.company WHERE id='10000000-0000-4000-8000-000000000001') IS DISTINCT FROM 'Empresa ficticia CI A'
    OR (SELECT name FROM sst.company WHERE id='20000000-0000-4000-8000-000000000002')<>'Empresa ficticia CI B'
    OR EXISTS (SELECT 1 FROM sst.auth_credential)
    OR EXISTS (SELECT 1 FROM sst.auth_session) THEN
    RAISE EXCEPTION 'Seed de auth exige empresas ficticias da CI e auth vazia';
  END IF;
END $$;
BEGIN;
-- O mesmo tecnico ficticio tem 2 vinculos para exercitar troca de empresa.
INSERT INTO sst.user_company_role(company_id,user_id,role)
VALUES ('20000000-0000-4000-8000-000000000002',
        '11000000-0000-4000-8000-000000000001','cliente');

INSERT INTO sst.auth_credential(user_id,password_verifier)
VALUES ('11000000-0000-4000-8000-000000000001',
'scrypt$131072$8$1$8ee14d963363a557534aaeee01e41a11$9341afbb464041474db2f3c691b19572efb22a62c5df3b0936a826982c052627bc7b7c3398738a44de51ced864541685a0f186b61f09a68cec5b2589d099d7ec');

CREATE ROLE sst_ci_auth_runner LOGIN PASSWORD 'ci-auth-synthetic-test-only-7416';
GRANT sst_auth_runtime TO sst_ci_auth_runner WITH INHERIT FALSE, SET TRUE;
COMMIT;
