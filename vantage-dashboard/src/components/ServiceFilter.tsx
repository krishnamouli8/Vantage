interface Props {
  selected: string;
  services: string[];
  onChange: (service: string) => void;
}

export function ServiceFilter({ selected, services, onChange }: Props) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
      <label style={{ 
        fontSize: '0.875rem', 
        fontWeight: 500,
        color: 'var(--color-text-secondary)',
      }}>
        Service
      </label>
      <select
        className="select"
        value={selected}
        onChange={(e) => onChange(e.target.value)}
      >
        <option value="">All Services</option>
        {services.map(service => (
          <option key={service} value={service}>
            {service}
          </option>
        ))}
      </select>
    </div>
  );
}
