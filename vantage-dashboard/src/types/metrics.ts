export interface Metric {
  timestamp: number;
  service_name: string;
  metric_name: string;
  value: number;
  duration_ms?: number;
  status_code?: number;
  endpoint?: string;
  method?: string;
}

export interface AggregatedMetrics {
  total_requests: number;
  avg_duration: number;
  min_duration: number;
  max_duration: number;
  error_count: number;
}
