-- NOVA base de homologacao: fotos de teste em volume privado dedicado.
-- Nao usa Drive nem altera qualquer foto/assinatura legada.
BEGIN;
DO $$
BEGIN
  IF (SELECT count(*) FROM sst.schema_migrations WHERE version BETWEEN 1 AND 6) <> 6 THEN
    RAISE EXCEPTION 'Aplicar migracoes 001..006 antes da 007';
  END IF;
  IF EXISTS(SELECT 1 FROM sst.schema_migrations WHERE version=7) THEN
    RAISE EXCEPTION 'Migracao 007 ja aplicada';
  END IF;
END $$;
ALTER TABLE sst.evidence ADD COLUMN client_request_id uuid;
CREATE UNIQUE INDEX evidence_company_request_idx
  ON sst.evidence(company_id,client_request_id)
  WHERE client_request_id IS NOT NULL;
INSERT INTO sst.schema_migrations(version,description)
VALUES (7,'Midia privada ficticia: referencia de arquivo e envio idempotente');
COMMIT;
