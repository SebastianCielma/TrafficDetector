terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

resource "google_project_service" "artifact_registry" {
  service = "artifactregistry.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "cloud_run" {
  service = "run.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "iam" {
  service = "iam.googleapis.com"
  disable_on_destroy = false
}

resource "google_artifact_registry_repository" "repo" {
  location      = var.region
  repository_id = "traffic-repo"
  description   = "Docker repository for Traffic AI"
  format        = "DOCKER"

  depends_on = [google_project_service.artifact_registry]
}

# ---------------------------------------------------------
# GCS + BigQuery
# ---------------------------------------------------------

resource "google_storage_bucket" "analytics_lake" {
  name          = "${var.project_id}-analytics-data"
  location      = var.region
  force_destroy = false

  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }
}

resource "google_bigquery_dataset" "traffic_warehouse" {
  dataset_id                  = "traffic_analytics"
  friendly_name               = "Traffic Analytics Warehouse"
  description                 = "Central repository for traffic detection data"
  location                    = var.region

  delete_contents_on_destroy = false
}

# ---------------------------------------------------------
# SECURITY & IAM (Least Privilege)
# ---------------------------------------------------------

resource "google_storage_bucket_iam_member" "app_gcs_writer" {
  bucket = google_storage_bucket.analytics_lake.name
  role   = "roles/storage.objectUser"
  member = "serviceAccount:${google_service_account.github_actions.email}"
}

resource "google_bigquery_dataset_access" "app_bq_writer" {
  dataset_id    = google_bigquery_dataset.traffic_warehouse.dataset_id
  role          = "WRITER"
  user_by_email = google_service_account.github_actions.email
}
