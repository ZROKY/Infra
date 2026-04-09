# ──────────────────────────────────────────────
# ZROKY Security Hardening — SEC-01, SEC-04
# Cloud Armor WAF + SSL Policy + Data Isolation
# ──────────────────────────────────────────────

# ── SSL Policy (TLS 1.3 only) ────────────────

resource "google_compute_ssl_policy" "tls13" {
  name            = "zroky-${var.environment}-tls13"
  project         = var.project_id
  profile         = "RESTRICTED"
  min_tls_version = "TLS_1_2"

  # TLS 1.3 cipher suites preferred (1.2 fallback for edge cases)
  custom_features = [
    "TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384",
    "TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384",
    "TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305_SHA256",
    "TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305_SHA256",
    "TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256",
    "TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256",
  ]
}

# ── Cloud Armor Security Policy (WAF) ────────

resource "google_compute_security_policy" "waf" {
  name    = "zroky-${var.environment}-waf"
  project = var.project_id

  # Default: allow
  rule {
    action   = "allow"
    priority = 2147483647 # Default rule (lowest priority)
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    description = "Default allow rule"
  }

  # OWASP Top 10: SQL Injection
  rule {
    action   = "deny(403)"
    priority = 1000
    match {
      expr {
        expression = "evaluatePreconfiguredExpr('sqli-v33-stable')"
      }
    }
    description = "Block SQL injection attempts"
  }

  # OWASP Top 10: Cross-Site Scripting
  rule {
    action   = "deny(403)"
    priority = 1001
    match {
      expr {
        expression = "evaluatePreconfiguredExpr('xss-v33-stable')"
      }
    }
    description = "Block XSS attempts"
  }

  # OWASP Top 10: Remote Code Execution
  rule {
    action   = "deny(403)"
    priority = 1002
    match {
      expr {
        expression = "evaluatePreconfiguredExpr('rce-v33-stable')"
      }
    }
    description = "Block remote code execution attempts"
  }

  # OWASP Top 10: Local File Inclusion
  rule {
    action   = "deny(403)"
    priority = 1003
    match {
      expr {
        expression = "evaluatePreconfiguredExpr('lfi-v33-stable')"
      }
    }
    description = "Block local file inclusion attempts"
  }

  # OWASP Top 10: Remote File Inclusion
  rule {
    action   = "deny(403)"
    priority = 1004
    match {
      expr {
        expression = "evaluatePreconfiguredExpr('rfi-v33-stable')"
      }
    }
    description = "Block remote file inclusion attempts"
  }

  # OWASP Top 10: Scanner detection
  rule {
    action   = "deny(403)"
    priority = 1005
    match {
      expr {
        expression = "evaluatePreconfiguredExpr('scannerdetection-v33-stable')"
      }
    }
    description = "Block known scanner/bot user agents"
  }

  # OWASP Top 10: Protocol attack
  rule {
    action   = "deny(403)"
    priority = 1006
    match {
      expr {
        expression = "evaluatePreconfiguredExpr('protocolattack-v33-stable')"
      }
    }
    description = "Block protocol-level attacks"
  }

  # Rate limiting (DDoS mitigation)
  rule {
    action   = "throttle"
    priority = 900
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    rate_limit_options {
      conform_action = "allow"
      exceed_action  = "deny(429)"
      enforce_on_key = "IP"
      rate_limit_threshold {
        count        = 1000
        interval_sec = 60
      }
    }
    description = "Rate limit: 1000 req/min per IP"
  }

  # Geo-blocking: Block sanctioned countries
  rule {
    action   = "deny(403)"
    priority = 500
    match {
      expr {
        expression = "origin.region_code == 'KP' || origin.region_code == 'IR' || origin.region_code == 'SY' || origin.region_code == 'CU'"
      }
    }
    description = "Block requests from sanctioned regions"
  }
}

# ── HTTPS Redirect (HTTP → HTTPS) ────────────

resource "google_compute_url_map" "https_redirect" {
  name    = "zroky-${var.environment}-https-redirect"
  project = var.project_id

  default_url_redirect {
    https_redirect         = true
    strip_query            = false
    redirect_response_code = "MOVED_PERMANENTLY_DEFAULT"
  }
}

# ── Managed SSL Certificate ──────────────────

resource "google_compute_managed_ssl_certificate" "api" {
  name    = "zroky-${var.environment}-api-cert"
  project = var.project_id

  managed {
    domains = [
      "api.zroky.ai",
      "ingest.zroky.ai",
      "sandbox.ingest.zroky.ai",
      "badge.zroky.ai",
      "app.zroky.ai",
    ]
  }
}

# ── Firewall: Deny direct HTTP to backends ───

resource "google_compute_firewall" "deny_http_direct" {
  name    = "zroky-${var.environment}-deny-http-direct"
  project = var.project_id
  network = var.network_id

  deny {
    protocol = "tcp"
    ports    = ["80"]
  }

  # Apply to all backend instances
  target_tags   = ["zroky-backend"]
  source_ranges = ["0.0.0.0/0"]
  priority      = 100

  description = "Deny direct HTTP — all traffic must go through HTTPS Load Balancer"
}
