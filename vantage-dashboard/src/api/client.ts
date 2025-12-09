const API_BASE = 'http://localhost:8001';

export const api = {
  async getTimeseries(service?: string, range: number = 3600) {
    const params = new URLSearchParams();
    if (service) params.set('service', service);
    params.set('range', range.toString());
    
    const response = await fetch(`${API_BASE}/api/metrics/timeseries?${params}`);
    return response.json();
  },

  async getAggregated(service?: string, range: number = 3600) {
    const params = new URLSearchParams();
    if (service) params.set('service', service);
    params.set('range', range.toString());
    
    const response = await fetch(`${API_BASE}/api/metrics/aggregated?${params}`);
    return response.json();
  },

  async getServices() {
    const response = await fetch(`${API_BASE}/api/services`);
    return response.json();
  }
};
