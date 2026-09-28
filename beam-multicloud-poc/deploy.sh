#!/usr/bin/env bash
set -euo pipefail

# ---- EDIT THESE ----
PROJECT_ID="your-project-id"
REGION="us-central1"
BUCKET="gs://your-bucket-poc-staging"
SUBSCRIPTION="projects/${PROJECT_ID}/subscriptions/poc-sub"
OUTPUT_TABLE="${PROJECT_ID}:poc_dataset.events"
JOB_NAME="poc-custom-pipeline-$(date +%Y%m%d-%H%M%S)"
# --------------------

echo "Deploying ${JOB_NAME} to Dataflow..."

python poc_pipeline.py \
  --input_subscription="${SUBSCRIPTION}" \
  --output_table="${OUTPUT_TABLE}" \
  --runner=DataflowRunner \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --temp_location="${BUCKET}/temp" \
  --staging_location="${BUCKET}/staging" \
  --streaming \
  --job_name="${JOB_NAME}"

echo "Job submitted. Monitor at:"
echo "https://console.cloud.google.com/dataflow/jobs/${REGION}/${JOB_NAME}?project=${PROJECT_ID}"
