import { AggregatedMetrics } from '../types/metrics';

interface Props {
  title: string;
  value: string | number;
  subtitle?: string;
}

export function StatsCard({ title, value, subtitle }: Props) {
  return (
    <div style={{
      padding: '1.5rem',
      backgroundColor: '#f8f9fa',
      borderRadius: '8px',
      boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
    }}>
      <h4 style={{ margin: 0, fontSize: '0.875rem', color: '#6c757d' }}>{title}</h4>
      <div style={{ fontSize: '2rem', fontWeight: 'bold', margin: '0.5rem 0' }}>
        {value}
      </div>
      {subtitle && <p style={{ margin: 0, fontSize: '0.875rem', color: '#6c757d' }}>{subtitle}</p>}
    </div>
  );
}
