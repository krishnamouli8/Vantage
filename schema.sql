-- ClickHouse Schema for Vantage Platform
-- Metrics table with MergeTree engine, monthly partitioning, and 90-day TTL

CREATE TABLE IF NOT EXISTS vantage.metrics (
    id UInt64,
    timestamp DateTime64(3),
    service_name String,
    metric_name String,
    metric_type String,
    value Float64,
    endpoint String,
    method String,
    status_code UInt16,
    duration_ms Float64,
    tags String,
    trace_id String,
    span_id String,
    aggregated UInt8 DEFAULT 0,
    resolution_minutes UInt32 DEFAULT 0,
    min_value Nullable(Float64),
    max_value Nullable(Float64),
    p50 Nullable(Float64),
    p95 Nullable(Float64),
    p99 Nullable(Float64),
    sample_count Nullable(UInt64),
    error_count Nullable(UInt64),
    created_at DateTime DEFAULT now()
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (service_name, metric_name, timestamp)
TTL timestamp + INTERVAL 90 DAY;

-- Sample test data
INSERT INTO vantage.metrics (id, timestamp, service_name, metric_name, metric_type, value, endpoint, method, status_code, duration_ms, tags, trace_id, span_id)
VALUES 
(1, '2025-12-13 16:00:00', 'test-api', 'http.request.duration', 'gauge', 123.45, '/api/users', 'GET', 200, 123.45, '{"env":"prod"}', 'trace-001', 'span-001'),
(2, '2025-12-13 16:00:01', 'test-api', 'http.request.count', 'counter', 1.0, '/api/users', 'POST', 201, 89.22, '{"env":"prod"}', 'trace-002', 'span-002'),
(3, '2025-12-13 16:00:02', 'test-api', 'http.request.duration', 'gauge', 234.56, '/api/posts', 'GET', 200, 234.56, '{"env":"prod"}', 'trace-003', 'span-003'),
(4, '2025-12-13 16:00:03', 'auth-service', 'http.request.duration', 'gauge', 45.67, '/auth/login', 'POST', 200, 45.67, '{"env":"prod"}', 'trace-004', 'span-004'),
(5, '2025-12-13 16:00:04', 'auth-service', 'http.request.duration', 'gauge', 32.11, '/auth/verify', 'GET', 200, 32.11, '{"env":"prod"}', 'trace-005', 'span-005');
