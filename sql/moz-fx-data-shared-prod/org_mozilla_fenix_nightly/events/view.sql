CREATE OR REPLACE VIEW
  `moz-fx-data-shared-prod.org_mozilla_fenix_nightly.events`
AS SELECT
  * REPLACE(
    mozfun.norm.metadata(metadata) AS metadata)
FROM
  `moz-fx-data-shared-prod.org_mozilla_fenix_nightly_stable.events_v1`
