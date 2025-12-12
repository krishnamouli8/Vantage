import { XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { Metric } from '../types/metrics';

interface Props {
  metrics: Metric[];
}

export function MetricChart({ metrics }: Props) {
  // Group metrics by timestamp and calculate average duration
  const chartData = metrics
    .filter(m => m.duration_ms !== undefined)
    .reduce((acc: any[], metric) => {
      const time = new Date(metric.timestamp);
      const timeKey = time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      
      const existing = acc.find(d => d.time === timeKey);
      if (existing) {
        existing.requests += 1;
        existing.totalDuration += metric.duration_ms || 0;
        existing.avgDuration = existing.totalDuration / existing.requests;
      } else {
        acc.push({
          time: timeKey,
          requests: 1,
          totalDuration: metric.duration_ms || 0,
          avgDuration: metric.duration_ms || 0,
        });
      }
      
      return acc;
    }, [])
    .sort((a, b) => {
      // Simple time-based sorting
      return a.time.localeCompare(b.time);
    });

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div style={{
          background: 'var(--color-bg-card)',
          backdropFilter: 'blur(20px)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-md)',
          padding: 'var(--space-3)',
          boxShadow: 'var(--shadow-lg)',
        }}>
          <p style={{ margin: 0, marginBottom: 'var(--space-2)', fontWeight: 600 }}>
            {payload[0].payload.time}
          </p>
          <p style={{ margin: 0, color: 'var(--color-primary)', fontSize: '0.875rem' }}>
            Avg Duration: {payload[0].value.toFixed(2)}ms
          </p>
          <p style={{ margin: 0, color: 'var(--color-text-secondary)', fontSize: '0.875rem' }}>
            Requests: {payload[0].payload.requests}
          </p>
        </div>
      );
    }
    return null;
  };

  if (chartData.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: 'var(--space-8)', color: 'var(--color-text-secondary)' }}>
        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" style={{ margin: '0 auto var(--space-4)' }}>
          <line x1="12" y1="20" x2="12" y2="10"/>
          <line x1="18" y1="20" x2="18" y2="4"/>
          <line x1="6" y1="20" x2="6" y2="16"/>
        </svg>
        <h3 style={{ marginBottom: 'var(--space-2)' }}>No Data Available</h3>
        <p style={{ fontSize: '0.875rem' }}>
          Send some metrics to see them visualized here
        </p>
      </div>
    );
  }

  return (
    <div style={{ width: '100%' }}>
      <div style={{ marginBottom: 'var(--space-6)' }}>
        <h3 style={{ margin: 0, marginBottom: 'var(--space-1)' }}>Request Performance</h3>
        <p style={{ margin: 0, color: 'var(--color-text-secondary)', fontSize: '0.875rem' }}>
          Average response time over time
        </p>
      </div>
      
      <ResponsiveContainer width="100%" height={350}>
        <AreaChart data={chartData}>
          <defs>
            <linearGradient id="colorDuration" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" opacity={0.3} />
          <XAxis 
            dataKey="time" 
            stroke="var(--color-text-tertiary)"
            style={{ fontSize: '0.75rem' }}
          />
          <YAxis 
            stroke="var(--color-text-tertiary)"
            style={{ fontSize: '0.75rem' }}
            label={{ 
              value: 'Duration (ms)', 
              angle: -90, 
              position: 'insideLeft',
              style: { fill: 'var(--color-text-secondary)', fontSize: '0.75rem' }
            }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Area 
            type="monotone" 
            dataKey="avgDuration" 
            stroke="#6366f1" 
            strokeWidth={2}
            fill="url(#colorDuration)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
