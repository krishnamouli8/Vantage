import { useEffect, useState } from 'react';
import { api } from '../api/client';

interface BackendAlert {
  alert_id: string;
  service_name: string;
  metric_name: string;
  severity: string;
  status: string;
  message: string;
  current_value: number;
  expected_min: number;
  expected_max: number;
  threshold_breach_count: number;
  first_triggered: number;
  last_triggered: number;
  resolved_at: number | null;
}

export interface Alert {
  severity: 'Critical' | 'Warning' | 'Info';
  service: string;
  message: string;
  time: string;
  status: string;
  statusColor: string;
  dotColor: string;
}

function formatRelativeTime(timestamp: number): string {
  const now = Date.now();
  const diff = Math.floor((now - timestamp * 1000) / 1000); // Convert to seconds
  
  if (diff < 60) return 'Just now';
  if (diff < 3600) return `${Math.floor(diff / 60)} min ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)} hour${Math.floor(diff / 3600) > 1 ? 's' : ''} ago`;
  return `${Math.floor(diff / 86400)} day${Math.floor(diff / 86400) > 1 ? 's' : ''} ago`;
}

function mapBackendAlert(alert: BackendAlert): Alert {
  // Map severity
  const severity = alert.severity.toLowerCase() === 'critical' ? 'Critical' :
                   alert.severity.toLowerCase() === 'warning' ? 'Warning' : 'Info';
  
  // Map status
  let status = 'Logged';
  let statusColor = 'text-slate-400';
  let dotColor = 'bg-slate-400';
  
  if (alert.status === 'firing') {
    status = 'Investigating';
    statusColor = 'text-orange-500';
    dotColor = 'bg-orange-500';
  } else if (alert.status === 'resolved') {
    status = 'Resolved';
    statusColor = 'text-green-500';
    dotColor = 'bg-green-500';
  }
  
  return {
    severity,
    service: alert.service_name,
    message: alert.message,
    time: formatRelativeTime(alert.last_triggered),
    status,
    statusColor,
    dotColor,
  };
}

export function useAlerts(limit: number = 100) {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        setLoading(true);
        const data: BackendAlert[] = await api.getAlerts(limit);
        const mappedAlerts = data.map(mapBackendAlert);
        setAlerts(mappedAlerts);
        setError(null);
      } catch (err) {
        console.error('Error fetching alerts:', err);
        setError('Failed to fetch alerts');
        setAlerts([]);
      } finally {
        setLoading(false);
      }
    };

    fetchAlerts();
    const interval = setInterval(fetchAlerts, 30000); // Refresh every 30s

    return () => clearInterval(interval);
  }, [limit]);

  return { alerts, loading, error };
}
