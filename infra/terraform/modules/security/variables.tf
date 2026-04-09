variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "environment" {
  description = "Environment name (staging, production)"
  type        = string
  default     = "production"
}

variable "network_id" {
  description = "VPC network self_link for firewall rules"
  type        = string
}
