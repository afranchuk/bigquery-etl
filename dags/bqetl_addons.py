# Generated via https://github.com/mozilla/bigquery-etl/blob/main/bigquery_etl/query_scheduling/generate_airflow_dags.py

from airflow import DAG
from airflow.sensors.external_task import ExternalTaskMarker
from airflow.sensors.external_task import ExternalTaskSensor
from airflow.utils.task_group import TaskGroup
from airflow.providers.cncf.kubernetes.secret import Secret
import datetime
from operators.gcp_container_operator import GKEPodOperator
from utils.constants import ALLOWED_STATES, FAILED_STATES
from utils.gcp import bigquery_etl_query, bigquery_dq_check, bigquery_bigeye_check
from bigeye_airflow.operators.run_metrics_operator import RunMetricsOperator

docs = """
### bqetl_addons

Built from bigquery-etl repo, [`dags/bqetl_addons.py`](https://github.com/mozilla/bigquery-etl/blob/generated-sql/dags/bqetl_addons.py)

#### Description

Daily rollups of addon data from `main` pings.

Depends on `bqetl_search`, so is scheduled after that DAG.

#### Owner

kik@mozilla.com

#### Tags

* impact/tier_2
* repo/bigquery-etl
"""

addon_moderations_derived__cinder_decisions_raw__v1_bqetl_addons__cinder_bearer_token = Secret(
    deploy_type="env",
    deploy_target="CINDER_TOKEN",
    secret="airflow-gke-secrets",
    key="bqetl_addons__cinder_bearer_token",
)


default_args = {
    "owner": "kik@mozilla.com",
    "start_date": datetime.datetime(2018, 11, 27, 0, 0),
    "end_date": None,
    "email": ["telemetry-alerts@mozilla.com", "kik@mozilla.com"],
    "depends_on_past": False,
    "retry_delay": datetime.timedelta(seconds=1800),
    "email_on_failure": True,
    "email_on_retry": True,
    "retries": 2,
}

tags = ["impact/tier_2", "repo/bigquery-etl"]

with DAG(
    "bqetl_addons",
    default_args=default_args,
    schedule_interval="0 4 * * *",
    doc_md=docs,
    tags=tags,
) as dag:

    wait_for_copy_deduplicate_main_ping = ExternalTaskSensor(
        task_id="wait_for_copy_deduplicate_main_ping",
        external_dag_id="copy_deduplicate",
        external_task_id="copy_deduplicate_main_ping",
        execution_delta=datetime.timedelta(seconds=10800),
        check_existence=True,
        mode="reschedule",
        allowed_states=ALLOWED_STATES,
        failed_states=FAILED_STATES,
        pool="DATA_ENG_EXTERNALTASKSENSOR",
    )

    wait_for_search_derived__search_clients_daily__v8 = ExternalTaskSensor(
        task_id="wait_for_search_derived__search_clients_daily__v8",
        external_dag_id="bqetl_search",
        external_task_id="search_derived__search_clients_daily__v8",
        execution_delta=datetime.timedelta(seconds=3600),
        check_existence=True,
        mode="reschedule",
        allowed_states=ALLOWED_STATES,
        failed_states=FAILED_STATES,
        pool="DATA_ENG_EXTERNALTASKSENSOR",
    )

    wait_for_telemetry_derived__clients_last_seen__v1 = ExternalTaskSensor(
        task_id="wait_for_telemetry_derived__clients_last_seen__v1",
        external_dag_id="bqetl_main_summary",
        external_task_id="telemetry_derived__clients_last_seen__v1",
        execution_delta=datetime.timedelta(seconds=7200),
        check_existence=True,
        mode="reschedule",
        allowed_states=ALLOWED_STATES,
        failed_states=FAILED_STATES,
        pool="DATA_ENG_EXTERNALTASKSENSOR",
    )

    addon_moderations_derived__cinder_decisions_raw__v1 = GKEPodOperator(
        task_id="addon_moderations_derived__cinder_decisions_raw__v1",
        arguments=[
            "python",
            "sql/moz-fx-data-shared-prod/addon_moderations_derived/cinder_decisions_raw_v1/query.py",
        ]
        + ["--date", "{{ ds }}"],
        image="gcr.io/moz-fx-data-airflow-prod-88e0/bigquery-etl:latest",
        owner="mhirose@mozilla.com",
        email=[
            "kik@mozilla.com",
            "mhirose@mozilla.com",
            "telemetry-alerts@mozilla.com",
        ],
        secrets=[
            addon_moderations_derived__cinder_decisions_raw__v1_bqetl_addons__cinder_bearer_token,
        ],
    )

    telemetry_derived__addon_aggregates__v2 = bigquery_etl_query(
        task_id="telemetry_derived__addon_aggregates__v2",
        destination_table="addon_aggregates_v2",
        dataset_id="telemetry_derived",
        project_id="moz-fx-data-shared-prod",
        owner="kik@mozilla.com",
        email=["kik@mozilla.com", "telemetry-alerts@mozilla.com"],
        date_partition_parameter="submission_date",
        depends_on_past=False,
    )

    telemetry_derived__addon_names__v1 = bigquery_etl_query(
        task_id="telemetry_derived__addon_names__v1",
        destination_table="addon_names_v1",
        dataset_id="telemetry_derived",
        project_id="moz-fx-data-shared-prod",
        owner="kik@mozilla.com",
        email=["kik@mozilla.com", "telemetry-alerts@mozilla.com"],
        date_partition_parameter=None,
        depends_on_past=False,
        task_concurrency=1,
        parameters=["submission_date:DATE:{{ds}}"],
    )

    telemetry_derived__addons__v2 = bigquery_etl_query(
        task_id="telemetry_derived__addons__v2",
        destination_table="addons_v2",
        dataset_id="telemetry_derived",
        project_id="moz-fx-data-shared-prod",
        owner="kik@mozilla.com",
        email=["kik@mozilla.com", "telemetry-alerts@mozilla.com"],
        date_partition_parameter="submission_date",
        depends_on_past=False,
    )

    with TaskGroup(
        "telemetry_derived__addons__v2_external",
    ) as telemetry_derived__addons__v2_external:
        ExternalTaskMarker(
            task_id="bqetl_feature_usage__wait_for_telemetry_derived__addons__v2",
            external_dag_id="bqetl_feature_usage",
            external_task_id="wait_for_telemetry_derived__addons__v2",
            execution_date="{{ (execution_date - macros.timedelta(days=-1, seconds=82800)).isoformat() }}",
        )

        telemetry_derived__addons__v2_external.set_upstream(
            telemetry_derived__addons__v2
        )

    telemetry_derived__addons_daily__v1 = bigquery_etl_query(
        task_id="telemetry_derived__addons_daily__v1",
        destination_table="addons_daily_v1",
        dataset_id="telemetry_derived",
        project_id="moz-fx-data-shared-prod",
        owner="kik@mozilla.com",
        email=["kik@mozilla.com", "telemetry-alerts@mozilla.com"],
        date_partition_parameter="submission_date",
        depends_on_past=False,
    )

    telemetry_derived__addon_aggregates__v2.set_upstream(
        wait_for_copy_deduplicate_main_ping
    )

    telemetry_derived__addon_names__v1.set_upstream(wait_for_copy_deduplicate_main_ping)

    telemetry_derived__addons__v2.set_upstream(wait_for_copy_deduplicate_main_ping)

    telemetry_derived__addons_daily__v1.set_upstream(
        wait_for_search_derived__search_clients_daily__v8
    )

    telemetry_derived__addons_daily__v1.set_upstream(
        wait_for_telemetry_derived__clients_last_seen__v1
    )
