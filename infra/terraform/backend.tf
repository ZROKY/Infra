# ──────────────────────────────────────────────
# Remote State Backend (GCS)
# ──────────────────────────────────────────────
# NOTE: Create the bucket manually first:
#   gsutil mb -l us-central1 gs://zroky-terraform-state
#   gsutil versioning set on gs://zroky-terraform-state

terraform {
  backend "gcs" {
    bucket = "zroky-terraform-state"
    prefix = "infra"
  }
}
