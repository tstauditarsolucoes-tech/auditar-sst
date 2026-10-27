-- CI e homologacao SOMENTE: valores totalmente ficticios, sempre ROLLBACK.
\set ON_ERROR_STOP on
BEGIN;
INSERT INTO sst.company(id,name) VALUES
  ('10000000-0000-4000-8000-000000000001','Empresa Ficticia A'),
  ('20000000-0000-4000-8000-000000000002','Empresa Ficticia B');
INSERT INTO sst.inspection(id,company_id,inspection_type,status,title) VALUES
  ('11000000-0000-4000-8000-000000000001','10000000-0000-4000-8000-000000000001','vistoria','rascunho','Exemplo A'),
  ('22000000-0000-4000-8000-000000000002','20000000-0000-4000-8000-000000000002','vistoria','rascunho','Exemplo B');
INSERT INTO sst.non_conformity(company_id,inspection_id,description,probability,severity) VALUES
  ('10000000-0000-4000-8000-000000000001','11000000-0000-4000-8000-000000000001','Extintor ficticio A',3,4),
  ('20000000-0000-4000-8000-000000000002','22000000-0000-4000-8000-000000000002','Protecao ficticia B',4,5);

-- Teste no role NAO SUPERUSER e NAO LOGIN. Nunca simular isolamento usando owner do banco.
SET ROLE sst_app_runtime;
DO $$
DECLARE cnt integer;
BEGIN
  SELECT count(*) INTO cnt FROM sst.inspection;
  IF cnt <> 0 THEN RAISE EXCEPTION 'RLS falhou: sem empresa retornou % linhas', cnt; END IF;
END $$;

SET LOCAL app.company_id = '10000000-0000-4000-8000-000000000001';
DO $$
DECLARE cnt integer;
BEGIN
  SELECT count(*) INTO cnt FROM sst.company;
  IF cnt <> 1 THEN RAISE EXCEPTION 'RLS company retornou %', cnt; END IF;
  SELECT count(*) INTO cnt FROM sst.inspection;
  IF cnt <> 1 THEN RAISE EXCEPTION 'RLS inspection retornou %', cnt; END IF;
  SELECT count(*) INTO cnt FROM sst.non_conformity;
  IF cnt <> 1 THEN RAISE EXCEPTION 'RLS NC retornou %', cnt; END IF;
END $$;

-- Escrita na empresa B precisa ser rejeitada pelo banco.
DO $$
BEGIN
  BEGIN
    INSERT INTO sst.inspection(company_id,inspection_type,title)
    VALUES ('20000000-0000-4000-8000-000000000002','vistoria','Escrita indevida B');
    RAISE EXCEPTION 'ERRO: banco aceitou escrita entre empresas';
  EXCEPTION WHEN insufficient_privilege THEN
    NULL; -- violacao de row-level security como esperado
  END;
END $$;

-- Registro A nao pode usar uma vistoria da empresa B mesmo se o backend errar o ID.
DO $$
BEGIN
  BEGIN
    INSERT INTO sst.non_conformity(company_id,inspection_id,description,probability,severity)
    VALUES ('10000000-0000-4000-8000-000000000001',
            '22000000-0000-4000-8000-000000000002','NC cruzada',3,3);
    RAISE EXCEPTION 'ERRO: FK aceitou registro cruzado';
  EXCEPTION WHEN foreign_key_violation THEN
    NULL;
  END;
END $$;

-- Mesmo com o role runtime, as contas globais de usuarios NAO estao abertas.
DO $$
BEGIN
  BEGIN
    PERFORM id FROM sst.app_user;
    RAISE EXCEPTION 'ERRO: role runtime leu usuarios';
  EXCEPTION WHEN insufficient_privilege THEN
    NULL;
  END;
END $$;
RESET ROLE;
ROLLBACK;
