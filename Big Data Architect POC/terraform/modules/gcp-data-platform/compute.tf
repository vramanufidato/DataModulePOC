resource "google_dataproc_cluster" "spark" {
  count  = var.environment != "prod" ? 0 : 1
  name   = "poc-spark-${var.environment}"
  region = var.region
  labels = local.common_labels

  cluster_config {
    master_config {
      num_instances = 1
      machine_type  = "n1-standard-4"
    }
    worker_config {
      num_instances = var.dataproc_worker_count
      machine_type  = var.dataproc_machine_type
    }
    software_config {
      image_version       = "2.1-debian11"
      optional_components = ["JUPYTER"]
    }
    gce_cluster_config {
      service_account = google_service_account.pipeline.email
      tags            = ["poc", var.environment]
    }
    autoscaling_config {
      policy_uri = ""
    }
  }

  depends_on = [google_project_service.services]
}

resource "google_dataproc_cluster_iam_member" "pipeline" {
  count    = var.environment != "prod" ? 0 : 1
  cluster  = google_dataproc_cluster.spark[0].name
  role     = "roles/dataproc.editor"
  member   = "serviceAccount:${google_service_account.pipeline.email}"
}
