# ──────────────────────────────────────────────
# GKE Cluster + Node Pools
# ──────────────────────────────────────────────

resource "google_container_cluster" "main" {
  name     = "zroky-${var.environment}"
  project  = var.project_id
  location = var.region

  # We manage node pools separately
  remove_default_node_pool = true
  initial_node_count       = 1

  network    = var.network
  subnetwork = var.subnetwork

  ip_allocation_policy {
    cluster_secondary_range_name  = "gke-pods"
    services_secondary_range_name = "gke-services"
  }

  # Workload Identity
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  # Network policy
  network_policy {
    enabled  = true
    provider = "CALICO"
  }

  # Binary Authorization
  binary_authorization {
    evaluation_mode = "PROJECT_SINGLETON_POLICY_ENFORCE"
  }

  # Logging + Monitoring
  logging_config {
    enable_components = ["SYSTEM_COMPONENTS", "WORKLOADS"]
  }

  monitoring_config {
    enable_components = ["SYSTEM_COMPONENTS"]
    managed_prometheus {
      enabled = true
    }
  }

  # Maintenance window (Tue 2am-6am UTC)
  maintenance_policy {
    recurring_window {
      start_time = "2024-01-01T02:00:00Z"
      end_time   = "2024-01-01T06:00:00Z"
      recurrence = "FREQ=WEEKLY;BYDAY=TU"
    }
  }

  release_channel {
    channel = "REGULAR"
  }
}

# ── Primary Node Pool (API + Dashboard + Engines) ──
resource "google_container_node_pool" "primary" {
  name     = "primary"
  project  = var.project_id
  location = var.region
  cluster  = google_container_cluster.main.name

  autoscaling {
    min_node_count = var.environment == "dev" ? 1 : 2
    max_node_count = var.environment == "dev" ? 3 : 10
  }

  node_config {
    machine_type = var.environment == "dev" ? "e2-standard-2" : "e2-standard-4"
    disk_size_gb = 50
    disk_type    = "pd-ssd"

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform",
    ]

    workload_metadata_config {
      mode = "GKE_METADATA"
    }

    labels = {
      environment = var.environment
      team        = "zroky"
    }
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }
}

# ── GPU Node Pool (Safety Judge — Llama-3-8B) ──
resource "google_container_node_pool" "gpu" {
  count    = var.environment == "dev" ? 0 : 1
  name     = "gpu-pool"
  project  = var.project_id
  location = var.region
  cluster  = google_container_cluster.main.name

  autoscaling {
    min_node_count = 0
    max_node_count = 2
  }

  node_config {
    machine_type = "n1-standard-4"
    disk_size_gb = 100
    disk_type    = "pd-ssd"
    spot         = true # Preemptible for cost savings

    guest_accelerator {
      type  = "nvidia-tesla-t4"
      count = 1
      gpu_driver_installation_config {
        gpu_driver_version = "LATEST"
      }
    }

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform",
    ]

    workload_metadata_config {
      mode = "GKE_METADATA"
    }

    labels = {
      environment = var.environment
      gpu         = "true"
    }

    taint {
      key    = "nvidia.com/gpu"
      value  = "present"
      effect = "NO_SCHEDULE"
    }
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }
}
