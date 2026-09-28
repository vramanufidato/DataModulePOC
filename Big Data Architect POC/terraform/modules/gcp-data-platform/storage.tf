resource "google_storage_bucket" "bronze" {
  name                        = var.bronze_bucket_name
  location                    = var.region
  force_destroy               = var.environment != "prod"
  uniform_bucket_level_access = true
  labels                      = local.common_labels

  lifecycle_rule {
    condition { age = var.bronze_retention_days }
    action    { type = "SetStorageClass" storage_class = "NEARLINE" }
  }
  lifecycle_rule {
    condition { age = var.bronze_retention_days * 4 }
    action    { type = "SetStorageClass" storage_class = "COLDLINE" }
  }
  versioning { enabled = var.environment == "prod" }
}

resource "google_bigquery_dataset" "datasets" {
  for_each   = toset(var.datasets)
  dataset_id = each.key
  location   = "US"
  labels     = local.common_labels
}
