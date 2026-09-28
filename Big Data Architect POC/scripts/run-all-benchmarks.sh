#!/usr/bin/env bash
set -euo pipefail

echo "Running benchmarks across all vendors..."
mkdir -p benchmarks/results

for vendor in gcp aws azure databricks; do
  echo "→ $vendor"
  case "$vendor" in
    gcp)       bash poc-gcp/benchmarks/run.sh > benchmarks/results/gcp.csv ;;
    aws)       bash poc-aws/benchmarks/run.sh > benchmarks/results/aws.csv ;;
    azure)     bash poc-azure/benchmarks/run.sh > benchmarks/results/azure.csv ;;
    databricks) bash poc-databricks/benchmarks/run.sh > benchmarks/results/databricks.csv ;;
  esac
done

echo "Done. Results in benchmarks/results/"
