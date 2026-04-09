# ──────────────────────────────────────────────
# ZROKY Infrastructure — Root Module
# ──────────────────────────────────────────────

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# ── Networking ────────────────────────────────
module "networking" {
  source = "./modules/networking"

  project_id  = var.project_id
  region      = var.region
  environment = var.environment
}

# ── GKE Cluster ───────────────────────────────
module "gke" {
  source = "./modules/gke"

  project_id  = var.project_id
  region      = var.region
  environment = var.environment
  network     = module.networking.network_name
  subnetwork  = module.networking.subnet_name

  depends_on = [module.networking]
}

# ── Cloud SQL (PostgreSQL) ────────────────────
module "cloudsql" {
  source = "./modules/cloudsql"

  project_id    = var.project_id
  region        = var.region
  environment   = var.environment
  network_id    = module.networking.network_id
  db_tier       = var.db_tier
  db_password   = var.db_password

  depends_on = [module.networking]
}

# ── Redis (Memorystore) ──────────────────────
module "redis" {
  source = "./modules/redis"

  project_id    = var.project_id
  region        = var.region
  environment   = var.environment
  network_id    = module.networking.network_id
  redis_memory  = var.redis_memory_gb

  depends_on = [module.networking]
}

# ── Cloud Pub/Sub ────────────────────────────
module "pubsub" {
  source = "./modules/pubsub"

  project_id  = var.project_id
  environment = var.environment
}

# ── Kubernetes provider (post-GKE) ──────────
provider "kubernetes" {
  host                   = "https://${module.gke.cluster_endpoint}"
  token                  = data.google_client_config.default.access_token
  cluster_ca_certificate = base64decode(module.gke.cluster_ca_certificate)
}

data "google_client_config" "default" {}
