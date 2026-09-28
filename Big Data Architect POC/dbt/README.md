# dbt Project — Medallion Silver → Gold
Portable dbt models that run against BigQuery, Redshift, Synapse, or Databricks.

## Quick Start
```bash
cd dbt
pip install -r requirements.txt
dbt deps

# Pick a target
dbt debug --target gcp
dbt run   --target gcp
dbt test  --target gcp
```

## Targets
| Target   | Adapter   | Warehouse   |
| gcp   | dbt-bigquery   | BigQuery   |
| aws   | dbt-redshift   | Redshift   |
| azure   | dbt-synapse   | Synapse Dedicated   |
| databricks   | dbt-databricks   | Databricks SQL Warehouse   |

## Layers
- `models/staging/` — Silver-layer cleanses (1:1 with Bronze sources)
- `models/marts/` — Gold-layer aggregates + star schemas
- `models/metrics/` — Semantic-layer metric definitions
