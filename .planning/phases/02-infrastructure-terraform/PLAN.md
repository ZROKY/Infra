# Phase 2 — Infrastructure (Terraform + Databases)

**Goal:** All GCP infrastructure provisioned via Terraform — GKE, Cloud SQL, ClickHouse, Redis, Pub/Sub
**Requirements:** INFRA-01, INFRA-02, INFRA-03, INFRA-04, INFRA-05, INFRA-06
**Success criteria:** `terraform plan` clean, all modules defined, local docker-compose verified

---

## Plan 1: Terraform Project Structure + Provider Config
**Wave:** 1
**Files:**
```
infra/terraform/
  main.tf              # Root module — calls all child modules
  variables.tf         # Input variables (project_id, region, env)
  outputs.tf           # Output values (cluster endpoint, DB URLs)
  versions.tf          # Provider + Terraform version constraints
  terraform.tfvars.example  # Example variable values
  backend.tf           # GCS remote state backend
  environments/
    dev.tfvars          # Dev environment overrides
    staging.tfvars      # Staging overrides
    prod.tfvars         # Production overrides
```

## Plan 2: GKE Cluster Module
**Wave:** 2 (depends on Plan 1)
**Files:**
```
infra/terraform/modules/gke/
  main.tf              # GKE cluster + node pools
  variables.tf
  outputs.tf
```
- Regional cluster (us-central1)
- Node pool: e2-standard-4, 2-5 nodes auto-scaling
- GPU node pool: n1-standard-4 + T4 GPU (for Safety Judge, preemptible)
- Workload Identity enabled
- Network policy enabled

## Plan 3: Cloud SQL (PostgreSQL) Module
**Wave:** 2 (parallel with Plan 2)
**Files:**
```
infra/terraform/modules/cloudsql/
  main.tf              # Cloud SQL instance + databases
  variables.tf
  outputs.tf
```
- PostgreSQL 15, db-f1-micro (dev) / db-custom-2-8192 (prod)
- Private IP networking
- Automated backups, point-in-time recovery
- 2 databases: zroky_main, zroky_test

## Plan 4: Redis (Memorystore) Module
**Wave:** 2 (parallel)
**Files:**
```
infra/terraform/modules/redis/
  main.tf
  variables.tf
  outputs.tf
```
- Memorystore Redis 7.x
- 1GB (dev) / 5GB (prod)
- Private service access
- AUTH enabled

## Plan 5: Cloud Pub/Sub Module
**Wave:** 2 (parallel)
**Files:**
```
infra/terraform/modules/pubsub/
  main.tf
  variables.tf
  outputs.tf
```
- 4 topics: safety-events, grounding-events, consistency-events, system-events
- 4 subscriptions (one per engine)
- Dead letter topic for failed messages
- Message retention: 7 days

## Plan 6: Networking Module (VPC + Firewall)
**Wave:** 1 (Plan 2-5 depend on this)
**Files:**
```
infra/terraform/modules/networking/
  main.tf
  variables.tf
  outputs.tf
```
- Custom VPC with subnets
- Private Google Access
- Cloud NAT for outbound
- Firewall rules (internal only + health checks)

## Plan 7: ClickHouse on GKE (Kubernetes Manifests)
**Wave:** 3 (depends on Plan 2 GKE)
**Files:**
```
infra/k8s/
  clickhouse/
    statefulset.yaml
    service.yaml
    configmap.yaml
    pvc.yaml
```
- Altinity ClickHouse Operator OR raw StatefulSet
- Single node (dev), 3-node cluster (prod)
- Persistent volume: 50GB SSD

## Plan 8: Docker Compose Update (Local Dev Parity)
**Wave:** 1 (independent — local dev)
**Updates:** `docker-compose.yml`
- Verify PostgreSQL 15, Redis 7, ClickHouse match Terraform specs
- Add Pub/Sub emulator (gcloud pubsub emulator)
- Health checks on all services

---

## Execution Order
```
Wave 1: Plan 1 (TF structure) + Plan 6 (Networking) + Plan 8 (Docker Compose)
Wave 2: Plan 2 (GKE) + Plan 3 (CloudSQL) + Plan 4 (Redis) + Plan 5 (Pub/Sub) — parallel
Wave 3: Plan 7 (ClickHouse k8s)
```
