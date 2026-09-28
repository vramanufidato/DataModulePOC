"""
Cross-vendor query benchmark driver.
Runs the same set of analytical queries against GCP, AWS, Azure, and
Databricks and records latency, throughput, and error rates.

Run:
    locust -f locustfile.py --headless -u 50 -r 5 -t 5m \
        --csv=results/benchmark --only-summary

Environment variables (see .env.example):
    GCP_PROJECT_ID, AWS_REGION, AZURE_SYNAPSE_HOST, DATABRICKS_HOST, ...
"""
from __future__ import annotations

import os
import random
import time
from typing import Any, Callable

from locust import User, between, events, task
from locust.env import Environment

# ─── Vendors ─────────────────────────────────────────
VENDOR = os.getenv("BENCH_VENDOR", "gcp").lower()
QUERY_TIMEOUT = int(os.getenv("BENCH_QUERY_TIMEOUT", "60"))

# ─── Query definitions (identical semantics across vendors) ────
QUERIES: dict[str, str] = {
    "daily_revenue_by_region": """
        SELECT region, SUM(amount) AS revenue
        FROM {schema}.clean_orders
        WHERE DATE(order_ts) = CURRENT_DATE()
        GROUP BY region
    """,
    "top_products": """
        SELECT product_id, SUM(amount) AS revenue
        FROM {schema}.clean_orders
        WHERE DATE(order_ts) BETWEEN CURRENT_DATE() - 7 AND CURRENT_DATE()
        GROUP BY product_id
        ORDER BY revenue DESC
        LIMIT 20
    """,
    "customer_ltv": """
        SELECT c.customer_id, c.tier, SUM(o.amount) AS ltv
        FROM {schema}.clean_orders o
        JOIN {schema}.clean_customers c USING (customer_id)
        GROUP BY c.customer_id, c.tier
        ORDER BY ltv DESC
        LIMIT 100
    """,
    "hourly_trend": """
        SELECT DATE_TRUNC('hour', order_ts) AS hour, COUNT(*) AS orders
        FROM {schema}.clean_orders
        WHERE DATE(order_ts) = CURRENT_DATE()
        GROUP BY 1
        ORDER BY 1
    """,
    "region_category_matrix": """
        SELECT c.region, p.category, SUM(o.amount) AS revenue
        FROM {schema}.clean_orders o
        JOIN {schema}.clean_customers c USING (customer_id)
        JOIN {schema}.clean_products  p USING (product_id)
        WHERE DATE(o.order_ts) >= CURRENT_DATE() - 30
        GROUP BY 1, 2
    """,
}

# ─── Vendor adapters ─────────────────────────────────
class GCPAdapter:
    def __init__(self):
        from google.cloud import bigquery
        self.client = bigquery.Client(project=os.environ["GCP_PROJECT_ID"])
        self.schema = os.getenv("GCP_SCHEMA", "`poc.silver`")

    def execute(self, sql: str) -> int:
        job = self.client.query(sql.format(schema=self.schema))
        rows = list(job.result(timeout=QUERY_TIMEOUT))
        return len(rows)

class AWSAdapter:
    def __init__(self):
        import boto3
        self.client = boto3.client("athena", region_name=os.getenv("AWS_REGION", "us-east-1"))
        self.database = os.getenv("AWS_DATABASE", "poc_silver")
        self.output = os.getenv("AWS_ATHENA_OUTPUT", "s3://poc-athena-results/")

    def execute(self, sql: str) -> int:
        q = self.client.start_query_execution(
            QueryString=sql.format(schema=self.database),
            ResultConfiguration={"OutputLocation": self.output},
        )
        qid = q["QueryExecutionId"]

        deadline = time.time() + QUERY_TIMEOUT
        while time.time() < deadline:
            status = self.client.get_query_execution(QueryExecutionId=qid)
            state = status["QueryExecution"]["Status"]["State"]
            if state in ("SUCCEEDED", "FAILED", "CANCELLED"):
                if state != "SUCCEEDED":
                    raise RuntimeError(f"Athena query {state}")
                return 1
            time.sleep(0.5)
        raise TimeoutError("Athena query timeout")

class AzureAdapter:
    def __init__(self):
        import pyodbc
        conn_str = (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={os.environ['AZURE_SYNAPSE_HOST']};"
            f"DATABASE={os.getenv('AZURE_SYNAPSE_DB', 'poc')};"
            f"UID={os.environ['AZURE_SYNAPSE_USER']};"
            f"PWD={os.environ['AZURE_SYNAPSE_PASSWORD']};"
            "Encrypt=yes;TrustServerCertificate=no;"
        )
        self.conn = pyodbc.connect(conn_str, timeout=QUERY_TIMEOUT)
        self.schema = os.getenv("AZURE_SCHEMA", "silver")

    def execute(self, sql: str) -> int:
        with self.conn.cursor() as cur:
            cur.execute(sql.format(schema=self.schema))
            return len(cur.fetchall())

class DatabricksAdapter:
    def __init__(self):
        from databricks import sql as dbsql
        self.conn = dbsql.connect(
            server_hostname=os.environ["DATABRICKS_HOST"].replace("https://", ""),
            http_path=os.environ["DATABRICKS_HTTP_PATH"],
            access_token=os.environ["DATABRICKS_TOKEN"],
        )
        self.schema = os.getenv("DATABRICKS_SCHEMA", "poc.silver")

    def execute(self, sql: str) -> int:
        with self.conn.cursor() as cur:
            cur.execute(sql.format(schema=self.schema))
            return len(cur.fetchall())

ADAPTERS: dict[str, Callable[[], Any]] = {
    "gcp": GCPAdapter,
    "aws": AWSAdapter,
    "azure": AzureAdapter,
    "databricks": DatabricksAdapter,
}

# ─── Locust User ─────────────────────────────────────
class QueryUser(User):
    """Simulates a BI analyst running ad-hoc queries."""
    wait_time = between(1, 3)

    def __init__(self, environment: Environment):
        super().__init__(environment)
        self.adapter = ADAPTERS[VENDOR]()

    @task(5)
    def daily_revenue(self):
        self._run("daily_revenue_by_region")

    @task(3)
    def top_products(self):
        self._run("top_products")

    @task(2)
    def customer_ltv(self):
        self._run("customer_ltv")

    @task(2)
    def hourly_trend(self):
        self._run("hourly_trend")

    @task(1)
    def region_category_matrix(self):
        self._run("region_category_matrix")

    def _run(self, query_name: str) -> None:
        sql = QUERIES[query_name]
        start = time.perf_counter()
        try:
            rows = self.adapter.execute(sql)
            elapsed_ms = (time.perf_counter() - start) * 1000
            events.request.fire(
                request_type=f"query/{VENDOR}",
                name=query_name,
                response_time=elapsed_ms,
                response_length=rows,
                exception=None,
                context={},
            )
        except Exception as exc:  # noqa: BLE001
            elapsed_ms = (time.perf_counter() - start) * 1000
            events.request.fire(
                request_type=f"query/{VENDOR}",
                name=query_name,
                response_time=elapsed_ms,
                response_length=0,
                exception=exc,
                context={},
            )
