ASSERT(
  (
    SELECT
      COUNT(*)
    FROM
      `moz-fx-data-marketing-prod.ga_derived.downloads_with_attribution_v2`
    WHERE
      download_date = @download_date
  ) > 250000
)
AS
  'ETL Data Check Failed: Table moz-fx-data-marketing-prod.ga_derived.downloads_with_attribution_v2 contains less than 250,000 rows for date: .'
