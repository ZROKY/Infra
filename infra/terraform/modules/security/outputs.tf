output "ssl_policy_name" {
  description = "Name of the TLS 1.3 SSL policy"
  value       = google_compute_ssl_policy.tls13.name
}

output "waf_policy_name" {
  description = "Name of the Cloud Armor WAF policy"
  value       = google_compute_security_policy.waf.name
}

output "ssl_certificate_name" {
  description = "Name of the managed SSL certificate"
  value       = google_compute_managed_ssl_certificate.api.name
}

output "https_redirect_map_name" {
  description = "Name of the HTTPS redirect URL map"
  value       = google_compute_url_map.https_redirect.name
}
