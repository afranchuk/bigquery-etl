"""Delete user data from long term storage."""

import logging
import warnings
from argparse import ArgumentParser
from collections import defaultdict
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from functools import partial
from multiprocessing.pool import ThreadPool
from operator import attrgetter
from textwrap import dedent
from typing import Callable, Iterable, Optional, Tuple, Union

from google.api_core.exceptions import NotFound
from google.cloud import bigquery
from google.cloud.bigquery import QueryJob

from ..format_sql.formatter import reformat
from ..util import standard_args
from ..util.bigquery_id import FULL_JOB_ID_RE, full_job_id, sql_table_id
from ..util.client_queue import ClientQueue
from ..util.exceptions import BigQueryInsertError
from .config import (
    DELETE_TARGETS,
    DeleteSource,
    DeleteTarget,
    find_experiment_analysis_targets,
    find_glean_targets,
    find_pioneer_targets,
)

NULL_PARTITION_ID = "__NULL__"
OUTSIDE_RANGE_PARTITION_ID = "__UNPARTITIONED__"

parser = ArgumentParser(description=__doc__)
standard_args.add_dry_run(parser)
parser.add_argument(
    "--environment",
    default="telemetry",
    const="telemetry",
    nargs="?",
    choices=["telemetry", "pioneer", "experiments"],
    help="environment to run in (dictates the choice of source and target tables): "
    "telemetry - standard environment, "
    "pioneer - restricted pioneer environment, "
    "experiments - experiment analysis tables",
)
parser.add_argument(
    "--pioneer-study-projects",
    "--pioneer_study_projects",
    default=[],
    help="Pioneer study-specific analysis projects to include in data deletion.",
    type=lambda s: [i for i in s.split(",")],
)
parser.add_argument(
    "--partition-limit",
    "--partition_limit",
    metavar="N",
    type=int,
    help="Only use the first N partitions per table; requires --dry-run",
)
parser.add_argument(
    "--no-use-dml",
    "--no_use_dml",
    action="store_false",
    dest="use_dml",
    help="Use SELECT * FROM instead of DELETE in queries to avoid concurrent DML limit "
    "or errors due to read-only permissions being insufficient to dry run DML; unless "
    "used with --dry-run, DML will still be used for special partitions like __NULL__",
)
standard_args.add_log_level(parser)
standard_args.add_parallelism(parser)
parser.add_argument(
    "-e",
    "--end-date",
    "--end_date",
    default=datetime.utcnow().date(),
    type=lambda x: datetime.strptime(x, "%Y-%m-%d").date(),
    help="last date of pings to delete; One day after last date of "
    "deletion requests to process; defaults to today in UTC",
)
parser.add_argument(
    "-s",
    "--start-date",
    "--start_date",
    type=lambda x: datetime.strptime(x, "%Y-%m-%d").date(),
    help="first date of deletion requests to process; DOES NOT apply to ping date; "
    "defaults to 14 days before --end-date in UTC",
)
standard_args.add_billing_projects(parser, default=["moz-fx-data-bq-batch-prod"])
parser.add_argument(
    "--source-project",
    "--source_project",
    help="override the project used for deletion request tables",
)
parser.add_argument(
    "--target-project",
    "--target_project",
    help="override the project used for target tables",
)
parser.add_argument(
    "--max-single-dml-bytes",
    "--max_single_dml_bytes",
    default=10 * 2**40,
    type=int,
    help="Maximum number of bytes in a table that should be processed using a single "
    "DML query; tables above this limit will be processed using per-partition "
    "queries; this option prevents queries against large tables from exceeding the "
    "6-hour time limit; defaults to 10 TiB",
)
standard_args.add_priority(parser)
parser.add_argument(
    "--state-table",
    "--state_table",
    metavar="TABLE",
    help="Table for recording state; Used to avoid repeating deletes if interrupted; "
    "Create it if it does not exist; By default state is not recorded",
)
parser.add_argument(
    "--task-table",
    "--task_table",
    metavar="TABLE",
    help="Table for recording tasks; Used along with --state-table to determine "
    "progress; Create it if it does not exist; By default tasks are not recorded",
)
standard_args.add_table_filter(parser)
parser.add_argument(
    "--sampling-tables",
    "--sampling_tables",
    nargs="+",
    dest="sampling_tables",
    help="Create tasks per sample id for the given table(s).  Table format is dataset.table_name.",
    default=[],
)
parser.add_argument(
    "--sampling-parallelism",
    "--sampling_parallelism",
    type=int,
    default=10,
    help="Number of concurrent queries to run per partition when shredding per sample id",
)
parser.add_argument(
    "--temp-dataset",
    "--temp_dataset",
    metavar="PROJECT.DATASET",
    help="Dataset (project.dataset format) to write intermediate results of sampled queries to. "
    "Must be specified when --sampling-tables is set.",
)


