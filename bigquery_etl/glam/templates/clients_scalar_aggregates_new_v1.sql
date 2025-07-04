{% set aggregate_filter_clause %}
{% if filter_version %}
  LEFT JOIN
    glam_etl.{{ prefix }}__latest_versions_v1
    USING (channel)
{% endif %}
WHERE
      -- allow for builds to be slighly ahead of the current submission date, to
      -- account for a reasonable amount of clock skew
  {{ build_date_udf }}(app_build_id) < DATE_ADD(@submission_date, INTERVAL 3 day)
      -- only keep builds from the last year
  AND {{ build_date_udf }}(app_build_id) > DATE_SUB(@submission_date, INTERVAL 365 day)
  {% if filter_version %}
    AND app_version
    BETWEEN (latest_version - {{ num_versions_to_keep }} +1)
    AND latest_version
  {% endif %}
  {% endset %}
WITH filtered_date_channel AS (
  SELECT
    *
  FROM
    glam_etl.{{prefix}}__view_clients_daily_scalar_aggregates_v1
  WHERE
    submission_date = @submission_date
),
filtered_aggregates AS (
  SELECT
    submission_date,
    {{ attributes }},
    {{ user_data_attributes }},
    agg_type,
    value
  FROM
    filtered_date_channel
  CROSS JOIN
    UNNEST(scalar_aggregates)
  WHERE
    value IS NOT NULL
),
version_filtered_new AS (
  SELECT
    submission_date,
    {% for attribute in attributes_list %}
      scalar_aggs.{{ attribute }},
    {% endfor %}
    {{ user_data_attributes }},
    agg_type,
    value
  FROM
    filtered_aggregates AS scalar_aggs {{ aggregate_filter_clause }}
),
scalar_aggregates_new AS (
  SELECT
    {{ attributes }},
    {{ user_data_attributes }},
    agg_type,
    --format:off
    CASE agg_type
      WHEN 'max' THEN max(value)
      WHEN 'min' THEN min(value)
      WHEN 'count' THEN sum(value)
      WHEN 'sum' THEN sum(value)
      WHEN 'false' THEN sum(value)
      WHEN 'true' THEN sum(value)
    END AS value
    --format:on
  FROM
    version_filtered_new
  WHERE
    -- avoid overflows from very large numbers that are typically anomalies
    -- Negative values are incorrect and should not happen but were observed,
    -- probably due to some bit flips.
    value
    BETWEEN 0
    AND POW(2, 40)
  GROUP BY
    {{ attributes }},
    {{ user_data_attributes }},
    agg_type
)
SELECT
  {{ attributes }},
  ARRAY_AGG(({{ user_data_attributes }}, agg_type, value)) AS scalar_aggregates
FROM
  scalar_aggregates_new
GROUP BY
  {{ attributes }}
