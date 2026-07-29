variable "project_id" {
  description = "Google Cloud or Cloud Provider Project ID"
  type        = string
  default     = "meal-planner-production"
}

variable "region" {
  description = "Deployment Region"
  type        = string
  default     = "us-central1"
}

variable "app_image" {
  description = "Docker Container Image URI"
  type        = string
  default     = "gcr.io/meal-planner-production/assessment-agent:latest"
}

variable "secret_manager_keys" {
  description = "List of Secret Manager keys to bind"
  type        = list(string)
  default     = ["GEMINI_API_KEY", "OPENAI_API_KEY", "JWT_SECRET_KEY"]
}