@dataclass
class DeleteJobResults:
    """Subset of a bigquery job object retaining only fields that are needed."""

    job_id: str
    total_bytes_processed: Optional[int]
    num_dml_affected_rows: Optional[int]
    destination: str


def record_state(client, task_id, job, dry_run, start_date, end_date, state_table):
    """Record the job for task_id in state_table."""
    if state_table is not None:
        job_id = "a job_id" if dry_run else full_job_id(job)
        insert_tense = "Would insert" if dry_run else "Inserting"
        logging.info(f"{insert_tense} {job_id} in {state_table} for task: {task_id}")
        if not dry_run:
            BigQueryInsertError.raise_if_present(
                errors=client.insert_rows_json(
                    state_table,
                    [
                        {
                            "task_id": task_id,
                            "job_id": job_id,
                            "job_created": job.created.isoformat(),
                            "start_date": start_date.isoformat(),
                            "end_date": end_date.isoformat(),
                        }
                    ],
                    skip_invalid_rows=False,
                )
            )


def wait_for_job(
    client,
    states,
    task_id,
    dry_run,
    create_job,
    check_table_existence=False,
    **state_kwargs,
) -> DeleteJobResults:
    """Get a job from state or create a new job, and wait for the job to complete."""
    job = None
    if task_id in states:
        job = client.get_job(**FULL_JOB_ID_RE.fullmatch(states[task_id]).groupdict())  # type: ignore[union-attr]
        if job.errors:
            logging.info(f"Previous attempt failed, retrying for {task_id}")
            job = None
        elif job.ended:
            # if destination table no longer exists (temp table expired), rerun job
            try:
                if check_table_existence:
                    client.get_table(job.destination)
                logging.info(
                    f"Previous attempt succeeded, reusing result for {task_id}"
                )
            except NotFound:
                logging.info(f"Previous result expired, retrying for {task_id}")
                job = None
        else:
            logging.info(f"Previous attempt still running for {task_id}")
    if job is None:
        job = create_job(client)
        record_state(
            client=client, task_id=task_id, dry_run=dry_run, job=job, **state_kwargs
        )
    if not dry_run and not job.ended:
        logging.info(f"Waiting on {full_job_id(job)} for {task_id}")
        job.result()

    try:
        bytes_processed = job.total_bytes_processed
    except AttributeError:
        bytes_processed = 0

    return DeleteJobResults(
        job_id=job.job_id,
        total_bytes_processed=bytes_processed,
        num_dml_affected_rows=(
            job.num_dml_affected_rows if isinstance(job, QueryJob) else None
        ),
        destination=job.destination,
    )


def get_task_id(target, partition_id):
    """Get unique task id for state tracking."""
    task_id = sql_table_id(target)
    if partition_id:
        task_id += f"${partition_id}"
    return task_id


@dataclass
class Partition:
    """Return type for get_partition."""

    condition: str
    id: Optional[str] = None
    is_special: bool = False


