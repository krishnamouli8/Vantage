import { useEffect, useState } from 'react';
import { api } from '../api/client';

interface BackendHealthScore {
  service_name: string;
  overall_score: number;
  error_rate_score: number;
  latency_score: number;
  traffic_score: number;
  error_rate: number;
  p95_latency_ms: number;
  request_count: number;
}

export interface ServiceHealth {
  name: string;
  status: string;
  icon: string;
  health: 'healthy' | 'warning' | 'critical';
}

function getServiceIcon(serviceName: string): string {
  const name = serviceName.toLowerCase();
  if (name.includes('api') || name.includes('collector')) return 'api';
  if (name.includes('worker') || name.includes('ingestion')) return 'move_down';
  if (name.includes('database') || name.includes('sqlite') || name.includes('clickhouse')) return 'storage';
  if (name.includes('python') || name.includes('agent')) return 'code';
  if (name.includes('kafka') || name.includes('redpanda')) return 'stream';
  return 'dns'; // default for services
}

function mapBackendHealth(health: BackendHealthScore): ServiceHealth {
  const score = health.overall_score;
  
  let healthStatus: 'healthy' | 'warning' | 'critical';
  if (score >= 80) healthStatus = 'healthy';
  else if (score >= 50) healthStatus = 'warning';
  else healthStatus = 'critical';
  
  return {
    name: health.service_name,
    status: `Score: ${Math.round(score)}%`,
    icon: getServiceIcon(health.service_name),
    health: healthStatus,
  };
}

export function useServiceHealth() {
  const [services, setServices] = useState<ServiceHealth[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchHealthScores = async () => {
      try {
        setLoading(true);
        const data: BackendHealthScore[] = await api.getHealthScores();
        const mappedServices = data.map(mapBackendHealth);
        setServices(mappedServices);
        setError(null);
      } catch (err) {
        console.error('Error fetching health scores:', err);
        setError('Failed to fetch health scores');
        setServices([]);
      } finally {
        setLoading(false);
      }
    };

    fetchHealthScores();
    const interval = setInterval(fetchHealthScores, 60000); // Refresh every 60s

    return () => clearInterval(interval);
  }, []);

  return { services, loading, error };
}
