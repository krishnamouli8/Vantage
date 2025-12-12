import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { Metric, AggregatedMetrics } from '../types/metrics';

export function useMetrics(service?: string, range: number = 3600) {
  const [metrics, setMetrics] = useState<Metric[]>([]);
  const [aggregated, setAggregated] = useState<AggregatedMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [timeseriesData, aggregatedData] = await Promise.all([
          api.getTimeseries(service, range),
          api.getAggregated(service, range)
        ]);
        setMetrics(timeseriesData);
        setAggregated(aggregatedData);
      } catch (error) {
        console.error('Error fetching metrics:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30s

    return () => clearInterval(interval);
  }, [service, range]);

  return { metrics, aggregated, loading };
}
