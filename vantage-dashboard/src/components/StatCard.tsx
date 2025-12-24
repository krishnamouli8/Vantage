import React from 'react';

interface StatCardProps {
  label: string;
  value: string | number;
  trend?: string;
  trendDirection?: 'up' | 'down' | 'neutral';
  icon: string;
  colorClass: string;
}

const StatCard: React.FC<StatCardProps> = ({ label, value, trend, trendDirection = 'neutral', icon, colorClass }) => {
  const getTrendStyle = () => {
    switch (trendDirection) {
      case 'up': return 'text-green-500 bg-green-500/10';
      case 'down': return 'text-green-500 bg-green-500/10'; 
      default: return 'text-slate-500 bg-slate-500/10';
    }
  };

  // Icon mapping from existing icon names to Material Icons
  const iconMap: { [key: string]: string } = {
    'activity': 'bolt',
    'clock': 'timer',
    'alert': 'error_outline',
    'check': 'check_circle',
  };

  const materialIcon = iconMap[icon] || icon;

  return (
    <div className="bg-surface-light dark:bg-surface-dark p-6 rounded-2xl border border-slate-100 dark:border-border-dark transition-all duration-300">
      <div className="flex justify-between items-start mb-6">
        <div className={`${colorClass} w-10 h-10 rounded-lg flex items-center justify-center`}>
          <span className="material-icons-round text-xl">{materialIcon}</span>
        </div>
        {trend && (
          <div className={`flex items-center text-[10px] font-bold px-2 py-1 rounded-md ${getTrendStyle()}`}>
            {trendDirection === 'up' && <span className="material-icons-round text-[12px] mr-1">arrow_upward</span>}
            {trendDirection === 'down' && <span className="material-icons-round text-[12px] mr-1">arrow_downward</span>}
            {trend}
          </div>
        )}
      </div>
      <div className="space-y-1">
        <h3 className="text-slate-500 dark:text-slate-500 text-xs font-semibold uppercase tracking-wider">{label}</h3>
        <p className="text-3xl font-bold text-slate-900 dark:text-white">{value}</p>
      </div>
    </div>
  );
};

export default StatCard;
