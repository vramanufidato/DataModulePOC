# GCP Data Platform POC

BigQuery + Dataproc Serverless + Dataplex, following Medallion architecture.

## Architecture
![GCP Architecture](../diagrams/rendered/05-gcp-architecture.svg)

## Deploy
```bash
cd terraform && terraform init && terraform apply
```

## Run Pipelines
```bash
gsutil cp pipelines/** gs://<bucket>-scripts/
gcloud dataproc batches submit pyspark pipelines/silver/b2s_orders.py
```

## Cost
See cost-model.csv — GCP column.
