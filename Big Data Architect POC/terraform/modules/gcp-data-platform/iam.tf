resource "google_service_account" "pipeline" {
  account_id   = "poc-pipeline-${var.environment}"
  display_name = "POC Pipeline ${var.environment}"
}

resource "google_project_iam_member" "pipeline" {
  for_each = toset([
    "roles/bigquery.dataEditor",
    "roles/storage.objectAdmin",
    "roles/dataproc.editor",
    "roles/dataplex.dataOwner",
  ])
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.pipeline.email}"
}

resource "google_bigquery_datapolicy_data_policy" "pii" {
  count            = var.enable_policy_tags ? 1 : 0
  location         = "US"
  data_policy_id   = "pii-${var.environment}"
  policy_tag       = google_data_catalog_policy_tag.pii[0].id
  data_policy_type = "COLUMN_LEVEL_SECURITY_POLICY"
}

resource "google_data_catalog_policy_tag" "pii" {
  count         = var.enable_policy_tags ? 1 : 0
  taxonomy      = google_data_catalog_taxonomy.security[0].id
  display_name  = "PII"
  description   = "Personally identifiable information"
}

resource "google_data_catalog_taxonomy" "security" {
  count        = var.enable_policy_tags ? 1 : 0
  display_name = "security-${var.environment}"
  description  = "Security taxonomy"
  activated_policy_types = ["FINE_GRAINED_ACCESS_CONTROL"]
}
