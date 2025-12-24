import React from 'react';

const Sidebar: React.FC = () => {
  const navItems = [
    { label: 'Dashboard', icon: 'dashboard', active: true },
    { label: 'Services', icon: 'dns' },
    { label: 'Metrics', icon: 'timeline' },
    { label: 'Logs', icon: 'receipt_long' },
  ];

  const settingsItems = [
    { label: 'API Keys', icon: 'api' },
    { label: 'Configuration', icon: 'settings' },
  ];

  return (
    <aside className="w-64 bg-background-light dark:bg-background-dark border-r border-slate-200 dark:border-border-dark flex flex-col transition-colors duration-300 z-20 hidden md:flex">
      <div className="h-20 flex items-center px-6">
        <div className="flex items-center gap-3 text-slate-900 dark:text-white font-bold text-2xl tracking-tight">
          <div className="text-primary flex items-center">
            <span className="material-icons-round text-3xl">insights</span>
          </div>
          Vantage
        </div>
      </div>
      
      <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
        <p className="px-4 text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-[0.15em] mb-4">Platform</p>
        <div className="space-y-1">
          {navItems.map((item) => (
            <a
              key={item.label}
              href="#"
              className={`flex items-center gap-3 px-4 py-2.5 rounded-lg transition-all group ${
                item.active 
                  ? 'bg-orange-500/10 text-primary font-semibold' 
                  : 'text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
              }`}
            >
              <span className={`material-icons-round text-[20px] ${item.active ? 'text-primary' : ''}`}>{item.icon}</span>
              <span className="text-sm">{item.label}</span>
            </a>
          ))}
        </div>

        <p className="px-4 text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-[0.15em] mt-8 mb-4">Settings</p>
        <div className="space-y-1">
          {settingsItems.map((item) => (
            <a
              key={item.label}
              href="#"
              className="flex items-center gap-3 px-4 py-2.5 rounded-lg text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 transition-all group"
            >
              <span className="material-icons-round text-[20px]">{item.icon}</span>
              <span className="text-sm">{item.label}</span>
            </a>
          ))}
        </div>
      </nav>

      <div className="p-6 border-t border-slate-200 dark:border-border-dark">
        <div className="flex items-center gap-3 cursor-pointer">
          <img 
            alt="User Avatar" 
            className="w-10 h-10 rounded-full border border-slate-200 dark:border-slate-800" 
            src="https://picsum.photos/seed/devops/40/40" 
          />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-slate-900 dark:text-white truncate">DevOps Lead</p>
            <p className="text-xs text-slate-500 truncate">admin@vantage.io</p>
          </div>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
