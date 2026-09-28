terraform {
  backend "gcs" {
    bucket = "poc-tfstate"
    prefix = "env/dev"
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
  environment             = "dev"
  
  bronze_bucket_name      = "${var.project_id}-bronze"
  bronze_retention_days   = 30
  
  dataproc_worker_count   = 2
  dataproc_machine_type   = "n1-standard-4"
  
  enable_dataplex         = true
  enable_policy_tags      = false
  datasets                = ["silver", "gold"]

  labels = {
    owner       = "data-platform-team"
    cost_center = "poc"
  }
}

output "bronze_bucket" {
  value = module.data_platform.bronze_bucket
}
