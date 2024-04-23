# Generated via https://github.com/mozilla/bigquery-etl/blob/main/bigquery_etl/query_scheduling/generate_airflow_dags.py

from airflow import DAG
from airflow.sensors.external_task import ExternalTaskMarker
from airflow.sensors.external_task import ExternalTaskSensor
from airflow.utils.task_group import TaskGroup
import datetime
from operators.gcp_container_operator import GKEPodOperator
from utils.constants import ALLOWED_STATES, FAILED_STATES
from utils.gcp import bigquery_etl_query, bigquery_dq_check

docs = """
### bqetl_fivetran_google_ads

Built from bigquery-etl repo, [`dags/bqetl_fivetran_google_ads.py`](https://github.com/mozilla/bigquery-etl/blob/generated-sql/dags/bqetl_fivetran_google_ads.py)

#### Description

Queries for Google Ads data coming from Fivetran. Fivetran updates these tables every hour.
#### Owner

frank@mozilla.com

#### Tags

* impact/tier_2
* repo/bigquery-etl
"""


default_args = {
    "owner": "frank@mozilla.com",
    "start_date": datetime.datetime(2023, 1, 1, 0, 0),
    "end_date": None,
    "email": ["telemetry-alerts@mozilla.com", "frank@mozilla.com"],
    "depends_on_past": False,
    "retry_delay": datetime.timedelta(seconds=1800),
    "email_on_failure": True,
    "email_on_retry": True,
    "retries": 2,
}

tags = ["impact/tier_2", "repo/bigquery-etl"]

