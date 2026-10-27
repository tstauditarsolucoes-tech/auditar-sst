-- SOMENTE GitHub Actions em banco novo/ficticio descartavel.
-- NAO usar em bases existentes, ambientes reais ou VPS com dados.
\set ON_ERROR_STOP on
\if :{?AUDITAR_INTEGRATION_CI}
\else
  SELECT 1/0 AS 'SEED_PROIBIDA_SEM_CHAVE_EXPLICITA_CI';
\endif
DO $$
BEGIN
  IF current_database() <> 'auditar_web_hml' THEN
    RAISE EXCEPTION 'Seed permitida somente no nome de banco de homologacao CI';
  END IF;
  IF EXISTS (SELECT 1 FROM sst.company) OR EXISTS (SELECT 1 FROM sst.app_user) THEN
    RAISE EXCEPTION 'Seed exige banco efemero vazio, sem nenhum dado existente';
  END IF;
END $$;

BEGIN;
INSERT INTO sst.company(id,name) VALUES
('10000000-0000-4000-8000-000000000001','Empresa ficticia CI A'),
('20000000-0000-4000-8000-000000000002','Empresa ficticia CI B');

INSERT INTO sst.app_user(id,display_name,email) VALUES
('11000000-0000-4000-8000-000000000001','Tecnico Ficticio CI','tecnico-ci-a@example.invalid'),
('11000000-0000-4000-8000-000000000002','Cliente Ficticio CI','cliente-ci-a@example.invalid'),
('22000000-0000-4000-8000-000000000002','Tecnico Ficticio CI B','tecnico-ci-b@example.invalid');

INSERT INTO sst.user_company_role(company_id,user_id,role) VALUES
('10000000-0000-4000-8000-000000000001','11000000-0000-4000-8000-000000000001','tecnico'),
('10000000-0000-4000-8000-000000000001','11000000-0000-4000-8000-000000000002','cliente'),
('20000000-0000-4000-8000-000000000002','22000000-0000-4000-8000-000000000002','tecnico');

-- Identidade DB efemera nao-superuser; so pode trocar para sst_app_runtime.
CREATE ROLE sst_ci_runner LOGIN PASSWORD 'ci-synthetic-test-only-not-for-deploy-9274';
GRANT sst_app_runtime TO sst_ci_runner WITH INHERIT FALSE, SET TRUE;
COMMIT;
