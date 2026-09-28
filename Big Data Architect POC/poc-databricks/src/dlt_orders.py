# Databricks notebook source
# DLT pipeline: orders Bronze → Silver → Gold
import dlt
from pyspark.sql.functions import col, to_timestamp, current_timestamp

LANDING = spark.conf.get("landing.path") + "/orders"
BRONZE_SCHEMA = spark.conf.get("bronze.schema")
GOLD_SCHEMA = spark.conf.get("gold.schema")

@dlt.table(
    name=f"{BRONZE_SCHEMA}.orders",
    comment="Raw orders from Auto Loader",
    table_properties={"quality": "bronze"},
)
def bronze_orders():
    return (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.schemaLocation", f"{LANDING}/_schemas")
        .option("cloudFiles.inferColumnTypes", "true")
        .load(LANDING)
    )

@dlt.table(
    name="clean_orders",
    comment="Cleansed and deduplicated orders",
    table_properties={"quality": "silver"},
)
@dlt.expect_or_drop("valid_order_id", "order_id IS NOT NULL")
@dlt.expect_or_drop("positive_amount", "amount > 0")
@dlt.expect("recent", "order_ts >= current_timestamp() - INTERVAL 30 DAYS")
def silver_orders():
    return (
        dlt.read_stream(f"{BRONZE_SCHEMA}.orders")
        .dropDuplicates(["order_id"])
        .withColumn("order_ts", to_timestamp("order_ts"))
        .withColumn("ingested_at", current_timestamp())
    )

@dlt.table(
    name=f"{GOLD_SCHEMA}.daily_revenue",
    comment="Daily revenue by region and category",
    table_properties={"quality": "gold"},
    partition_cols=["order_date"],
)
def gold_daily_revenue():
    orders = dlt.read("clean_orders")
    customers = dlt.read("clean_customers")
    products = dlt.read("clean_products")

    return (
        orders.join(customers, "customer_id")
        .join(products, "product_id")
        .groupBy("order_date", "region", "category")
        .agg({"amount": "sum", "order_id": "count"})
    )
