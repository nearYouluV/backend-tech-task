-- ClickHouse initialization script for cold storage analytics
-- This script sets up the cold storage layer for analytics

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS events_analytics;

-- Switch to the analytics database
USE events_analytics;

-- Events cold storage table optimized for analytics
-- Uses MergeTree engine with partitioning by date for optimal performance
CREATE TABLE IF NOT EXISTS events_cold (
    -- Core event fields
    event_id UUID,
    user_id String,
    event_type LowCardinality(String),  -- Optimize for repeated values
    occurred_at DateTime64(3),          -- Millisecond precision
    
    -- Properties as JSON - ClickHouse can efficiently query JSON
    properties String,
    
    -- Metadata
    ingested_at DateTime64(3) DEFAULT now64(),
    partition_date Date MATERIALIZED toDate(occurred_at),
    
    -- Analytics-optimized fields
    hour UInt8 MATERIALIZED toHour(occurred_at),
    day_of_week UInt8 MATERIALIZED toDayOfWeek(occurred_at),
    month UInt8 MATERIALIZED toMonth(occurred_at),
    year UInt16 MATERIALIZED toYear(occurred_at)
    
) ENGINE = MergeTree()
PARTITION BY partition_date
ORDER BY (event_type, user_id, occurred_at)
TTL partition_date + INTERVAL 2 YEAR  -- Auto-cleanup after 2 years
SETTINGS index_granularity = 8192;

-- Daily Active Users materialized view for super-fast DAU queries
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_daily_active_users
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(event_date)
ORDER BY (event_date, user_id)
AS SELECT
    toDate(occurred_at) as event_date,
    user_id,
    1 as is_active  -- Will be summed, but we only care about distinct users
FROM events_cold;

-- Event type statistics materialized view
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_event_type_stats
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(event_date)
ORDER BY (event_date, event_type)
AS SELECT
    toDate(occurred_at) as event_date,
    event_type,
    count() as event_count
FROM events_cold
GROUP BY event_date, event_type;

-- Hourly event volume for performance monitoring
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_hourly_volume
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(event_hour)
ORDER BY (event_hour, event_type)
AS SELECT
    toStartOfHour(occurred_at) as event_hour,
    event_type,
    count() as event_count,
    uniq(user_id) as unique_users
FROM events_cold
GROUP BY event_hour, event_type;

-- Create indexes for common query patterns
-- ClickHouse automatically creates indexes based on ORDER BY

-- Grant permissions (if needed)
-- GRANT SELECT, INSERT ON events_analytics.* TO default;
