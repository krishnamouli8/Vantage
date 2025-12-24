import { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import StatCard from './components/StatCard';
import ThroughputChart from './components/ThroughputChart';
import ServiceHealth from './components/ServiceHealth';
import AlertsTable from './components/AlertsTable';
import AIInsights from './components/AIInsights';
import { useMetrics } from './hooks/useMetrics';
import { useWebSocket } from './hooks/useWebSocket';
import { useAlerts } from './hooks/useAlerts';
import { useServiceHealth } from './hooks/useServiceHealth';
import { api } from './api/client';

function App() {
  const [selectedService, setSelectedService] = useState('');
  const [timeRange, setTimeRange] = useState(3600);
  const [services, setServices] = useState<string[]>([]);
  const [previousAggregated, setPreviousAggregated] = useState<any>(null);
  const [isDarkMode, setIsDarkMode] = useState(true);
  
  const { metrics, aggregated, loading } = useMetrics(selectedService || undefined, timeRange);
  const { connected } = useWebSocket();
  const { alerts } = useAlerts(10); // Get latest 10 alerts
  const { services: healthServices } = useServiceHealth();

  useEffect(() => {
    api.getServices().then(setServices);
  }, []);

  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDarkMode]);
  
  // Store previous metrics for comparison
  useEffect(() => {
    if (aggregated && !loading) {
      setPreviousAggregated(aggregated);
    }
  }, [timeRange]);
  
  // Calculate percentage changes
  const calculateChange = (current: number, previous: number): string => {
    if (!previous || previous === 0) return '+0.0%';
    const change = ((current - previous) / previous) * 100;
    return `${change >= 0 ? '+' : ''}${change.toFixed(1)}%`;
  };
  
  const calculateTrend = (current: number, previous: number): 'up' | 'down' => {
    return current >= previous ? 'up' : 'down';
  };
  
  // Calculate success rate
  const calculateSuccessRate = (): string => {
    if (!aggregated || !aggregated.total_requests || aggregated.total_requests === 0) {
      return '0.0%';
    }
    const successCount = aggregated.total_requests - (aggregated.error_count || 0);
    const rate = (successCount / aggregated.total_requests) * 100;
    return rate.toFixed(1) + '%';
  };

  const toggleDarkMode = () => setIsDarkMode(!isDarkMode);

  // Format numbers for display
  const formatNumber = (num: number): string => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  return (
    <div className="flex h-screen w-full bg-background-light dark:bg-background-dark transition-colors duration-300">
      <Sidebar />
      <main className="flex-1 flex flex-col overflow-hidden relative">
        <Header onToggleDarkMode={toggleDarkMode} isDarkMode={isDarkMode} />
        
        <div className="flex-1 overflow-y-auto p-4 md:p-8 scroll-smooth">
          <div className="max-w-7xl mx-auto space-y-7">
            {/* Top Stat Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
              <StatCard 
                label="Total Requests" 
                value={formatNumber(aggregated?.total_requests || 0)}
                trend={previousAggregated ? calculateChange(aggregated?.total_requests || 0, previousAggregated.total_requests || 0) : '12%'}
                trendDirection={previousAggregated ? calculateTrend(aggregated?.total_requests || 0, previousAggregated.total_requests || 0) : 'up'}
                icon="activity"
                colorClass="text-orange-400 bg-orange-400/10" 
              />
              <StatCard 
                label="Avg. Latency" 
                value={`${(aggregated?.avg_duration || 0).toFixed(0)}ms`}
                trend={previousAggregated ? calculateChange(aggregated?.avg_duration || 0, previousAggregated.avg_duration || 0) : '5ms'}
                trendDirection={previousAggregated ? calculateTrend(previousAggregated.avg_duration || 0, aggregated?.avg_duration || 0) : 'down'}
                icon="clock"
                colorClass="text-blue-400 bg-blue-400/10" 
              />
              <StatCard 
                label="Error Rate" 
                value={aggregated?.error_count || 0}
                trend="stable"
                trendDirection="neutral"
                icon="alert"
                colorClass="text-red-400 bg-red-400/10" 
              />
              <StatCard 
                label="Active Services" 
                value={healthServices.length > 0 ? healthServices.length.toString() : services.length.toString()}
                trend={healthServices.length > 0 ? '+2 new' : 'None'}
                trendDirection="up"
                icon="check"
                colorClass="text-orange-400 bg-orange-400/10" 
              />
            </div>

            {/* Middle Section: Chart and Service Health */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 space-y-6">
                <ThroughputChart metrics={metrics} />
                <AIInsights aggregated={aggregated} alerts={alerts} />
              </div>
              <ServiceHealth services={healthServices} />
            </div>

            {/* Bottom Section: Alerts */}
            <AlertsTable alerts={alerts} />
          </div>
        </div>
       </main>
    </div>
  );
}

export default App;
