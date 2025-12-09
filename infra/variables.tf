variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "europe-west1"
}

variable "github_repo" {
  description = "GitHub Repository name (format: User/Repo)"
  type        = string
  default     = "sebastiancielma/trafficdetector"
}
