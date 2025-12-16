"""Named constants for Vantage platform.

Replaces magic numbers throughout the codebase with well-documented,
centralized constant definitions.
"""

# ============================================================================
# Database Configuration
# ============================================================================

# Batch size for database operations
# Optimized for ClickHouse batch inserts - larger batches reduce overhead
# but increase memory usage. 100 is a good balance for most workloads.
BATCH_SIZE_DEFAULT = 100

# Database connection timeout in seconds
# Prevents hanging connections that could exhaust connection pool
DATABASE_CONNECTION_TIMEOUT_SECONDS = 10

# ClickHouse specific settings
CLICKHOUSE_BATCH_SIZE = 1000  # ClickHouse handles larger batches efficiently
CLICKHOUSE_MAX_QUERY_SIZE = 262144  # 256 KB max query size
CLICKHOUSE_COMPRESSION = True  # Enable compression for network efficiency

# ============================================================================
# Retry & Backoff Configuration
# ============================================================================

# Base seconds for exponential backoff: 2s, 4s, 8s, 16s
# Used when retrying failed database or Kafka operations
RETRY_BACKOFF_BASE_SECONDS = 2

# Maximum number of retry attempts before giving up
# Prevents infinite retry loops while allowing transient failures to recover
MAX_RETRY_ATTEMPTS = 3

# ============================================================================
# Kafka Configuration
# ============================================================================

# Consumer poll timeout in milliseconds
# How long consumer waits for new messages before returning empty batch
KAFKA_CONSUMER_TIMEOUT_MS = 1000

# Maximum number of messages to fetch in single poll
KAFKA_MAX_POLL_RECORDS = 500

# Kafka producer batch size in bytes
KAFKA_PRODUCER_BATCH_SIZE = 16384  # 16 KB batches

# Kafka producer linger time in milliseconds
# Wait up to this long to batch messages before sending
KAFKA_PRODUCER_LINGER_MS = 10

# ============================================================================
# Metrics & Downsampling Configuration
# ============================================================================

# Resolution for downsampled metrics in minutes
# 360 minutes = 6 hours, used for long-term storage with reduced granularity
DOWNSAMPLING_RESOLUTION_MINUTES = 360

# Percentiles to calculate during downsampling
DOWNSAMPLING_PERCENTILES = [50, 95, 99]

# ============================================================================
# Data Retention Configuration
# ============================================================================

# Default retention period in days
# Raw metrics older than this are deleted to manage storage
DEFAULT_DATA_RETENTION_DAYS = 90

# Retention for downsampled metrics (longer than raw)
DOWNSAMPLED_DATA_RETENTION_DAYS = 365  # 1 year

# How often to run retention cleanup (in seconds)
# 86400 = once per day
DATA_RETENTION_CHECK_INTERVAL_SECONDS = 86400

# ============================================================================
# Rate Limiting Configuration
# ============================================================================

# Rate limit window in seconds
# Tracks request count within this sliding window
RATE_LIMIT_WINDOW_SECONDS = 60

# Maximum requests allowed per window
# Default conservative limit, should be tuned based on capacity
RATE_LIMIT_MAX_REQUESTS = 1000

# ============================================================================
# Circuit Breaker Configuration
# ============================================================================

# Number of failures before circuit opens
CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5

# Seconds to wait in OPEN state before trying HALF_OPEN
CIRCUIT_BREAKER_TIMEOUT_SECONDS = 60

# Successful requests needed in HALF_OPEN to return to CLOSED
CIRCUIT_BREAKER_SUCCESS_THRESHOLD = 2

# ============================================================================
# Monitoring & Metrics
# ============================================================================

# Prometheus metrics HTTP server port for worker
WORKER_METRICS_PORT = 9090

# Prometheus metrics HTTP server port for API
API_METRICS_PORT = 9091

# Histogram buckets for latency tracking (in seconds)
# Covers range from 1ms to 10 seconds
LATENCY_HISTOGRAM_BUCKETS = [
    0.001,  # 1ms
    0.005,  # 5ms
    0.01,   # 10ms
    0.025,  # 25ms
    0.05,   # 50ms
    0.1,    # 100ms
    0.25,   # 250ms
    0.5,    # 500ms
    1.0,    # 1s
    2.5,    # 2.5s
    5.0,    # 5s
    10.0,   # 10s
]

# ============================================================================
# Health Check Configuration
# ============================================================================

# Interval between health checks in seconds
HEALTH_CHECK_INTERVAL_SECONDS = 30

# Timeout for health check requests
HEALTH_CHECK_TIMEOUT_SECONDS = 5
