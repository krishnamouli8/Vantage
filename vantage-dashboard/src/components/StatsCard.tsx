interface Props {
  title: string;
  value: string | number;
  subtitle?: string;
  change?: string;
  trend?: 'up' | 'down';
  icon?: 'activity' | 'clock' | 'alert' | 'check';
}

const ICONS = {
  activity: (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
    </svg>
  ),
  clock: (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="10"/>
      <polyline points="12 6 12 12 16 14"/>
    </svg>
  ),
  alert: (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
      <line x1="12" y1="9" x2="12" y2="13"/>
      <line x1="12" y1="17" x2="12.01" y2="17"/>
    </svg>
  ),
  check: (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
      <polyline points="22 4 12 14.01 9 11.01"/>
    </svg>
  ),
};

export function StatsCard({ title, value, subtitle, change, trend, icon = 'activity' }: Props) {
  const trendColor = trend === 'up' 
    ? (icon === 'alert' ? 'var(--color-error)' : 'var(--color-success)')
    : 'var(--color-success)';

  const gradientMap = {
    activity: 'var(--gradient-primary)',
    clock: 'var(--gradient-info)',
    alert: 'var(--gradient-error)',
    check: 'var(--gradient-success)',
  };

  return (
    <div className="card stats-card animate-slide-in">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 'var(--space-4)' }}>
        <div style={{ flex: 1 }}>
          <h3 style={{ 
            margin: 0, 
            fontSize: '0.875rem', 
            fontWeight: 500,
            color: 'var(--color-text-secondary)',
            marginBottom: 'var(--space-2)',
          }}>
            {title}
          </h3>
          <div style={{ 
            fontSize: '2rem', 
            fontWeight: 700,
            marginBottom: subtitle ? 'var(--space-1)' : 0,
          }}>
            {value}
          </div>
          {subtitle && (
            <p style={{ 
              margin: 0, 
              fontSize: '0.75rem', 
              color: 'var(--color-text-tertiary)' 
            }}>
              {subtitle}
            </p>
          )}
        </div>
        
        <div style={{
          width: '48px',
          height: '48px',
          borderRadius: 'var(--radius-lg)',
          background: gradientMap[icon],
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white',
          flexShrink: 0,
        }}>
          {ICONS[icon]}
        </div>
      </div>

      {change && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          <span style={{ 
            color: trendColor,
            fontSize: '0.875rem',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--space-1)',
          }}>
            {trend === 'up' ? '↑' : '↓'} {change}
          </span>
          <span style={{ fontSize: '0.75rem', color: 'var(--color-text-tertiary)' }}>
            vs last hour
          </span>
        </div>
      )}
    </div>
  );
}
