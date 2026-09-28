terraform {
  required_version = ">= 1.5"
  required_providers {
    google = { source = "hashicorp/google", version = "~> 5.0" }
  }
}

locals {
  common_labels = merge(var.labels, {
    environment = var.environment
    managed_by  = "terraform"
    module      = "gcp-data-platform"
  })
}

resource "google_project_service" "services" {
  for_each = toset([
    "storage.googleapis.com",
    "bigquery.googleapis.com",
    "dataproc.googleapis.com",
    "dataflow.googleapis.com",
    "pubsub.googleapis.com",
    "datastream.googleapis.com",
    "dataplex.googleapis.com",
    "composer.googleapis.com",
    "iam.googleapis.com",
  ])
  service            = each.key
  disable_on_destroy = false
}