def _override_query_with_fxa_id_in_extras(
    field_condition: str,
    target: DeleteTarget,
    sources: Iterable[DeleteSource],
    source_condition: str,
) -> str:
    """Override query to handle fxa_id nested in event extras in relay_backend_stable.events_v1."""
    sources = list(sources)
    if (
        target.table == "relay_backend_stable.events_v1"
        and len(target.fields) == 1
        and target.fields[0] == "events[*].extra.fxa_id"
        and len(sources) == 1
        and sources[0].table == "firefox_accounts.fxa_delete_events"
        and sources[0].field == "user_id"
    ):
        field_condition = (
            """
                EXISTS (
                  WITH user_ids AS (
                  SELECT
                    user_id_unhashed AS user_id
                  FROM
                  `moz-fx-data-shared-prod.firefox_accounts.fxa_delete_events`
                  WHERE """
            + " AND ".join((source_condition, *sources[0].conditions))
            + """)
                  SELECT 1
                  FROM UNNEST(events) AS e
                  JOIN UNNEST(e.extra) AS ex
                  JOIN user_ids u
                  ON ex.value = u.user_id
                  WHERE ex.key = 'fxa_id'
                )
                """
        )
    return field_condition


def delete_from_partition(
    dry_run: bool,
    partition: Partition,
    priority: str,
    source_condition: str,
    sources: Iterable[DeleteSource],
    target: DeleteTarget,
    use_dml: bool,
    sample_id: Optional[int] = None,
    temp_dataset: Optional[str] = None,
    clustering_fields: Optional[Iterable[str]] = None,
    **wait_for_job_kwargs,
):
    """Return callable to handle deletion requests for partitions of a target table."""
    job_config = bigquery.QueryJobConfig(dry_run=dry_run, priority=priority)
    # whole table operations must use DML to protect against dropping partitions in the
    # case of conflicting write operations in ETL, and special partitions must use DML
    # because they can't be set as a query destination.
    if partition.id is None or partition.is_special:
        use_dml = True
    elif sample_id is not None:
        use_dml = False
        job_config.destination = (
            f"{temp_dataset}.{target.table_id}_{partition.id}__sample_{sample_id}"
        )
        job_config.write_disposition = bigquery.WriteDisposition.WRITE_TRUNCATE
        job_config.clustering_fields = clustering_fields
    elif not use_dml:
        job_config.destination = f"{sql_table_id(target)}${partition.id}"
        job_config.write_disposition = bigquery.WriteDisposition.WRITE_TRUNCATE

    def create_job(client) -> bigquery.QueryJob:
        def normalized_expr(expr: str) -> str:
            if (
                expr == "context_id"
                or expr == "payload.scalars.parent.deletion_request_context_id"
            ):
                return f"REPLACE(REPLACE({expr}, '{{', ''), '}}', '')"
            return expr

        if use_dml:
            field_condition = " OR ".join(
                f"""
                {normalized_expr(field)} IN (
                  SELECT
                    {normalized_expr(source.field)}
                  FROM
                    `{sql_table_id(source)}`
                  WHERE
                    {" AND ".join((source_condition, *source.conditions))}
                )
                """
                for field, source in zip(target.fields, sources)
            )

            # Temporary workaround for fxa_id nested in event extras in relay_backend_stable.events_v1
            # We'll be able to remove this once fxa_id is migrated to string metric
            # See https://mozilla-hub.atlassian.net/browse/DENG-7965 and 7964
            field_condition = _override_query_with_fxa_id_in_extras(
                field_condition, target, sources, source_condition
            )

            query = reformat(
                f"""
                DELETE
                  `{sql_table_id(target)}`
                WHERE
                  ({field_condition})
                  AND ({partition.condition})
                """
            )
        else:
            field_joins = "".join(
                (
                    f"""
                LEFT JOIN
                  (
                    SELECT
                      {normalized_expr(source.field)} AS _source_{index}
                    FROM
                      `{sql_table_id(source)}`
                    WHERE
                """
                    + " AND ".join((source_condition, *source.conditions))
                    + (f" AND sample_id = {sample_id}" if sample_id is not None else "")
                    + f"""
                  )
                  ON {normalized_expr(field)} = _source_{index}
                """
                )
                for index, (field, source) in enumerate(zip(target.fields, sources))
            )
            field_conditions = " AND ".join(
                f"_source_{index} IS NULL" for index, _ in enumerate(sources)
            )

            if partition.id is None:
                # only apply field conditions on partition.condition
                field_conditions = f"""
                ({partition.condition}) IS NOT TRUE
                OR ({field_conditions})
                """
                # always true partition condition to satisfy require_partition_filter
                partition_condition = f"""
                ({partition.condition}) IS NOT TRUE
                OR ({partition.condition})
                """
            else:
                partition_condition = partition.condition

            query = reformat(
                f"""
                SELECT
                  _target.*,
                FROM
                  `{sql_table_id(target)}` AS _target
                {field_joins}
                WHERE
                  ({field_conditions})
                  AND ({partition_condition})
                  {f" AND sample_id = {sample_id}" if sample_id is not None else ""}
                """
            )
        run_tense = "Would run" if dry_run else "Running"
        logging.debug(f"{run_tense} query: {query}")
        return client.query(query, job_config=job_config)

    return partial(
        wait_for_job, create_job=create_job, dry_run=dry_run, **wait_for_job_kwargs
    )


