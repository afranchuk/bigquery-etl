SELECT
  DATE(submission_timestamp) AS submission_date,
  client_info.client_id AS client_id,
  sample_id,
  COUNT(*) AS n_metrics_ping,
  1 AS days_sent_metrics_ping_bits,
FROM
  `org_mozilla_firefoxreality.metrics` AS m
WHERE
  DATE(submission_timestamp) = @submission_date
GROUP BY
  submission_date,
  client_id,
  sample_id
