-- Generated via ./bqetl glean_usage generate
CREATE OR REPLACE VIEW
  `moz-fx-data-shared-prod.firefox_ios.baseline_clients_daily`
AS
SELECT
  * REPLACE ("release" AS normalized_channel)
FROM
  `moz-fx-data-shared-prod.org_mozilla_ios_firefox.baseline_clients_daily`
UNION ALL
SELECT
  * REPLACE ("beta" AS normalized_channel)
FROM
  `moz-fx-data-shared-prod.org_mozilla_ios_firefoxbeta.baseline_clients_daily`
UNION ALL
SELECT
  * REPLACE ("nightly" AS normalized_channel)
FROM
  `moz-fx-data-shared-prod.org_mozilla_ios_fennec.baseline_clients_daily`
