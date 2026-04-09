# ──────────────────────────────────────────────
# Memorystore Redis 7.x
# ──────────────────────────────────────────────

resource "google_redis_instance" "main" {
  name               = "zroky-${var.environment}-redis"
  project            = var.project_id
  region             = var.region
  tier               = var.environment == "prod" ? "STANDARD_HA" : "BASIC"
  memory_size_gb     = var.redis_memory
  redis_version      = "REDIS_7_0"
  authorized_network = var.network_id

  auth_enabled            = true
  transit_encryption_mode = "SERVER_AUTHENTICATION"

  redis_configs = {
    maxmemory-policy = "allkeys-lru"
    notify-keyspace-events = ""
  }

  maintenance_policy {
    weekly_maintenance_window {
      day = "WEDNESDAY"
      start_time {
        hours   = 3
        minutes = 0
        seconds = 0
        nanos   = 0
      }
    }
  }

  labels = {
    environment = var.environment
    team        = "zroky"
  }
}
