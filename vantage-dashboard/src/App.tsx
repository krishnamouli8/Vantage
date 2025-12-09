import { useState, useEffect } from 'react';
import { MetricChart } from './components/MetricChart';
import { StatsCard } from './components/StatsCard';
import { ServiceFilter } from './components/ServiceFilter';
import { TimeRangeSelector } from './components/TimeRangeSelector';
import { useMetrics } from './hooks/useMetrics';
import { useWebSocket } from './hooks/useWebSocket';
import { api } from './api/client';

function App() {
  const [selectedService, setSelectedService] = useState('');
  const [timeRange, setTimeRange] = useState(3600);
  const [services, setServices] = useState<string[]>([]);
  
  const { metrics, aggregated, loading } = useMetrics(selectedService || undefined, timeRange);
  const { connected } = useWebSocket();

  useEffect(() => {
    api.getServices().then(setServices);
  }, []);

  return (
    <div style={{ 
      maxWidth: '1200px', 
      margin: '0 auto', 
      padding: '2rem',
      fontFamily: 'system-ui, -apple-system, sans-serif'
    }}>
      <header style={{ marginBottom: '2rem' }}>
        <h1 style={{ margin: 0 }}>Vantage Dashboard</h1>
        <p style={{ color: '#6c757d' }}>
          Real-time observability platform
          {connected && <span style={{ marginLeft: '1rem', color: '#28a745' }}>● Live</span>}
        </p>
      </header>

      <div style={{ marginBottom: '2rem' }}>
        <ServiceFilter 
          selected={selectedService}
          services={services}
          onChange={setSelectedService}
        />
        <TimeRangeSelector 
          selected={timeRange}
          onChange={setTimeRange}
        />
      </div>

      {loading ? (
        <div>Loading...</div>
      ) : (
        <>
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '1rem',
            marginBottom: '2rem'
          }}>
            <StatsCard 
              title="Total Requests" 
              value={aggregated?.total_requests || 0} 
            />
            <StatsCard 
              title="Avg Duration" 
              value={`${(aggregated?.avg_duration || 0).toFixed(2)}ms`}
            />
            <StatsCard 
              title="Errors" 
              value={aggregated?.error_count || 0}
              subtitle="Status 5xx"
            />
          </div>

          <MetricChart metrics={metrics} />
        </>
      )}
    </div>
  );
}

export default App;