def delete_from_partition_with_sampling(
    dry_run: bool,
    partition: Partition,
    priority: str,
    source_condition: str,
    sources: Iterable[DeleteSource],
    target: DeleteTarget,
    use_dml: bool,
    sampling_parallelism: int,
    temp_dataset: str,
    **wait_for_job_kwargs,
):
    """Return callable to delete from a partition of a target table per sample id."""
    copy_job_config = bigquery.CopyJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        create_disposition=bigquery.CreateDisposition.CREATE_IF_NEEDED,
    )
    target_table = f"{sql_table_id(target)}${partition.id}"

    def delete_by_sample(client) -> Union[bigquery.CopyJob, bigquery.QueryJob]:
        intermediate_clustering_fields = client.get_table(
            target_table
        ).clustering_fields

        tasks = [
            delete_from_partition(
                dry_run=dry_run,
                partition=partition,
                priority=priority,
                source_condition=source_condition,
                sources=sources,
                target=target,
                use_dml=use_dml,
                temp_dataset=temp_dataset,
                sample_id=s,
                clustering_fields=intermediate_clustering_fields,
                check_table_existence=True,
                **{
                    **wait_for_job_kwargs,
                    # override task id with sample id suffix
                    "task_id": f"{wait_for_job_kwargs['task_id']}__sample_{s}",
                },
            )
            for s in range(100)
        ]

        # Run all 100 delete functions in parallel, exception is raised without retry if any fail
        with ThreadPool(sampling_parallelism) as pool:
            jobs = [
                pool.apply_async(
                    task,
                    args=(client,),
                )
                for task in tasks
            ]

            results = [job.get() for job in jobs]

        intermediate_tables = [result.destination for result in results]
        run_tense = "Would copy" if dry_run else "Copying"
        logging.debug(
            f"{run_tense} {len(intermediate_tables)} "
            f"{[str(t) for t in intermediate_tables]} to {target_table}"
        )
        if not dry_run:
            copy_job = client.copy_table(
                sources=intermediate_tables,
                destination=target_table,
                job_config=copy_job_config,
            )
            # simulate query job properties for logging
            copy_job.total_bytes_processed = sum(
                [r.total_bytes_processed for r in results]
            )
            return copy_job
        else:
            # copy job doesn't have dry runs so dry run base partition for byte estimate
            return client.query(
                f"SELECT * FROM `{sql_table_id(target)}` WHERE {partition.condition}",
                job_config=bigquery.QueryJobConfig(dry_run=True),
            )

    return partial(
        wait_for_job,
        create_job=delete_by_sample,
        dry_run=dry_run,
        **wait_for_job_kwargs,
    )


