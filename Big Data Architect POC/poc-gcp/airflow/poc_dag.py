"""
POC Medallion Pipeline DAG
Orchestrates Bronze → Silver → Gold with DQ gates.
Deployed to Cloud Composer via:
  gcloud composer environments storage dags import \
    --environment=poc-composer --location=us-central1 \
    --source=airflow/poc_dag.py
"""
from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.models import Variable
from airflow.operators.bash import BashOperator
from airflow.operators.python import BranchPythonOperator, PythonOperator
from airflow.providers.google.cloud.operators.bigquery import (
    BigQueryInsertJobOperator,
)
from airflow.providers.google.cloud.operators.dataproc import (
    DataprocCreateBatchOperator,
)
from airflow.utils.trigger_rule import TriggerRule

# ─── Config ──────────────────────────────────────────
PROJECT_ID   = Variable.get("gcp_project_id", default_var="poc-data-platform")
REGION       = Variable.get("gcp_region", default_var="us-central1")
BRONZE_BUCKET = f"{PROJECT_ID}-bronze"
SCRIPTS_BUCKET = f"{PROJECT_ID}-scripts"

DEFAULT_ARGS = {
    "owner": "data-platform",
    "depends_on_past": False,
    "email": ["data-alerts@company.com"],
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "start_date": datetime(2026, 1, 1),
    "sla": timedelta(hours=2),
    "execution_timeout": timedelta(hours=3),
}

# ─── DQ Gate Function ────────────────────────────────
def run_dq_gate(**context) -> str:
    """Run data-quality checks; return branch based on result."""
    from google.cloud import bigquery
    client = bigquery.Client(project=PROJECT_ID)

    query = """
        SELECT
          COUNTIF(order_id IS NULL) AS null_ids,
          COUNT(*) - COUNT(DISTINCT order_id) AS dup_ids,
          COUNTIF(amount <= 0) AS bad_amounts
        FROM `{}.silver.clean_orders`
        WHERE DATE(ingested_at) = @run_date
    """.format(PROJECT_ID)

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter(
                "run_date", "DATE", context["ds"]
            )
        ]
    )
    rows = list(client.query(query, job_config=job_config).result())
    r = rows[0]

    if r.null_ids == 0 and r.dup_ids == 0 and r.bad_amounts == 0:
        return "dq_pass"

    context["task_instance"].xcom_push(
        key="dq_failures",
        value={"nulls": r.null_ids, "dups": r.dup_ids, "bad": r.bad_amounts},
    )
    return "dq_fail"

def raise_dq_alert(**context):
    failures = context["task_instance"].xcom_pull(
        task_ids="run_dq_gate", key="dq_failures"
    )
    raise ValueError(f"DQ gate failed: {failures}")

# ─── DAG ─────────────────────────────────────────────
with DAG(
    dag_id="poc_medallion_pipeline",
    default_args=DEFAULT_ARGS,
    description="Bronze → Silver → Gold with DQ gates",
    schedule="0 2 * * *",       # daily at 02:00 UTC
    catchup=False,
    max_active_runs=1,
    tags=["poc", "medallion", "gcp"],
) as dag:

    # ── 1. Ingest to Bronze (Dataflow batch) ─────────
    ingest_bronze = DataprocCreateBatchOperator(
        task_id="ingest_bronze",
        project_id=PROJECT_ID,
        region=REGION,
        batch={
            "pyspark_batch": {
                "main_python_file_uri": f"gs://{SCRIPTS_BUCKET}/bronze/ingest_orders.py",
                "args": [
                    "--date", "{{ ds }}",
                    "--output", f"gs://{BRONZE_BUCKET}/orders/{{{{ ds }}}}/",
                ],
            },
            "environment_config": {
                "execution_config": {
                    "service_account": f"poc-pipeline@{PROJECT_ID}.iam.gserviceaccount.com",
                }
            },
        },
        batch_id="ingest-bronze-{{ ds_nodash }}",
    )

    # ── 2. Bronze → Silver (Dataproc Serverless) ─────
    bronze_to_silver = DataprocCreateBatchOperator(
        task_id="bronze_to_silver",
        project_id=PROJECT_ID,
        region=REGION,
        batch={
            "pyspark_batch": {
                "main_python_file_uri": f"gs://{SCRIPTS_BUCKET}/silver/b2s_orders.py",
                "args": ["--date", "{{ ds }}"],
            },
            "environment_config": {
                "execution_config": {
                    "service_account": f"poc-pipeline@{PROJECT_ID}.iam.gserviceaccount.com",
                }
            },
        },
        batch_id="b2s-orders-{{ ds_nodash }}",
    )

    # ── 3. DQ Gate (branch) ──────────────────────────
    dq_gate = BranchPythonOperator(
        task_id="run_dq_gate",
        python_callable=run_dq_gate,
        provide_context=True,
    )

    dq_pass = BashOperator(
        task_id="dq_pass",
        bash_command='echo "DQ passed for {{ ds }}"',
    )

    dq_fail = PythonOperator(
        task_id="dq_fail",
        python_callable=raise_dq_alert,
        provide_context=True,
    )

    # ── 4. Silver → Gold (BigQuery SQL) ──────────────
    silver_to_gold = BigQueryInsertJobOperator(
        task_id="silver_to_gold",
        configuration={
            "query": {
                "query": """
                    CREATE OR REPLACE TABLE `{project}.gold.daily_revenue_{ds_nodash}`
                    PARTITION BY order_date
                    CLUSTER BY region, category AS
                    SELECT
                      DATE(o.order_ts) AS order_date,
                      c.region,
                      p.category,
                      SUM(o.amount) AS revenue,
                      COUNT(DISTINCT o.order_id) AS orders
                    FROM `{project}.silver.clean_orders` o
                    JOIN `{project}.silver.clean_customers` c USING (customer_id)
                    JOIN `{project}.silver.clean_products` p USING (product_id)
                    WHERE DATE(o.order_ts) = '{{ ds }}'
                    GROUP BY 1,2,3
                """.format(project=PROJECT_ID),
                "useLegacySql": False,
            }
        },
        trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS,
    )

    # ── 5. Refresh BI view ───────────────────────────
    refresh_bi = BashOperator(
        task_id="refresh_bi_view",
        bash_command='echo "Triggering Looker PDT refresh for {{ ds }}"',
        trigger_rule=TriggerRule.ALL_SUCCESS,
    )

    # ── Dependencies ─────────────────────────────────
    ingest_bronze >> bronze_to_silver >> dq_gate
    dq_gate >> dq_pass >> silver_to_gold >> refresh_bi
    dq_gate >> dq_fail
