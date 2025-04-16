# Generated via https://github.com/mozilla/bigquery-etl/blob/main/bigquery_etl/query_scheduling/generate_airflow_dags.py

from airflow import DAG
from airflow.sensors.external_task import ExternalTaskMarker
from airflow.sensors.external_task import ExternalTaskSensor
from airflow.utils.task_group import TaskGroup
import datetime
from operators.gcp_container_operator import GKEPodOperator
from utils.constants import ALLOWED_STATES, FAILED_STATES
from utils.gcp import bigquery_etl_query, bigquery_dq_check, bigquery_bigeye_check

docs = """
### bqetl_releases

Built from bigquery-etl repo, [`dags/bqetl_releases.py`](https://github.com/mozilla/bigquery-etl/blob/generated-sql/dags/bqetl_releases.py)

#### Description

Schedule release data import from https://product-details.mozilla.org/1.0

For more context, see
https://wiki.mozilla.org/Release_Management/Product_details

#### Owner

ascholtz@mozilla.com

#### Tags

* impact/tier_2
* repo/bigquery-etl
"""


default_args = {
    "owner": "ascholtz@mozilla.com",
    "start_date": datetime.datetime(2021, 4, 14, 0, 0),
    "end_date": None,
    "email": ["ascholtz@mozilla.com", "telemetry-alerts@mozilla.com"],
    "depends_on_past": False,
    "retry_delay": datetime.timedelta(seconds=1800),
    "email_on_failure": True,
    "email_on_retry": True,
    "retries": 2,
    "max_active_tis_per_dag": None,
}

tags = ["impact/tier_2", "repo/bigquery-etl"]

with DAG(
    "bqetl_releases",
    default_args=default_args,
    schedule_interval="0 4 * * *",
    doc_md=docs,
    tags=tags,
    catchup=False,
) as dag:

    bigeye__org_mozilla_fenix_derived__releases__v1 = bigquery_bigeye_check(
        task_id="bigeye__org_mozilla_fenix_derived__releases__v1",
        table_id="moz-fx-data-shared-prod.org_mozilla_fenix_derived.releases_v1",
        warehouse_id="1939",
        owner="ascholtz@mozilla.com",
        email=["ascholtz@mozilla.com", "telemetry-alerts@mozilla.com"],
        depends_on_past=False,
        execution_timeout=datetime.timedelta(hours=1),
        retries=1,
    )

    org_mozilla_fenix_derived__releases__v1 = GKEPodOperator(
        task_id="org_mozilla_fenix_derived__releases__v1",
        arguments=[
            "python",
            "sql/moz-fx-data-shared-prod/org_mozilla_fenix_derived/releases_v1/query.py",
        ]
        + [],
        image="gcr.io/moz-fx-data-airflow-prod-88e0/bigquery-etl:latest",
        owner="ascholtz@mozilla.com",
        email=["ascholtz@mozilla.com", "telemetry-alerts@mozilla.com"],
    )

    telemetry_derived__applications__v1 = GKEPodOperator(
        task_id="telemetry_derived__applications__v1",
        arguments=[
            "python",
            "sql/moz-fx-data-shared-prod/telemetry_derived/applications_v1/query.py",
        ]
        + [],
        image="gcr.io/moz-fx-data-airflow-prod-88e0/bigquery-etl:latest",
        owner="ascholtz@mozilla.com",
        email=["ascholtz@mozilla.com", "telemetry-alerts@mozilla.com"],
    )

    telemetry_derived__releases__v1 = GKEPodOperator(
        task_id="telemetry_derived__releases__v1",
        arguments=[
            "python",
            "sql/moz-fx-data-shared-prod/telemetry_derived/releases_v1/query.py",
        ]
        + [],
        image="gcr.io/moz-fx-data-airflow-prod-88e0/bigquery-etl:latest",
        owner="ascholtz@mozilla.com",
        email=["ascholtz@mozilla.com", "telemetry-alerts@mozilla.com"],
    )

    bigeye__org_mozilla_fenix_derived__releases__v1.set_upstream(
        org_mozilla_fenix_derived__releases__v1
    )
