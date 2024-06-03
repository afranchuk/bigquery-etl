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
### bqetl_mobile_search

Built from bigquery-etl repo, [`dags/bqetl_mobile_search.py`](https://github.com/mozilla/bigquery-etl/blob/generated-sql/dags/bqetl_mobile_search.py)

#### Owner

anicholson@mozilla.com

#### Tags

* impact/tier_1
* repo/bigquery-etl
"""


default_args = {
    "owner": "anicholson@mozilla.com",
    "start_date": datetime.datetime(2019, 7, 25, 0, 0),
    "end_date": None,
    "email": [
        "telemetry-alerts@mozilla.com",
        "anicholson@mozilla.com",
        "akomar@mozilla.com",
        "cmorales@mozilla.com",
    ],
    "depends_on_past": False,
    "retry_delay": datetime.timedelta(seconds=300),
    "email_on_failure": True,
    "email_on_retry": True,
    "retries": 1,
}

tags = ["impact/tier_1", "repo/bigquery-etl"]

with DAG(
    "bqetl_mobile_search",
    default_args=default_args,
    schedule_interval="0 2 * * *",
    doc_md=docs,
    tags=tags,
) as dag:

    search_derived__mobile_search_aggregates__v1 = bigquery_etl_query(
        task_id="search_derived__mobile_search_aggregates__v1",
        destination_table="mobile_search_aggregates_v1",
        dataset_id="search_derived",
        project_id="moz-fx-data-shared-prod",
        owner="akomar@mozilla.com",
        email=[
            "akomar@mozilla.com",
            "anicholson@mozilla.com",
            "cmorales@mozilla.com",
            "telemetry-alerts@mozilla.com",
        ],
        date_partition_parameter="submission_date",
        depends_on_past=False,
    )

    search_derived__mobile_search_clients_last_seen__v1 = bigquery_etl_query(
        task_id="search_derived__mobile_search_clients_last_seen__v1",
        destination_table="mobile_search_clients_last_seen_v1",
        dataset_id="search_derived",
        project_id="moz-fx-data-shared-prod",
        owner="akomar@mozilla.com",
        email=[
            "akomar@mozilla.com",
            "anicholson@mozilla.com",
            "cmorales@mozilla.com",
            "telemetry-alerts@mozilla.com",
        ],
        date_partition_parameter="submission_date",
        depends_on_past=True,
    )
