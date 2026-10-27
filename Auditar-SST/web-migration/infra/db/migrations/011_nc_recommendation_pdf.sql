-- Novo campo opcional de orientacao tecnica para NC de vistoria na HOMOLOGACAO.
-- Nunca executar em banco de producao nem na Central Online atual.
BEGIN;
DO $$
BEGIN
 IF (SELECT count(*) FROM sst.schema_migrations WHERE version BETWEEN 1 AND 10)<>10 THEN
   RAISE EXCEPTION 'Aplicar migracoes 001 a 010 primeiro';
 END IF;
 IF EXISTS(SELECT 1 FROM sst.schema_migrations WHERE version=11) THEN
   RAISE EXCEPTION 'Migracao 011 ja aplicada';
 END IF;
END $$;
ALTER TABLE sst.non_conformity
  ADD COLUMN recommendation varchar(1600) NOT NULL DEFAULT '';
INSERT INTO sst.schema_migrations(version,description)
VALUES(11,'NC Web: recomendacao tecnica separada da descricao para PDF piloto');
COMMIT;
