import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Metric } from '../types/metrics';

interface Props {
  metrics: Metric[];
}

export function MetricChart({ metrics }: Props) {
  // Group metrics by timestamp and calculate requests per second
  const chartData = metrics
    .filter(m => m.duration_ms !== undefined)
    .map(m => ({
      timestamp: new Date(m.timestamp).toLocaleTimeString(),
      duration: m.duration_ms || 0,
      requests: 1
    }));

  return (
    <div style={{ width: '100%', height: 400 }}>
      <h3 style={{ marginBottom: '1rem' }}>Request Duration</h3>
      <ResponsiveContainer>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="timestamp" />
          <YAxis label={{ value: 'Duration (ms)', angle: -90, position: 'insideLeft' }} />
          <Tooltip />
          <Line type="monotone" dataKey="duration" stroke="#8884d8" strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
