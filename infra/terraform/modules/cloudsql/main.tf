# ──────────────────────────────────────────────
# Cloud SQL — PostgreSQL 15
# ──────────────────────────────────────────────

resource "google_sql_database_instance" "main" {
  name                = "zroky-${var.environment}-pg"
  project             = var.project_id
  region              = var.region
  database_version    = "POSTGRES_15"
  deletion_protection = var.environment == "prod" ? true : false

  settings {
    tier              = var.db_tier
    availability_type = var.environment == "prod" ? "REGIONAL" : "ZONAL"
    disk_type         = "PD_SSD"
    disk_size         = var.environment == "dev" ? 10 : 50
    disk_autoresize   = true

    ip_configuration {
      ipv4_enabled                                  = false
      private_network                               = var.network_id
      enable_private_path_for_google_cloud_services = true
    }

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = true
      start_time                     = "03:00"
      transaction_log_retention_days = var.environment == "prod" ? 7 : 3

      backup_retention_settings {
        retained_backups = var.environment == "prod" ? 30 : 7
      }
    }

    maintenance_window {
      day          = 3 # Wednesday
      hour         = 3 # 3 AM UTC
      update_track = "stable"
    }

    database_flags {
      name  = "log_min_duration_statement"
      value = "1000" # Log queries > 1s
    }

    database_flags {
      name  = "max_connections"
      value = var.environment == "dev" ? "50" : "200"
    }

    insights_config {
      query_insights_enabled  = true
      query_plans_per_minute  = 5
      query_string_length     = 1024
      record_application_tags = true
      record_client_address   = false
    }
  }
}

# ── Databases ──
resource "google_sql_database" "zroky" {
  name     = "zroky"
  project  = var.project_id
  instance = google_sql_database_instance.main.name
}

resource "google_sql_database" "zroky_test" {
  count    = var.environment == "dev" ? 1 : 0
  name     = "zroky_test"
  project  = var.project_id
  instance = google_sql_database_instance.main.name
}

# ── Users ──
resource "google_sql_user" "admin" {
  name     = "zroky_admin"
  project  = var.project_id
  instance = google_sql_database_instance.main.name
  password = var.db_password
}

resource "google_sql_user" "app" {
  name     = "zroky_app"
  project  = var.project_id
  instance = google_sql_database_instance.main.name
  password = var.db_password # In prod, use separate secrets
}
