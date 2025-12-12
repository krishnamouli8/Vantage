interface Props {
  selected: number;
  onChange: (range: number) => void;
}

const TIME_RANGES = [
  { label: '1h', value: 3600 },
  { label: '6h', value: 21600 },
  { label: '24h', value: 86400 },
  { label: '7d', value: 604800 },
];

export function TimeRangeSelector({ selected, onChange }: Props) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
      <label style={{ 
        fontSize: '0.875rem', 
        fontWeight: 500,
        color: 'var(--color-text-secondary)',
      }}>
        Time Range
      </label>
      <div className="btn-group">
        {TIME_RANGES.map(({ label, value }) => (
          <button
            key={value}
            className={`btn ${selected === value ? 'active' : ''}`}
            onClick={() => onChange(value)}
          >
            {label}
          </button>
        ))}
      </div>
    </div>
  );
}