def get_partition_expr(table):
    """Get the SQL expression to use for a table's partitioning field."""
    if table.range_partitioning:
        return table.range_partitioning.field
    if table.time_partitioning:
        return f"CAST({table.time_partitioning.field or '_PARTITIONTIME'} AS DATE)"


def get_partition(table, partition_expr, end_date, id_=None) -> Optional[Partition]:
    """Return a Partition for id_ unless it is a date on or after end_date."""
    if id_ is None:
        if table.time_partitioning:
            return Partition(condition=f"{partition_expr} < '{end_date}'")
        return Partition(condition="TRUE")
    if id_ == NULL_PARTITION_ID:
        if table.time_partitioning:
            return Partition(
                condition=f"{table.time_partitioning.field} IS NULL",
                id=id_,
                is_special=True,
            )
        return Partition(condition=f"{partition_expr} IS NULL", id=id_, is_special=True)
    if table.time_partitioning:
        date = datetime.strptime(id_, "%Y%m%d").date()
        if date < end_date:
            return Partition(f"{partition_expr} = '{date}'", id_)
        return None
    if table.range_partitioning:
        if id_ == OUTSIDE_RANGE_PARTITION_ID:
            return Partition(
                condition=f"{partition_expr} < {table.range_partitioning.range_.start} "
                f"OR {partition_expr} >= {table.range_partitioning.range_.end}",
                id=id_,
                is_special=True,
            )
        if table.range_partitioning.range_.interval > 1:
            return Partition(
                condition=f"{partition_expr} BETWEEN {id_} "
                f"AND {int(id_) + table.range_partitioning.range_.interval - 1}",
                id=id_,
            )
    return Partition(condition=f"{partition_expr} = {id_}", id=id_)


def list_partitions(
    client, table, partition_expr, end_date, max_single_dml_bytes, partition_limit
):
    """List the relevant partitions in a table."""
    partitions = [
        partition
        for partition in (
            [
                get_partition(table, partition_expr, end_date, row["partition_id"])
                for row in client.query(
                    dedent(
                        f"""
                        SELECT
                          partition_id
                        FROM
                          [{sql_table_id(table)}$__PARTITIONS_SUMMARY__]
                        """
                    ).strip(),
                    bigquery.QueryJobConfig(use_legacy_sql=True),
                ).result()
            ]
            if table.num_bytes > max_single_dml_bytes and partition_expr is not None
            else [get_partition(table, partition_expr, end_date)]
        )
        if partition is not None
    ]
    if partition_limit:
        return sorted(partitions, key=attrgetter("id"), reverse=True)[:partition_limit]
    return partitions


@dataclass
class Task:
    """Return type for delete_from_table."""

    table: bigquery.Table
    sources: Tuple[DeleteSource]
    partition_id: Optional[str]
    func: Callable[[bigquery.Client], bigquery.QueryJob]

    @property
    def partition_sort_key(self):
        """Return a tuple to control the order in which tasks will be handled.

        When used with reverse=True, handle tasks without partition_id, then
        tasks without time_partitioning, then most recent dates first.
        """
        return (
            self.partition_id is None,
            self.table.time_partitioning is None,
            self.partition_id,
        )


def delete_from_table(
    client,
    target,
    sources,
    dry_run,
    end_date,
    max_single_dml_bytes,
    partition_limit,
    sampling_parallelism,
    use_sampling,
    temp_dataset,
    **kwargs,
) -> Iterable[Task]:
    """Yield tasks to handle deletion requests for a target table."""
    try:
        table = client.get_table(sql_table_id(target))
    except NotFound:
        logging.warning(f"Skipping {sql_table_id(target)} due to NotFound exception")
        return ()  # type: ignore
    partition_expr = get_partition_expr(table)
    for partition in list_partitions(
        client, table, partition_expr, end_date, max_single_dml_bytes, partition_limit
    ):
        # no sampling for __NULL__ partition
        if use_sampling and not partition.is_special:
            kwargs["sampling_parallelism"] = sampling_parallelism
            delete_func: Callable = delete_from_partition_with_sampling
        else:
            if use_sampling:
                logging.warning(
                    "Cannot use sampling on full table deletion, "
                    f"{target.dataset_id}.{target.table_id} is too small to use sampling"
                )
            kwargs.pop("sampling_parallelism", None)
            delete_func = delete_from_partition

        yield Task(
            table=table,
            sources=sources,
            partition_id=partition.id,
            func=delete_func(
                dry_run=dry_run,
                partition=partition,
                target=target,
                sources=sources,
                task_id=get_task_id(target, partition.id),
                end_date=end_date,
                temp_dataset=temp_dataset,
                **kwargs,
            ),
        )


