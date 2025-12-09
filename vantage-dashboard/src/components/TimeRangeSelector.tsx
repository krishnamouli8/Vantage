interface Props {
  selected: number;
  onChange: (range: number) => void;
}

const TIME_RANGES = [
  { label: '1 Hour', value: 3600 },
  { label: '6 Hours', value: 21600 },
  { label: '24 Hours', value: 86400 }
];

export function TimeRangeSelector({ selected, onChange }: Props) {
  return (
    <div style={{ marginBottom: '1rem' }}>
      <label style={{ marginRight: '0.5rem', fontWeight: 'bold' }}>Time Range:</label>
      {TIME_RANGES.map(range => (
        <button
          key={range.value}
          onClick={() => onChange(range.value)}
          style={{
            padding: '0.5rem 1rem',
            marginRight: '0.5rem',
            borderRadius: '4px',
            border: selected === range.value ? '2px solid #007bff' : '1px solid #ddd',
            backgroundColor: selected === range.value ? '#e7f3ff' : '#fff',
            cursor: 'pointer',
            fontWeight: selected === range.value ? 'bold' : 'normal'
          }}
        >
          {range.label}
        </button>
      ))}
    </div>
  );
}
