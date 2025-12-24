const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000';

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
  },

  async getAlerts(limit: number = 100) {
    const response = await fetch(`${API_BASE}/alerts/?limit=${limit}`);
    return response.json();
  },

  async getActiveAlerts() {
    const response = await fetch(`${API_BASE}/alerts/active`);
    return response.json();
  },

  async getHealthScores() {
    const response = await fetch(`${API_BASE}/health/scores`);
    return response.json();
  }
};
