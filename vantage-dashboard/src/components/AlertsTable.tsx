import React from 'react';
import { useAlerts, Alert } from '../hooks/useAlerts';

interface AlertsTableProps {
  alerts?: Alert[];
}

const AlertsTable: React.FC<AlertsTableProps> = ({ alerts: propAlerts }) => {
  const { alerts: fetchedAlerts, loading } = useAlerts(100);
  
  // Use provided alerts or fetched alerts
  const alerts = propAlerts || fetchedAlerts;

  if (loading && !propAlerts) {
    return (
      <div className="bg-surface-light dark:bg-surface-dark rounded-2xl border border-slate-100 dark:border-border-dark overflow-hidden mb-8 p-7">
        <div className="text-slate-500">Loading alerts...</div>
      </div>
    );
  }

  if (alerts.length === 0) {
    return (
      <div className="bg-surface-light dark:bg-surface-dark rounded-2xl border border-slate-100 dark:border-border-dark overflow-hidden mb-8">
        <div className="p-7 border-b border-slate-100 dark:border-border-dark flex justify-between items-center">
          <div>
            <h2 className="text-lg font-bold text-slate-900 dark:text-white">Recent Alerts</h2>
            <p className="text-xs text-slate-500 mt-1">Anomalies detected in the last 24 hours</p>
          </div>
        </div>
        <div className="p-7 text-center text-slate-500">
          <span className="material-icons-round text-4xl mb-2 block text-slate-300">check_circle</span>
          No alerts detected. All systems operational.
        </div>
      </div>
    );
  }

  return (
    <div className="bg-surface-light dark:bg-surface-dark rounded-2xl border border-slate-100 dark:border-border-dark overflow-hidden mb-8">
      <div className="p-7 border-b border-slate-100 dark:border-border-dark flex justify-between items-center">
        <div>
          <h2 className="text-lg font-bold text-slate-900 dark:text-white">Recent Alerts</h2>
          <p className="text-xs text-slate-500 mt-1">Anomalies detected in the last 24 hours</p>
        </div>
        <button className="text-xs font-bold text-primary hover:underline transition-all">View All</button>
      </div>
      
      <div className="overflow-x-auto">
        <table className="w-full text-left text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
          <thead className="bg-slate-50/50 dark:bg-black/20">
            <tr>
              <th className="px-7 py-4">Severity</th>
              <th className="px-7 py-4">Service</th>
              <th className="px-7 py-4">Message</th>
              <th className="px-7 py-4">Time</th>
              <th className="px-7 py-4 text-right pr-10">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-border-dark capitalize font-normal text-sm normal-case">
            {alerts.slice(0, 10).map((alert, idx) => (
              <tr key={idx} className="hover:bg-slate-50 dark:hover:bg-white/[0.02] transition-colors">
                <td className="px-7 py-4">
                  <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold ${
                    alert.severity === 'Critical' ? 'bg-red-500/10 text-red-500' :
                    alert.severity === 'Warning' ? 'bg-yellow-500/10 text-yellow-500' :
                    'bg-blue-500/10 text-blue-500'
                  }`}>
                    {alert.severity}
                  </span>
                </td>
                <td className="px-7 py-4 font-bold text-slate-900 dark:text-slate-200">{alert.service}</td>
                <td className="px-7 py-4 text-slate-600 dark:text-slate-400 truncate max-w-xs">{alert.message}</td>
                <td className="px-7 py-4 text-slate-500 whitespace-nowrap">{alert.time}</td>
                <td className="px-7 py-4 text-right pr-10">
                  <div className={`inline-flex items-center gap-2 font-bold text-[11px] ${alert.statusColor}`}>
                    <span className={`w-1.5 h-1.5 rounded-full ${alert.dotColor}`}></span>
                    {alert.status}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default AlertsTable;
