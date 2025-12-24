import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Metric } from '../types/metrics';

interface ThroughputChartProps {
  metrics: Metric[];
}

const ThroughputChart: React.FC<ThroughputChartProps> = ({ metrics }) => {
  // Transform metrics data for chart
  const chartData = metrics.slice(-12).map((metric, idx) => ({
    time: new Date(metric.timestamp).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
    rps: metric.value || Math.floor((metric.duration_ms || 0) / 10),
  }));

  // Show empty state if no data
  if (chartData.length === 0) {
    return (
      <div className="bg-surface-light dark:bg-surface-dark p-7 rounded-2xl border border-slate-100 dark:border-border-dark flex flex-col h-[420px]">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
          <div>
            <h2 className="text-lg font-bold text-slate-900 dark:text-white">Throughput</h2>
            <p className="text-xs text-slate-500 dark:text-slate-500 mt-1">Requests per second over time</p>
          </div>
        </div>
        
        <div className="flex-1 flex items-center justify-center text-slate-500">
          <div className="text-center">
            <span className="material-icons-round text-4xl mb-2 block text-slate-300">insert_chart</span>
            No metric data available
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-surface-light dark:bg-surface-dark p-7 rounded-2xl border border-slate-100 dark:border-border-dark flex flex-col h-[420px]">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
        <div>
          <h2 className="text-lg font-bold text-slate-900 dark:text-white">Throughput</h2>
          <p className="text-xs text-slate-500 dark:text-slate-500 mt-1">Requests per second over time</p>
        </div>
        <div className="flex items-center bg-slate-50 dark:bg-[#111] border border-slate-200 dark:border-border-dark rounded-lg px-3 py-1.5 cursor-pointer">
          <span className="text-xs font-semibold text-slate-600 dark:text-slate-300">Last 1 Hour</span>
          <span className="material-icons-round text-sm ml-2 text-slate-400">expand_more</span>
        </div>
      </div>
      
      <div className="flex-1 w-full relative">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 20, right: 0, left: -25, bottom: 0 }}>
            <defs>
              <linearGradient id="colorRps" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#f97316" stopOpacity={0.4}/>
                <stop offset="95%" stopColor="#f97316" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#1f1f1f" />
            <XAxis 
              dataKey="time" 
              axisLine={false} 
              tickLine={false} 
              tick={{ fontSize: 10, fill: '#4b5563', fontWeight: 600 }} 
              dy={15}
            />
            <YAxis 
              axisLine={false} 
              tickLine={false} 
              tick={{ fontSize: 10, fill: '#4b5563', fontWeight: 600 }}
            />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: '#111', 
                border: '1px solid #1f1f1f', 
                borderRadius: '8px', 
                color: '#fff',
                fontSize: '11px'
              }}
              itemStyle={{ color: '#f97316' }}
              cursor={{ stroke: '#f97316', strokeWidth: 1 }}
            />
            <Area 
              type="monotone" 
              dataKey="rps" 
              stroke="#f97316" 
              strokeWidth={3}
              fillOpacity={1} 
              fill="url(#colorRps)" 
              animationDuration={1500}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default ThroughputChart;
