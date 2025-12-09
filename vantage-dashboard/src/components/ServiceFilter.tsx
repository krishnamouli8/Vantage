interface Props {
  selected: string;
  services: string[];
  onChange: (service: string) => void;
}

export function ServiceFilter({ selected, services, onChange }: Props) {
  return (
    <div style={{ marginBottom: '1rem' }}>
      <label htmlFor="service-select" style={{ marginRight: '0.5rem', fontWeight: 'bold' }}>
        Service:
      </label>
      <select
        id="service-select"
        value={selected}
        onChange={(e) => onChange(e.target.value)}
        style={{
          padding: '0.5rem',
          borderRadius: '4px',
          border: '1px solid #ddd',
          fontSize: '1rem'
        }}
      >
        <option value="">All Services</option>
        {services.map(service => (
          <option key={service} value={service}>{service}</option>
        ))}
      </select>
    </div>
  );
}