def main():
    """Process deletion requests."""
    args = parser.parse_args()
    if args.partition_limit is not None and not args.dry_run:
        parser.print_help()
        logging.warning("ERROR: --partition-limit specified without --dry-run")
    if len(args.sampling_tables) > 0 and args.temp_dataset is None:
        parser.error("--temp-dataset must be specified when using --sampling-tables")
    if args.start_date is None:
        args.start_date = args.end_date - timedelta(days=14)
    source_condition = (
        f"DATE(submission_timestamp) >= '{args.start_date}' "
        f"AND DATE(submission_timestamp) < '{args.end_date}'"
    )
    client_q = ClientQueue(
        args.billing_projects,
        args.parallelism,
        connection_pool_max_size=(
            max(args.parallelism * args.sampling_parallelism, 12)
            if len(args.sampling_tables) > 0
            else None
        ),
    )
    client = client_q.default_client
    states = {}
    if args.state_table:
        state_table_exists = False
        try:
            client.get_table(args.state_table)
            state_table_exists = True
        except NotFound:
            if not args.dry_run:
                client.create_table(
                    bigquery.Table(
                        args.state_table,
                        [
                            bigquery.SchemaField("task_id", "STRING"),
                            bigquery.SchemaField("job_id", "STRING"),
                            bigquery.SchemaField("job_created", "TIMESTAMP"),
                            bigquery.SchemaField("start_date", "DATE"),
                            bigquery.SchemaField("end_date", "DATE"),
                        ],
                    )
                )
                state_table_exists = True
        if state_table_exists:
            states = dict(
                client.query(
                    reformat(
                        f"""
                        SELECT
                          task_id,
                          job_id,
                        FROM
                          `{args.state_table}`
                        WHERE
                          end_date = '{args.end_date}'
                        ORDER BY
                          job_created
                        """
                    )
                ).result()
            )

    if args.environment == "telemetry":
        with ThreadPool(6) as pool:
            glean_targets = find_glean_targets(pool, client)
        targets_with_sources = (
            *DELETE_TARGETS.items(),
            *glean_targets.items(),
        )
    elif args.environment == "experiments":
        targets_with_sources = find_experiment_analysis_targets(client).items()
    elif args.environment == "pioneer":
        with ThreadPool(args.parallelism) as pool:
            targets_with_sources = find_pioneer_targets(
                pool, client, study_projects=args.pioneer_study_projects
            ).items()

    missing_sampling_tables = [
        t
        for t in args.sampling_tables
        if t not in [target.table for target, _ in targets_with_sources]
    ]
    if len(missing_sampling_tables) > 0:
        raise ValueError(
            f"{len(missing_sampling_tables)} sampling tables not found in "
            f"targets: {missing_sampling_tables}"
        )

    tasks = [
        task
        for target, sources in targets_with_sources
        if args.table_filter(target.table)
        for task in delete_from_table(
            client=client,
            target=replace(target, project=args.target_project or target.project),
            sources=[
                replace(source, project=args.source_project or source.project)
                for source in (sources if isinstance(sources, tuple) else (sources,))
            ],
            source_condition=source_condition,
            dry_run=args.dry_run,
            use_dml=args.use_dml,
            priority=args.priority,
            start_date=args.start_date,
            end_date=args.end_date,
            max_single_dml_bytes=args.max_single_dml_bytes,
            partition_limit=args.partition_limit,
            state_table=args.state_table,
            states=states,
            sampling_parallelism=args.sampling_parallelism,
            use_sampling=target.table in args.sampling_tables,
            temp_dataset=args.temp_dataset,
        )
    ]

    if not tasks:
        logging.error("No tables selected")
        parser.exit(1)
    # ORDER BY partition_sort_key DESC, sql_table_id ASC
    # https://docs.python.org/3/howto/sorting.html#sort-stability-and-complex-sorts
    tasks.sort(key=lambda task: sql_table_id(task.table))
    tasks.sort(key=attrgetter("partition_sort_key"), reverse=True)

    with ThreadPool(args.parallelism) as pool:
        if args.task_table and not args.dry_run:
            # record task information
            try:
                client.get_table(args.task_table)
            except NotFound:
                table = bigquery.Table(
                    args.task_table,
                    [
                        bigquery.SchemaField("task_id", "STRING"),
                        bigquery.SchemaField("start_date", "DATE"),
                        bigquery.SchemaField("end_date", "DATE"),
                        bigquery.SchemaField("target", "STRING"),
                        bigquery.SchemaField("target_rows", "INT64"),
                        bigquery.SchemaField("target_bytes", "INT64"),
                        bigquery.SchemaField("source_bytes", "INT64"),
                    ],
                )
                table.time_partitioning = bigquery.TimePartitioning()
                client.create_table(table)
            sources = list(set(source for task in tasks for source in task.sources))
            source_bytes = {
                source: job.total_bytes_processed
                for source, job in zip(
                    sources,
                    pool.starmap(
                        client.query,
                        [
                            (
                                reformat(
                                    f"""
                                    SELECT
                                      {source.field}
                                    FROM
                                      `{sql_table_id(source)}`
                                    WHERE
                                      {source_condition}
                                    """
                                ),
                                bigquery.QueryJobConfig(dry_run=True),
                            )
                            for source in sources
                        ],
                        chunksize=1,
                    ),
                )
            }
            step = 10000  # max 10K rows per insert
            for start in range(0, len(tasks), step):
                end = start + step
                BigQueryInsertError.raise_if_present(
                    errors=client.insert_rows_json(
                        args.task_table,
                        [
                            {
                                "task_id": get_task_id(task.table, task.partition_id),
                                "start_date": args.start_date.isoformat(),
                                "end_date": args.end_date.isoformat(),
                                "target": sql_table_id(task.table),
                                "target_rows": task.table.num_rows,
                                "target_bytes": task.table.num_bytes,
                                "source_bytes": sum(
                                    map(source_bytes.get, task.sources)
                                ),
                            }
                            for task in tasks[start:end]
                        ],
                    )
                )
        results = pool.map(
            client_q.with_client, (task.func for task in tasks), chunksize=1
        )
    jobs_by_table = defaultdict(list)
    for i, job in enumerate(results):
        jobs_by_table[tasks[i].table].append(job)
    bytes_processed = rows_deleted = 0
    for table, jobs in jobs_by_table.items():
        table_bytes_processed = sum(job.total_bytes_processed or 0 for job in jobs)
        bytes_processed += table_bytes_processed
        table_id = sql_table_id(table)
        if args.dry_run:
            logging.info(f"Would scan {table_bytes_processed} bytes from {table_id}")
        else:
            table_rows_deleted = sum(job.num_dml_affected_rows or 0 for job in jobs)
            rows_deleted += table_rows_deleted
            logging.info(
                f"Scanned {table_bytes_processed} bytes and "
                f"deleted {table_rows_deleted} rows from {table_id}"
            )
    if args.dry_run:
        logging.info(f"Would scan {bytes_processed} in total")
    else:
        logging.info(
            f"Scanned {bytes_processed} and deleted {rows_deleted} rows in total"
        )


if __name__ == "__main__":
    warnings.filterwarnings("ignore", module="google.auth._default")
    main()
