variable "project_id" {
  type        = string
  description = "GCP project ID"
}

variable "region" {
  type        = string
  default     = "us-central1"
}

variable "environment" {
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Must be dev, staging, or prod."
  }
}

variable "bronze_bucket_name" {
  type = string
}

variable "bronze_retention_days" {
  type    = number
  default = 90
}

variable "dataproc_worker_count" {
  type    = number
  default = 2
}

variable "dataproc_machine_type" {
  type    = string
  default = "n1-standard-4"
}

variable "dataproc_max_idle_minutes" {
  type    = number
  default = 15
}

variable "enable_dataplex" {
  type    = bool
  default = true
}

variable "enable_policy_tags" {
  type    = bool
  default = false
}

variable "labels" {
  type    = map(string)
  default = {}
}

variable "datasets" {
  type        = list(string)
  description = "BigQuery datasets to create (Silver, Gold)"
  default     = ["silver", "gold"]
}
