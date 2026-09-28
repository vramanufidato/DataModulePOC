terraform {
  backend "gcs" {
    bucket = "poc-tfstate"
    prefix = "env/prod"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

module "data_platform" {
  source = "../../modules/gcp-data-platform"
  
  project_id              = var.project_id
  region                  = var.region
  environment             = "prod"
  
  bronze_bucket_name      = "${var.project_id}-bronze"
  bronze_retention_days   = 365
  
  dataproc_worker_count   = 8
  dataproc_machine_type   = "n1-highmem-8"
  
  enable_dataplex         = true
  enable_policy_tags      = true
  datasets                = ["silver", "gold"]

  labels = {
    owner       = "data-platform-team"
    cost_center = "analytics"
    compliance  = "soc2"
  }
}
