.PHONY: help generate-data deploy-gcp deploy-aws deploy-azure deploy-dbx \
        benchmark render-diagrams teardown-all lint

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	 awk 'BEGIN {FS = ":.*?## "}; {printf "%-20s %s\n", $$1, $$2}'

generate-data: ## Generate 10K sample records
	cd sample-data && pip install -r requirements.txt && python generate.py

deploy-gcp: ## Deploy GCP POC
	cd poc-gcp/terraform && terraform init && terraform apply -auto-approve

deploy-aws: ## Deploy AWS POC
	cd poc-aws/terraform && terraform init && terraform apply -auto-approve

deploy-azure: ## Deploy Azure POC
	cd poc-azure/terraform && terraform init && terraform apply -auto-approve

deploy-dbx: ## Deploy Databricks POC
	cd poc-databricks && databricks bundle deploy -t dev

benchmark: ## Run all vendor benchmarks
	bash scripts/run-all-benchmarks.sh

render-diagrams: ## Render Mermaid .mmd files to SVG
	bash scripts/render-mermaid.sh

teardown-all: ## Destroy all POCs
	cd poc-gcp/terraform && terraform destroy -auto-approve || true
	cd poc-aws/terraform && terraform destroy -auto-approve || true
	cd poc-azure/terraform && terraform destroy -auto-approve || true

lint: ## Lint Mermaid + Python
	bash scripts/render-mermaid.sh --validate-only
	ruff check sample-data/ poc-*/pipelines/
