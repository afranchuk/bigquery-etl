CREATE OR REPLACE VIEW
  `moz-fx-data-shared-prod.org_mozilla_vrbrowser.deletion_request`
AS SELECT
  * REPLACE(
    mozfun.norm.metadata(metadata) AS metadata)
FROM
  `moz-fx-data-shared-prod.org_mozilla_vrbrowser_stable.deletion_request_v1`
