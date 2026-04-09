-- ClickHouse: trust_events
-- Primary analytics table for all AI interaction events
-- Designed for billions of rows with monthly partitioning

CREATE DATABASE IF NOT EXISTS zroky_analytics;

CREATE TABLE IF NOT EXISTS zroky_analytics.trust_events
(
    -- AI Interaction Metadata
    event_id                String,
    client_id               String,
    agent_id                String,
    timestamp               DateTime64(3),
    model_name              LowCardinality(String),
    prompt_tokens           UInt32    DEFAULT 0,
    completion_tokens       UInt32    DEFAULT 0,
    latency_ms              UInt32    DEFAULT 0,
    cost_usd                Float32   DEFAULT 0,

    -- V1 Engine Scores
    safety_score            Float32   DEFAULT 0,
    grounding_score         Float32   DEFAULT 0,
    consistency_score       Float32   DEFAULT 0,
    system_score            Float32   DEFAULT 0,
    coverage_score          Float32   DEFAULT 0,
    total_trust_score       Float32   DEFAULT 0,

    -- V2+ Engine Scores (Nullable for forward compat)
    uncertainty_score       Nullable(Float32),
    cognitive_score         Nullable(Float32),
    context_score           Nullable(Float32),
    behavior_score          Nullable(Float32),
    focus_score             Nullable(Float32),

    -- Context
    session_id              String    DEFAULT '',
    user_segment            LowCardinality(String) DEFAULT '',

    -- Safety Flags
    safety_alert_triggered  UInt8     DEFAULT 0,
    alert_type              LowCardinality(String) DEFAULT '',

    -- Metadata
    inserted_at             DateTime  DEFAULT now()
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (client_id, agent_id, timestamp)
TTL timestamp + INTERVAL 24 MONTH
SETTINGS index_granularity = 8192;

-- Materialized view for hourly aggregates
CREATE TABLE IF NOT EXISTS zroky_analytics.trust_scores_hourly
(
    client_id               String,
    agent_id                String,
    hour                    DateTime,
    event_count             UInt64,
    avg_trust_score         Float64,
    avg_safety_score        Float64,
    avg_grounding_score     Float64,
    avg_consistency_score   Float64,
    avg_system_score        Float64,
    min_trust_score         Float32,
    max_trust_score         Float32,
    alert_count             UInt64
)
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(hour)
ORDER BY (client_id, agent_id, hour);

CREATE MATERIALIZED VIEW IF NOT EXISTS zroky_analytics.trust_scores_hourly_mv
TO zroky_analytics.trust_scores_hourly
AS SELECT
    client_id,
    agent_id,
    toStartOfHour(timestamp) AS hour,
    count() AS event_count,
    avg(total_trust_score) AS avg_trust_score,
    avg(safety_score) AS avg_safety_score,
    avg(grounding_score) AS avg_grounding_score,
    avg(consistency_score) AS avg_consistency_score,
    avg(system_score) AS avg_system_score,
    min(total_trust_score) AS min_trust_score,
    max(total_trust_score) AS max_trust_score,
    countIf(safety_alert_triggered = 1) AS alert_count
FROM zroky_analytics.trust_events
GROUP BY client_id, agent_id, hour;
