CREATE OR REPLACE VIEW
  `moz-fx-data-shared-prod.org_mozilla_ios_firefoxbeta.deletion_request`
AS SELECT
  * REPLACE(
    mozfun.norm.metadata(metadata) AS metadata)
FROM
  `moz-fx-data-shared-prod.org_mozilla_ios_firefoxbeta_stable.deletion_request_v1`
