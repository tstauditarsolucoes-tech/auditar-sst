-- Private CIPA portal only. Event-sourced checklist and identified observations.
-- Requires 014; no legacy import, no deletion or rewrite of existing events.
BEGIN;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM sst.schema_migrations WHERE version=14)
    OR EXISTS (SELECT 1 FROM sst.schema_migrations WHERE version=15) THEN
    RAISE EXCEPTION 'CIPA guided participation requires version 014 and must not be reapplied';
  END IF;
END $$;
ALTER TABLE sst.cipa_portal_entry DROP CONSTRAINT cipa_portal_entry_kind_check;
ALTER TABLE sst.cipa_portal_entry ADD CONSTRAINT cipa_portal_entry_kind_check
  CHECK(kind IN ('sugestao','apoio','atualizacao','decisao','orientacao','aviso','ciencia_reuniao','acesso',
                 'checklist','observacao'));
CREATE INDEX cipa_portal_member_checklist
  ON sst.cipa_portal_entry(company_id,mandate_id,author_account_id,created_at DESC)
  WHERE kind='checklist';
INSERT INTO sst.schema_migrations(version,description)
  VALUES(15,'CIPA: checklist individual mensal e observacoes identificadas com historico');
COMMIT;
