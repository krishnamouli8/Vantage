import { useState, useEffect } from 'react';
import { MetricChart } from './components/MetricChart';
import { StatsCard } from './components/StatsCard';
import { ServiceFilter } from './components/ServiceFilter';
import { TimeRangeSelector } from './components/TimeRangeSelector';
import { ThemeToggle } from './components/ThemeToggle';
import { useMetrics } from './hooks/useMetrics';
import { useWebSocket } from './hooks/useWebSocket';
import { api } from './api/client';

function App() {
  const [selectedService, setSelectedService] = useState('');
  const [timeRange, setTimeRange] = useState(3600);
  const [services, setServices] = useState<string[]>([]);
  const [previousAggregated, setPreviousAggregated] = useState<any>(null);
  
  const { metrics, aggregated, loading } = useMetrics(selectedService || undefined, timeRange);
  const { connected } = useWebSocket();

  useEffect(() => {
    api.getServices().then(setServices);
  }, []);
  
  // Store previous metrics for comparison
  useEffect(() => {
    if (aggregated && !loading) {
      setPreviousAggregated(aggregated);
    }
  }, [timeRange]); // Only update when timeRange changes
  
  // Calculate percentage changes
  const calculateChange = (current: number, previous: number): string => {
    if (!previous || previous === 0) return '+0.0%';
    const change = ((current - previous) / previous) * 100;
    return `${change >= 0 ? '+' : ''}${change.toFixed(1)}%`;
  };
  
  const calculateTrend = (current: number, previous: number): 'up' | 'down' => {
    return current >= previous ? 'up' : 'down';
  };
  
  // Calculate success rate
  const calculateSuccessRate = (): string => {
    if (!aggregated || !aggregated.total_requests || aggregated.total_requests === 0) {
      return '0.0%';
    }
    const successCount = aggregated.total_requests - (aggregated.error_count || 0);
    const rate = (successCount / aggregated.total_requests) * 100;
    return rate.toFixed(1) + '%';
  };

  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className="sidebar">
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', marginBottom: 'var(--space-2)' }}>
            <div style={{
              width: '40px',
              height: '40px',
              background: 'var(--gradient-primary)',
              borderRadius: 'var(--radius-lg)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 'bold',
              color: 'white',
              fontSize: '1.25rem',
            }}>
              V
            </div>
            <h2 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 700 }}>Vantage</h2>
          </div>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.875rem', margin: 0 }}>
            Observability Platform
          </p>
        </div>

        <nav style={{ flex: 1 }}>
          <div style={{ marginBottom: 'var(--space-6)' }}>
            <h3 style={{ 
              fontSize: '0.75rem', 
              fontWeight: 600, 
              textTransform: 'uppercase', 
              letterSpacing: '0.05em',
              color: 'var(--color-text-tertiary)',
              marginBottom: 'var(--space-3)',
            }}>
              Analytics
            </h3>
            <ul style={{ listStyle: 'none' }}>
              <li>
                <a href="#" className="btn btn-ghost" style={{ 
                  width: '100%', 
                  justifyContent: 'flex-start',
                  background: 'var(--gradient-primary)',
                  color: 'white',
                }}>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                    <line x1="3" y1="9" x2="21" y2="9"/>
                    <line x1="9" y1="21" x2="9" y2="9"/>
                  </svg>
                  Dashboard
                </a>
              </li>
              <li>
                <a href="#" className="btn btn-ghost" style={{ width: '100%', justifyContent: 'flex-start' }}>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="12" y1="20" x2="12" y2="10"/>
                    <line x1="18" y1="20" x2="18" y2="4"/>
                    <line x1="6" y1="20" x2="6" y2="16"/>
                  </svg>
                  Metrics
                </a>
              </li>
              <li>
                <a href="#" className="btn btn-ghost" style={{ width: '100%', justifyContent: 'flex-start' }}>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14 2 14 8 20 8"/>
                    <line x1="16" y1="13" x2="8" y2="13"/>
                    <line x1="16" y1="17" x2="8" y2="17"/>
                    <polyline points="10 9 9 9 8 9"/>
                  </svg>
                  Traces
                </a>
              </li>
            </ul>
          </div>

          <div>
            <h3 style={{ 
              fontSize: '0.75rem', 
              fontWeight: 600, 
              textTransform: 'uppercase', 
              letterSpacing: '0.05em',
              color: 'var(--color-text-tertiary)',
              marginBottom: 'var(--space-3)',
            }}>
              System
            </h3>
            <ul style={{ listStyle: 'none' }}>
              <li>
                <a href="#" className="btn btn-ghost" style={{ width: '100%', justifyContent: 'flex-start' }}>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="3"/>
                    <path d="M12 1v6m0 6v6M5.6 5.6l4.2 4.2m4.2 4.2l4.2 4.2M1 12h6m6 0h6M5.6 18.4l4.2-4.2m4.2-4.2l4.2-4.2"/>
                  </svg>
                  Settings
                </a>
              </li>
            </ul>
          </div>
        </nav>

        <div style={{ 
          padding: 'var(--space-4)', 
          background: 'var(--color-bg-tertiary)',
          borderRadius: 'var(--radius-lg)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: 'var(--space-2)' }}>
            <div className={connected ? 'pulse-dot' : ''} style={{ 
              background: connected ? 'var(--color-success)' : 'var(--color-text-tertiary)',
            }}></div>
            <span style={{ fontSize: '0.875rem', fontWeight: 500 }}>
              {connected ? 'Live' : 'Disconnected'}
            </span>
          </div>
          <p style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', margin: 0 }}>
            {connected ? 'Real-time data streaming' : 'Waiting for connection...'}
          </p>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        <header className="header">
          <div>
            <h1 style={{ margin: 0, fontSize: '1.75rem', marginBottom: 'var(--space-1)' }}>Dashboard</h1>
            <p style={{ margin: 0, color: 'var(--color-text-secondary)', fontSize: '0.875rem' }}>
              Real-time performance metrics and insights
            </p>
          </div>
          <ThemeToggle />
        </header>

        <div className="content-wrapper">
          {/* Filters */}
          <div className="card" style={{ marginBottom: 'var(--space-6)' }}>
            <div style={{ display: 'flex', gap: 'var(--space-4)', alignItems: 'center', flexWrap: 'wrap' }}>
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
          </div>

          {/* Stats Cards */}
          {loading ? (
            <div className="grid grid-auto-fit" style={{ marginBottom: 'var(--space-6)' }}>
              {[1, 2, 3, 4].map(i => (
                <div key={i} className="skeleton" style={{ height: '120px' }}></div>
              ))}
            </div>
          ) : (
            <div className="grid grid-auto-fit" style={{ marginBottom: 'var(--space-6)' }}>
              <StatsCard 
                title="Total Requests" 
                value={aggregated?.total_requests || 0}
                change={previousAggregated ? calculateChange(aggregated?.total_requests || 0, previousAggregated.total_requests || 0) : undefined}
                trend={previousAggregated ? calculateTrend(aggregated?.total_requests || 0, previousAggregated.total_requests || 0) : undefined}
                icon="activity"
              />
              <StatsCard 
                title="Avg Duration" 
                value={`${(aggregated?.avg_duration || 0).toFixed(2)}ms`}
                change={previousAggregated ? calculateChange(aggregated?.avg_duration || 0, previousAggregated.avg_duration || 0) : undefined}
                trend={previousAggregated ? calculateTrend(previousAggregated.avg_duration || 0, aggregated?.avg_duration || 0) : undefined}
                icon="clock"
              />
              <StatsCard 
                title="Error Count" 
                value={aggregated?.error_count || 0}
                subtitle="5xx errors"
                change={previousAggregated ? calculateChange(aggregated?.error_count || 0, previousAggregated.error_count || 0) : undefined}
                trend={previousAggregated ? calculateTrend(previousAggregated.error_count || 0, aggregated?.error_count || 0) : undefined}
                icon="alert"
              />
              <StatsCard 
                title="Success Rate" 
                value={calculateSuccessRate()}
                change={previousAggregated ? calculateChange(
                  aggregated?.total_requests ? ((aggregated.total_requests - (aggregated.error_count || 0)) / aggregated.total_requests) * 100 : 0,
                  previousAggregated.total_requests ? ((previousAggregated.total_requests - (previousAggregated.error_count || 0)) / previousAggregated.total_requests) * 100 : 0
                ) : undefined}
                trend={previousAggregated && aggregated?.total_requests && previousAggregated.total_requests ? calculateTrend(
                  ((aggregated.total_requests - (aggregated.error_count || 0)) / aggregated.total_requests) * 100,
                  ((previousAggregated.total_requests - (previousAggregated.error_count || 0)) / previousAggregated.total_requests) * 100
                ) : undefined}
                icon="check"
              />
            </div>
          )}

          {/* Charts */}
          {loading ? (
            <div className="skeleton" style={{ height: '400px', marginBottom: 'var(--space-6)' }}></div>
          ) : (
            <div className="card" style={{ marginBottom: 'var(--space-6)' }}>
              <MetricChart metrics={metrics} />
            </div>
          )}

          {/* Additional Info */}
          <div className="grid grid-cols-2" style={{ gap: 'var(--space-6)' }}>
            <div className="card">
              <h3 style={{ marginBottom: 'var(--space-4)' }}>Services</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
                {services.length === 0 ? (
                  <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.875rem' }}>
                    No services detected yet
                  </p>
                ) : (
                  services.slice(0, 5).map(service => (
                    <div key={service} style={{ 
                      display: 'flex', 
                      justifyContent: 'space-between', 
                      alignItems: 'center',
                      padding: 'var(--space-3)',
                      background: 'var(--color-bg-secondary)',
                      borderRadius: 'var(--radius-md)',
                    }}>
                      <span style={{ fontWeight: 500 }}>{service}</span>
                      <span className="badge badge-success">Active</span>
                    </div>
                  ))
                )}
              </div>
            </div>

            <div className="card">
              <h3 style={{ marginBottom: 'var(--space-4)' }}>Recent Activity</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                {metrics.slice(0, 5).map((metric, idx) => (
                  <div key={idx} style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between', 
                    alignItems: 'center',
                    fontSize: '0.875rem',
                  }}>
                    <div>
                      <div style={{ fontWeight: 500, marginBottom: 'var(--space-1)' }}>
                        {metric.method} {metric.endpoint}
                      </div>
                      <div style={{ color: 'var(--color-text-secondary)', fontSize: '0.75rem' }}>
                        {new Date(metric.timestamp).toLocaleTimeString()}
                      </div>
                    </div>
                    <span className={`badge ${
                      metric.status_code && metric.status_code >= 500 ? 'badge-error' :
                      metric.status_code && metric.status_code >= 400 ? 'badge-warning' :
                      'badge-success'
                    }`}>
                      {metric.status_code}
                    </span>
                  </div>
                ))}
                {metrics.length === 0 && (
                  <p style={{ color: 'var(--color-text-secondary)', fontSize: '0.875rem' }}>
                    No recent activity
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
