# ──────────────────────────────────────────────
# Cloud Pub/Sub — 4 engine topics + dead letter
# ──────────────────────────────────────────────

locals {
  engine_topics = [
    "safety-events",
    "grounding-events",
    "consistency-events",
    "system-events",
  ]
}

# ── Dead Letter Topic ──
resource "google_pubsub_topic" "dead_letter" {
  name    = "zroky-${var.environment}-dead-letter"
  project = var.project_id

  message_retention_duration = "604800s" # 7 days

  labels = {
    environment = var.environment
    team        = "zroky"
  }
}

resource "google_pubsub_subscription" "dead_letter" {
  name    = "zroky-${var.environment}-dead-letter-sub"
  project = var.project_id
  topic   = google_pubsub_topic.dead_letter.id

  message_retention_duration = "604800s" # 7 days
  retain_acked_messages      = true
  ack_deadline_seconds       = 60

  labels = {
    environment = var.environment
    team        = "zroky"
  }
}

# ── Engine Topics ──
resource "google_pubsub_topic" "engine" {
  for_each = toset(local.engine_topics)

  name    = "zroky-${var.environment}-${each.value}"
  project = var.project_id

  message_retention_duration = "86400s" # 24 hours

  labels = {
    environment = var.environment
    team        = "zroky"
  }
}

# ── Engine Subscriptions ──
resource "google_pubsub_subscription" "engine" {
  for_each = toset(local.engine_topics)

  name    = "zroky-${var.environment}-${each.value}-sub"
  project = var.project_id
  topic   = google_pubsub_topic.engine[each.value].id

  ack_deadline_seconds       = 30
  message_retention_duration = "86400s"

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }

  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.dead_letter.id
    max_delivery_attempts = 5
  }

  expiration_policy {
    ttl = "" # Never expires
  }

  labels = {
    environment = var.environment
    team        = "zroky"
  }
}