with DAG(
    "bqetl_fivetran_google_ads",
    default_args=default_args,
    schedule_interval="0 2 * * *",
    doc_md=docs,
    tags=tags,
) as dag:

    checks__fail_google_ads_derived__ad_groups__v1 = bigquery_dq_check(
        task_id="checks__fail_google_ads_derived__ad_groups__v1",
        source_table="ad_groups_v1",
        dataset_id="google_ads_derived",
        project_id="moz-fx-data-shared-prod",
        is_dq_check_fail=True,
        owner="frank@mozilla.com",
        email=["frank@mozilla.com", "telemetry-alerts@mozilla.com"],
        depends_on_past=False,
        task_concurrency=1,
        retries=0,
    )

    checks__fail_google_ads_derived__campaigns__v1 = bigquery_dq_check(
        task_id="checks__fail_google_ads_derived__campaigns__v1",
        source_table="campaigns_v1",
        dataset_id="google_ads_derived",
        project_id="moz-fx-data-shared-prod",
        is_dq_check_fail=True,
        owner="frank@mozilla.com",
        email=["frank@mozilla.com", "telemetry-alerts@mozilla.com"],
        depends_on_past=False,
        task_concurrency=1,
        retries=0,
    )

    google_ads_derived__accounts__v1 = bigquery_etl_query(
        task_id="google_ads_derived__accounts__v1",
        destination_table="accounts_v1",
        dataset_id="google_ads_derived",
        project_id="moz-fx-data-shared-prod",
        owner="lschiestl@mozilla.com",
        email=[
            "frank@mozilla.com",
            "lschiestl@mozilla.com",
            "telemetry-alerts@mozilla.com",
        ],
        date_partition_parameter=None,
        depends_on_past=False,
        task_concurrency=1,
    )

    google_ads_derived__ad_groups__v1 = bigquery_etl_query(
        task_id="google_ads_derived__ad_groups__v1",
        destination_table="ad_groups_v1",
        dataset_id="google_ads_derived",
        project_id="moz-fx-data-shared-prod",
        owner="frank@mozilla.com",
        email=["frank@mozilla.com", "telemetry-alerts@mozilla.com"],
        date_partition_parameter=None,
        depends_on_past=False,
        task_concurrency=1,
    )

    google_ads_derived__campaign_conversions_by_date__v1 = bigquery_etl_query(
        task_id="google_ads_derived__campaign_conversions_by_date__v1",
        destination_table="campaign_conversions_by_date_v1",
        dataset_id="google_ads_derived",
        project_id="moz-fx-data-shared-prod",
        owner="frank@mozilla.com",
        email=["frank@mozilla.com", "telemetry-alerts@mozilla.com"],
        date_partition_parameter=None,
        depends_on_past=False,
        task_concurrency=1,
    )

    google_ads_derived__campaign_names_map__v1 = bigquery_etl_query(
        task_id="google_ads_derived__campaign_names_map__v1",
        destination_table="campaign_names_map_v1",
        dataset_id="google_ads_derived",
        project_id="moz-fx-data-shared-prod",
        owner="frank@mozilla.com",
        email=["frank@mozilla.com", "telemetry-alerts@mozilla.com"],
        date_partition_parameter=None,
        depends_on_past=False,
        task_concurrency=1,
    )

    with TaskGroup(
        "google_ads_derived__campaign_names_map__v1_external",
    ) as google_ads_derived__campaign_names_map__v1_external:
        ExternalTaskMarker(
            task_id="bqetl_campaign_cost_breakdowns__wait_for_google_ads_derived__campaign_names_map__v1",
            external_dag_id="bqetl_campaign_cost_breakdowns",
            external_task_id="wait_for_google_ads_derived__campaign_names_map__v1",
            execution_date="{{ (execution_date - macros.timedelta(days=-1, seconds=82800)).isoformat() }}",
        )

        google_ads_derived__campaign_names_map__v1_external.set_upstream(
            google_ads_derived__campaign_names_map__v1
        )

    google_ads_derived__campaigns__v1 = bigquery_etl_query(
        task_id="google_ads_derived__campaigns__v1",
        destination_table="campaigns_v1",
        dataset_id="google_ads_derived",
        project_id="moz-fx-data-shared-prod",
        owner="frank@mozilla.com",
        email=["frank@mozilla.com", "telemetry-alerts@mozilla.com"],
        date_partition_parameter=None,
        depends_on_past=False,
        task_concurrency=1,
    )

    google_ads_derived__daily_ad_group_stats__v1 = bigquery_etl_query(
        task_id="google_ads_derived__daily_ad_group_stats__v1",
        destination_table="daily_ad_group_stats_v1",
        dataset_id="google_ads_derived",
        project_id="moz-fx-data-shared-prod",
        owner="frank@mozilla.com",
        email=["frank@mozilla.com", "telemetry-alerts@mozilla.com"],
        date_partition_parameter=None,
        depends_on_past=False,
        task_concurrency=1,
    )

    google_ads_derived__daily_campaign_stats__v1 = bigquery_etl_query(
        task_id="google_ads_derived__daily_campaign_stats__v1",
        destination_table="daily_campaign_stats_v1",
        dataset_id="google_ads_derived",
        project_id="moz-fx-data-shared-prod",
        owner="frank@mozilla.com",
        email=["frank@mozilla.com", "telemetry-alerts@mozilla.com"],
        date_partition_parameter=None,
        depends_on_past=False,
        task_concurrency=1,
    )

    checks__fail_google_ads_derived__ad_groups__v1.set_upstream(
        google_ads_derived__ad_groups__v1
    )

    checks__fail_google_ads_derived__campaigns__v1.set_upstream(
        google_ads_derived__campaigns__v1
    )

    google_ads_derived__ad_groups__v1.set_upstream(
        checks__fail_google_ads_derived__campaigns__v1
    )

    google_ads_derived__campaign_conversions_by_date__v1.set_upstream(
        google_ads_derived__campaign_names_map__v1
    )

    google_ads_derived__campaign_names_map__v1.set_upstream(
        google_ads_derived__accounts__v1
    )

    google_ads_derived__campaigns__v1.set_upstream(google_ads_derived__accounts__v1)
