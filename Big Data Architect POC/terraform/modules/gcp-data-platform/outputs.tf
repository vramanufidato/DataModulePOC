output "bronze_bucket" {
  value = google_storage_bucket.bronze.name
}

output "silver_dataset" {
  value = try(google_bigquery_dataset.datasets["silver"].dataset_id, null)
}

output "gold_dataset" {
  value = try(google_bigquery_dataset.datasets["gold"].dataset_id, null)
}

output "pipeline_service_account" {
  value = google_service_account.pipeline.email
}

output "dataproc_cluster_name" {
  value = try(google_dataproc_cluster.spark[0].name, null)
}
