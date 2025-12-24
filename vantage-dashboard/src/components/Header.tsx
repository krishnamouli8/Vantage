import React from 'react';

interface HeaderProps {
  onToggleDarkMode: () => void;
  isDarkMode: boolean;
}

const Header: React.FC<HeaderProps> = ({ onToggleDarkMode, isDarkMode }) => {
  return (
    <header className="h-20 bg-background-light/50 dark:bg-background-dark/50 backdrop-blur-md flex items-center justify-between px-8 z-10 shrink-0">
      <div className="flex items-center gap-6">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Overview</h1>
        <div className="hidden sm:flex items-center gap-2 text-xs font-semibold text-green-500/80 bg-green-500/10 px-3 py-1.5 rounded-full border border-green-500/20">
          <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></span>
          Production
        </div>
      </div>
      
      <div className="flex items-center gap-5">
        <div className="relative hidden lg:block">
          <span className="material-icons-round absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 text-lg">search</span>
          <input 
            className="pl-10 pr-4 py-2 w-72 bg-slate-100 dark:bg-[#111] border border-slate-200 dark:border-border-dark rounded-lg text-sm focus:ring-1 focus:ring-primary focus:border-primary text-slate-900 dark:text-slate-100 placeholder-slate-500 transition-all outline-none" 
            placeholder="Search metrics, logs..." 
            type="text"
          />
        </div>
        
        <div className="flex items-center gap-1">
          <button className="p-2 text-slate-500 hover:text-primary dark:text-slate-400 dark:hover:text-white transition-colors relative">
            <span className="material-icons-round">notifications</span>
            <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full border-2 border-background-light dark:border-background-dark"></span>
          </button>
          
          <button 
            onClick={onToggleDarkMode}
            className="p-2 text-slate-500 hover:text-primary dark:text-slate-400 dark:hover:text-white transition-colors"
          >
            <span className="material-icons-round">{isDarkMode ? 'light_mode' : 'dark_mode'}</span>
          </button>
        </div>
      </div>
    </header>
  );
};

export default Header;
