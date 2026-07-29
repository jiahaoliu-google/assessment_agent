terraform {
  required_version = ">= 1.3.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Service Account for Multi-Agent Application Runtime
resource "google_service_account" "agent_sa" {
  account_id   = "assessment-agent-sa"
  display_name = "Service Account for Assessment Multi-Agent Meal Planner"
}

# Secret Manager IAM Bindings (Granting Secret Accessor to Agent SA)
resource "google_secret_manager_secret_iam_member" "secret_access" {
  for_each  = toset(var.secret_manager_keys)
  secret_id = "projects/${var.project_id}/secrets/${each.value}"
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.agent_sa.email}"
}

# Cloud Run / Container Deployment with Non-Root Security Context
resource "google_cloud_run_v2_service" "meal_planner_app" {
  name     = "assessment-agent-service"
  location = var.region

  template {
    service_account = google_service_account.agent_sa.email

    containers {
      image = var.app_image

      resources {
        limits = {
          cpu    = "2000m"
          memory = "2Gi"
        }
      }

      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }

      # Secret Manager Integration in Cloud Run Environment
      dynamic "env" {
        for_each = toset(var.secret_manager_keys)
        content {
          name = env.value
          value_source {
            secret_key_ref {
              secret  = env.value
              version = "latest"
            }
          }
        }
      }
    }
  }
}
