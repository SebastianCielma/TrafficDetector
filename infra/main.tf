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
