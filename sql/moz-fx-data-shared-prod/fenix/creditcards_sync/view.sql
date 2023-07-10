-- Generated via ./bqetl generate glean_usage
CREATE OR REPLACE VIEW
  `moz-fx-data-shared-prod.fenix.creditcards_sync`
AS
SELECT
  "org_mozilla_firefox" AS normalized_app_id,
  mozfun.norm.fenix_app_info(
    "org_mozilla_firefox",
    client_info.app_build
  ).channel AS normalized_channel,
  additional_properties,
  client_info,
  document_id,
  events,
  metadata,
  metrics,
  normalized_app_name,
  normalized_country_code,
  normalized_os,
  normalized_os_version,
  ping_info,
  sample_id,
  submission_timestamp
FROM
  `moz-fx-data-shared-prod.org_mozilla_firefox.creditcards_sync`
UNION ALL
SELECT
  "org_mozilla_firefox_beta" AS normalized_app_id,
  mozfun.norm.fenix_app_info(
    "org_mozilla_firefox_beta",
    client_info.app_build
  ).channel AS normalized_channel,
  additional_properties,
  client_info,
  document_id,
  events,
  metadata,
  STRUCT(
    metrics.counter,
    metrics.datetime,
    CAST(NULL AS ARRAY<STRUCT<key STRING, value STRING>>) AS jwe,
    metrics.labeled_counter,
    CAST(
      NULL
      AS
        ARRAY<
          STRUCT<
            key STRING,
            value ARRAY<STRUCT<key STRING, value STRUCT<denominator INTEGER, numerator INTEGER>>>
          >
        >
    ) AS labeled_rate,
    metrics.labeled_string,
    metrics.string,
    CAST(NULL AS ARRAY<STRUCT<key STRING, value STRING>>) AS url,
    CAST(NULL AS ARRAY<STRUCT<key STRING, value STRING>>) AS text
  ) AS metrics,
  normalized_app_name,
  normalized_country_code,
  normalized_os,
  normalized_os_version,
  ping_info,
  sample_id,
  submission_timestamp
FROM
  `moz-fx-data-shared-prod.org_mozilla_firefox_beta.creditcards_sync`
UNION ALL
SELECT
  "org_mozilla_fenix" AS normalized_app_id,
  mozfun.norm.fenix_app_info(
    "org_mozilla_fenix",
    client_info.app_build
  ).channel AS normalized_channel,
  additional_properties,
  client_info,
  document_id,
  events,
  metadata,
  STRUCT(
    metrics.counter,
    metrics.datetime,
    CAST(NULL AS ARRAY<STRUCT<key STRING, value STRING>>) AS jwe,
    metrics.labeled_counter,
    CAST(
      NULL
      AS
        ARRAY<
          STRUCT<
            key STRING,
            value ARRAY<STRUCT<key STRING, value STRUCT<denominator INTEGER, numerator INTEGER>>>
          >
        >
    ) AS labeled_rate,
    metrics.labeled_string,
    metrics.string,
    CAST(NULL AS ARRAY<STRUCT<key STRING, value STRING>>) AS url,
    CAST(NULL AS ARRAY<STRUCT<key STRING, value STRING>>) AS text
  ) AS metrics,
  normalized_app_name,
  normalized_country_code,
  normalized_os,
  normalized_os_version,
  ping_info,
  sample_id,
  submission_timestamp
FROM
  `moz-fx-data-shared-prod.org_mozilla_fenix.creditcards_sync`
UNION ALL
SELECT
  "org_mozilla_fenix_nightly" AS normalized_app_id,
  mozfun.norm.fenix_app_info(
    "org_mozilla_fenix_nightly",
    client_info.app_build
  ).channel AS normalized_channel,
  additional_properties,
  client_info,
  document_id,
  events,
  metadata,
  metrics,
  normalized_app_name,
  normalized_country_code,
  normalized_os,
  normalized_os_version,
  ping_info,
  sample_id,
  submission_timestamp
FROM
  `moz-fx-data-shared-prod.org_mozilla_fenix_nightly.creditcards_sync`
UNION ALL
SELECT
  "org_mozilla_fennec_aurora" AS normalized_app_id,
  mozfun.norm.fenix_app_info(
    "org_mozilla_fennec_aurora",
    client_info.app_build
  ).channel AS normalized_channel,
  additional_properties,
  client_info,
  document_id,
  events,
  metadata,
  metrics,
  normalized_app_name,
  normalized_country_code,
  normalized_os,
  normalized_os_version,
  ping_info,
  sample_id,
  submission_timestamp
FROM
  `moz-fx-data-shared-prod.org_mozilla_fennec_aurora.creditcards_sync`
