# ──────────────────────────────────────────────
# Outputs
# ──────────────────────────────────────────────

output "gke_cluster_name" {
  description = "GKE cluster name"
  value       = module.gke.cluster_name
}

output "gke_cluster_endpoint" {
  description = "GKE cluster endpoint"
  value       = module.gke.cluster_endpoint
  sensitive   = true
}

output "cloudsql_connection_name" {
  description = "Cloud SQL connection name for proxy"
  value       = module.cloudsql.connection_name
}

output "cloudsql_private_ip" {
  description = "Cloud SQL private IP"
  value       = module.cloudsql.private_ip
  sensitive   = true
}

output "redis_host" {
  description = "Redis host IP"
  value       = module.redis.host
  sensitive   = true
}

output "redis_port" {
  description = "Redis port"
  value       = module.redis.port
}

output "pubsub_topics" {
  description = "Pub/Sub topic names"
  value       = module.pubsub.topic_names
}

output "network_name" {
  description = "VPC network name"
  value       = module.networking.network_name
}
