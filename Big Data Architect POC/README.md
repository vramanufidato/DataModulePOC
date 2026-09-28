# Multi-Cloud Data Platform POC

A production-grade POC of a Medallion-architecture data platform implemented
on GCP, AWS, Azure, and Databricks — with identical business scenarios,
pipelines, governance, and DQ frameworks.

## Blog Series
Ten-part series documenting design, implementation, and comparison.
→ [docs/blog-series/](docs/blog-series/)

## POCs
- [GCP](./poc-gcp/) — BigQuery + Dataproc + Dataplex
- [AWS](./poc-aws/) — S3 + Glue + Iceberg + Redshift
- [Azure](./poc-azure/) — ADLS + Databricks + Synapse
- [Databricks](./poc-databricks/) — Delta + DLT + Unity Catalog

## Quick Start
```bash
make generate-data   # Generate 10K sample records
make deploy-gcp      # Deploy GCP POC
make deploy-aws      # Deploy AWS POC
make deploy-azure    # Deploy Azure POC
make deploy-dbx      # Deploy Databricks POC
make benchmark       # Run cross-vendor benchmarks
make render-diagrams # Render all Mermaid diagrams to SVG
```

## Diagram Preview
All architecture diagrams are stored as Mermaid `.mmd` files in `diagrams/` and rendered inline in blog posts.

## License
MIT
