import React, { useState, useEffect } from 'react';
import { Alert } from '../hooks/useAlerts';

interface AIInsightsProps {
  aggregated?: any;
  alerts?: Alert[];
}

const AIInsights: React.FC<AIInsightsProps> = ({ aggregated, alerts = [] }) => {
  const [insight, setInsight] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    // Generate insight based on real metrics and alerts
    setLoading(true);
    const timer = setTimeout(() => {
      let generatedInsight = '';
      
      // Check for critical alerts first
      const criticalAlerts = alerts.filter(a => a.severity === 'Critical');
      const warningAlerts = alerts.filter(a => a.severity === 'Warning');
      
      if (criticalAlerts.length > 0) {
        const services = criticalAlerts.map(a => a.service).join(', ');
        generatedInsight = `Critical: ${criticalAlerts.length} critical alert${criticalAlerts.length > 1 ? 's' : ''} detected affecting ${services}. Immediate investigation required to prevent service degradation.`;
      } else if (warningAlerts.length > 0) {
        const services = warningAlerts.map(a => a.service).slice(0, 2).join(', ');
        generatedInsight = `Warning: ${warningAlerts.length} warning${warningAlerts.length > 1 ? 's' : ''} detected on ${services}${warningAlerts.length > 2 ? ' and others' : ''}. Monitor closely for potential escalation.`;
      } else if (aggregated) {
        // Analyze metrics for insights
        const errorRate = aggregated.error_count || 0;
        const avgDuration = aggregated.avg_duration || 0;
        const totalRequests = aggregated.total_requests || 0;
        
        if (errorRate > 10) {
          generatedInsight = `Attention: Error rate is elevated at ${errorRate} errors across ${totalRequests.toLocaleString()} requests. Review recent deployments and service logs.`;
        } else if (avgDuration > 500) {
          generatedInsight = `Performance: Average latency is ${avgDuration.toFixed(0)}ms. Consider scaling resources or optimizing database queries to improve response times.`;
        } else if (totalRequests > 10000) {
          generatedInsight = `System health is excellent. Successfully processed ${totalRequests.toLocaleString()} requests with minimal errors and optimal latency. All services operating within normal parameters.`;
        } else if (totalRequests > 0) {
          generatedInsight = `Platform operational. Processing ${totalRequests.toLocaleString()} requests with stable performance. Continue monitoring for anomalies.`;
        } else {
          generatedInsight = 'Monitoring all services. Awaiting incoming metrics to provide detailed insights and recommendations.';
        }
      } else {
        generatedInsight = 'Vantage AI is analyzing your platform metrics. Insights will be generated based on real-time data and alert patterns.';
      }
      
      setInsight(generatedInsight);
      setLoading(false);
    }, 1500);

    return () => clearTimeout(timer);
  }, [aggregated, alerts]);

  return (
    <div className="bg-gradient-to-br from-orange-50 to-white dark:from-orange-950/20 dark:to-surface-dark p-6 rounded-2xl shadow-soft border border-orange-100 dark:border-orange-900/30 flex items-start gap-4">
      <div className="bg-orange-100 dark:bg-orange-500/20 p-3 rounded-xl shrink-0">
        <span className="material-icons-round text-orange-500 text-2xl">psychology</span>
      </div>
      <div className="space-y-1">
        <div className="flex items-center gap-2">
          <h4 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider">Vantage AI Insight</h4>
          {loading && <span className="w-1.5 h-1.5 rounded-full bg-primary animate-ping"></span>}
        </div>
        <p className={`text-sm leading-relaxed ${loading ? 'text-slate-400 italic' : 'text-slate-600 dark:text-slate-300'}`}>
          {loading ? 'Analyzing system metrics...' : insight}
        </p>
      </div>
    </div>
  );
};

export default AIInsights;
