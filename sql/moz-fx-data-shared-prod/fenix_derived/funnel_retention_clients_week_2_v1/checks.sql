
#fail
WITH min_row_count AS (
  SELECT
    COUNT(*) AS total_rows
  FROM
    `moz-fx-data-shared-prod.fenix_derived.funnel_retention_clients_week_2_v1`
  WHERE
    submission_date = @submission_date
)
SELECT
  IF(
    (SELECT COUNTIF(total_rows < 1) FROM min_row_count) > 0,
    ERROR(
      CONCAT(
        "Min Row Count Error: ",
        (SELECT total_rows FROM min_row_count),
        " rows found, expected more than 1 rows"
      )
    ),
    NULL
  );

#fail
SELECT
  IF(
    DATE_DIFF(submission_date, first_seen_date, DAY) <> 13,
    ERROR(
      "Day difference between submission_date and first_seen_date is not equal to 13 as expected"
    ),
    NULL
  )
FROM
  `moz-fx-data-shared-prod.fenix_derived.funnel_retention_clients_week_2_v1`
WHERE
  submission_date = @submission_date;
