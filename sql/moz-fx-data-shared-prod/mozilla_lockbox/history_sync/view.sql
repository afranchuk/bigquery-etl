CREATE OR REPLACE VIEW
  `moz-fx-data-shared-prod.mozilla_lockbox.history_sync`
AS SELECT
  * REPLACE(
    mozfun.norm.metadata(metadata) AS metadata,
    mozfun.norm.glean_ping_info(ping_info) AS ping_info)
FROM
  `moz-fx-data-shared-prod.mozilla_lockbox_stable.history_sync_v1`
