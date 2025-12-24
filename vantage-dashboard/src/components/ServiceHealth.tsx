import React from 'react';
import { useServiceHealth, ServiceHealth as ServiceHealthType } from '../hooks/useServiceHealth';

interface ServiceHealthProps {
  services?: ServiceHealthType[];
}

const ServiceHealth: React.FC<ServiceHealthProps> = ({ services: propServices }) => {
  const { services: fetchedServices, loading } = useServiceHealth();
  
  // Use provided services or fetched services
  const services = propServices || fetchedServices;

  if (loading && !propServices) {
    return (
      <div className="bg-surface-light dark:bg-surface-dark p-7 rounded-2xl border border-slate-100 dark:border-border-dark flex flex-col">
        <h2 className="text-lg font-bold text-slate-900 dark:text-white mb-6">Service Health</h2>
        <div className="text-slate-500">Loading service health...</div>
      </div>
    );
  }

  if (services.length === 0) {
    return (
      <div className="bg-surface-light dark:bg-surface-dark p-7 rounded-2xl border border-slate-100 dark:border-border-dark flex flex-col">
        <h2 className="text-lg font-bold text-slate-900 dark:text-white mb-6">Service Health</h2>
        <div className="text-center text-slate-500 py-8">
          <span className="material-icons-round text-4xl mb-2 block text-slate-300">cloud_off</span>
          No services detected
        </div>
      </div>
    );
  }

  return (
    <div className="bg-surface-light dark:bg-surface-dark p-7 rounded-2xl border border-slate-100 dark:border-border-dark flex flex-col">
      <h2 className="text-lg font-bold text-slate-900 dark:text-white mb-6">Service Health</h2>
      <div className="space-y-3">
        {services.map((service) => (
          <div 
            key={service.name} 
            className="flex items-center justify-between p-3.5 rounded-xl bg-slate-50 dark:bg-[#111] border border-transparent dark:hover:border-border-dark transition-all cursor-default"
          >
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-white dark:bg-[#181818] flex items-center justify-center border border-slate-100 dark:border-border-dark text-slate-400">
                <span className="material-icons-round text-lg">{service.icon}</span>
              </div>
              <div>
                <p className="text-sm font-bold text-slate-900 dark:text-slate-200">{service.name}</p>
                <p className="text-[11px] font-medium text-slate-500 tracking-wide">{service.status}</p>
              </div>
            </div>
            <div className="flex items-center">
              <span className={`w-2 h-2 rounded-full ${
                service.health === 'healthy' 
                  ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.4)]' 
                  : service.health === 'warning'
                  ? 'bg-yellow-500 shadow-[0_0_8px_rgba(234,179,8,0.4)] animate-pulse'
                  : 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.4)] animate-pulse'
              }`}></span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ServiceHealth;
