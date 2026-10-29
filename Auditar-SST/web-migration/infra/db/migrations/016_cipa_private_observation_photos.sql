-- CIPA member image evidence: staging-only, isolated from legacy Drive/NC files.
BEGIN;
DO $$ BEGIN
  IF NOT EXISTS(SELECT 1 FROM sst.schema_migrations WHERE version=15)
     OR EXISTS(SELECT 1 FROM sst.schema_migrations WHERE version=16) THEN
    RAISE EXCEPTION 'CIPA observation photo migration requires 015 and is not repeatable';
  END IF;
END $$;
CREATE TABLE sst.cipa_portal_photo (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id uuid NOT NULL,
  mandate_id uuid NOT NULL,
  entry_id uuid NOT NULL,
  author_account_id uuid NOT NULL,
  object_key text NOT NULL,
  mime_type varchar(30) NOT NULL CHECK(mime_type IN ('image/jpeg','image/png','image/webp')),
  sha256 char(64) NOT NULL CHECK(sha256 ~ '^[0-9a-f]{64}$'),
  size_bytes integer NOT NULL CHECK(size_bytes BETWEEN 1 AND 2097152),
  client_request_id uuid NOT NULL,
  request_fingerprint char(64) NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(company_id,id),
  UNIQUE(company_id,entry_id),
  UNIQUE(company_id,client_request_id),
  FOREIGN KEY(company_id,mandate_id) REFERENCES sst.cipa_mandate(company_id,id),
  FOREIGN KEY(company_id,entry_id) REFERENCES sst.cipa_portal_entry(company_id,id),
  FOREIGN KEY(company_id,author_account_id) REFERENCES sst.cipa_portal_account(company_id,id),
  FOREIGN KEY(company_id,mandate_id,author_account_id)
    REFERENCES sst.cipa_portal_grant(company_id,mandate_id,account_id)
);
CREATE INDEX cipa_portal_photo_mandate ON sst.cipa_portal_photo(company_id,mandate_id,created_at DESC);
GRANT SELECT,INSERT ON sst.cipa_portal_photo TO sst_app_runtime,sst_cipa_runtime;
ALTER TABLE sst.cipa_portal_photo ENABLE ROW LEVEL SECURITY;
ALTER TABLE sst.cipa_portal_photo FORCE ROW LEVEL SECURITY;
CREATE POLICY staff_photo_scope ON sst.cipa_portal_photo TO sst_app_runtime
  USING(company_id=NULLIF(current_setting('app.company_id',true),'')::uuid)
  WITH CHECK(company_id=NULLIF(current_setting('app.company_id',true),'')::uuid);
CREATE POLICY member_photo_scope ON sst.cipa_portal_photo TO sst_cipa_runtime
  USING(company_id=NULLIF(current_setting('app.company_id',true),'')::uuid AND
        author_account_id=NULLIF(current_setting('app.cipa_account_id',true),'')::uuid AND
        EXISTS(SELECT 1 FROM sst.cipa_portal_grant g WHERE g.company_id=cipa_portal_photo.company_id
          AND g.mandate_id=cipa_portal_photo.mandate_id AND g.account_id=cipa_portal_photo.author_account_id))
  WITH CHECK(company_id=NULLIF(current_setting('app.company_id',true),'')::uuid AND
        author_account_id=NULLIF(current_setting('app.cipa_account_id',true),'')::uuid AND
        EXISTS(SELECT 1 FROM sst.cipa_portal_grant g WHERE g.company_id=cipa_portal_photo.company_id
          AND g.mandate_id=cipa_portal_photo.mandate_id AND g.account_id=cipa_portal_photo.author_account_id));
INSERT INTO sst.schema_migrations(version,description) VALUES(16,'CIPA: photos of identified observations in private tenant-scoped staging volume');
COMMIT;
