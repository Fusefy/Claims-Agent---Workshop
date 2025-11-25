import { useState, useEffect, useMemo } from 'react';
import { LineChart, Line, AreaChart, Area, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer } from 'recharts';
import { LineChartOutlined, AlertOutlined, DatabaseOutlined, CheckCircleOutlined, ExclamationCircleOutlined, CloseCircleOutlined, ArrowUpOutlined, ArrowDownOutlined, ReloadOutlined } from '@ant-design/icons';
import { Tooltip } from 'antd';
import { MonitoringData, MetricAnalysisResult } from '@/types/monitoring';
import './Monitoring.css';

// Helper function to humanize metric keys
const humanizeMetricKey = (key: string): string => {
  if (!key) return '';
  const spaced = key
    .replace(/_/g, ' ')
    .replace(/([A-Z])/g, ' $1')
    .trim();
  const normalized = spaced.replace(/\bf1\b/gi, 'F1');
  return normalized.charAt(0).toUpperCase() + normalized.slice(1);
};

// Helper function to analyze metric runs
export function analyzeMetricRuns(runs: MonitoringData[]): MetricAnalysisResult {
  if (!runs || runs.length === 0) return {};

  const firstMetrics = runs[0].metrics;
  const metricNames = Object.keys(firstMetrics).filter((key) => !key.endsWith('_explanation'));

  const result: MetricAnalysisResult = {};

  for (const metric of metricNames) {
    const values: number[] = runs.map((r) => Number(r.metrics[metric]));
    const average = values.reduce((sum, v) => sum + v, 0) / (values.length || 1);

    let lastIncreaseCount = 0;
    for (let i = values.length - 1; i > 0; i--) {
      if (values[i] > values[i - 1]) lastIncreaseCount++;
      else break;
    }

    result[metric] = {
      average: parseFloat(average.toFixed(2)),
      lastIncreaseCount
    };
  }

  return result;
}

// Format date - supports both start_time and timestamp fields
const formatDate = (monitoringWindow: { start_time?: string; end_time?: string; timestamp?: string }): string => {
  const timestamp = monitoringWindow.start_time || monitoringWindow.timestamp || '';
  if (!timestamp) return 'N/A';
  const date = new Date(timestamp);
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
};

// MetricsChart Component
export const MetricsChart: React.FC<{
  data: MonitoringData[];
  title?: string;
}> = ({ data, title = 'Agent Performance Metrics Over Time (KPI)' }) => {
  const { percentageMetricsCharts, secondsMetricsCharts, metricsWithExp } = useMemo(() => {
    const percentageMetrics = [
      'Claims Processing Straight-Through Rate',
      'Error Rate on Approved Claims',
      'Time to Adjudication Reduction',
      'Claim Denial Rate',
      'Compliance Dashboard Accuracy',
      'Integration Accuracy'
    ];
    const secondsMetrics = ['Processing Latency'];

    const percentageMetricsCharts: any[] = [];
    const secondsMetricsCharts: any[] = [];
    const metricsWithExp: { metricName: string; explanation: string | number }[] = [];
    const allMetric: string[] = [];

    data.forEach((item) => {
      if (item.metrics) {
        let percentageMetricsChartsnewItem: any = { date: formatDate(item.monitoring_window) };
        let secondsMetricsChartsnewItem: any = { date: formatDate(item.monitoring_window) };

        Object.keys(item.metrics).forEach((key) => {
          if (key !== 'date' && !key.includes('explanation')) {
            if (!allMetric.includes(key)) {
              allMetric.push(key);
              if (item.metrics[`${key}_explanation`]) {
                metricsWithExp.push({
                  explanation: item.metrics[`${key}_explanation`] || '',
                  metricName: key
                });
              }
            }

            if (percentageMetrics.includes(key)) {
              percentageMetricsChartsnewItem[key] = item.metrics[key];
            }
            if (secondsMetrics.includes(key)) {
              secondsMetricsChartsnewItem[key] = item.metrics[key];
            }
          }
        });

        if (Object.keys(percentageMetricsChartsnewItem).length > 1) {
          percentageMetricsCharts.push(percentageMetricsChartsnewItem);
        }
        if (Object.keys(secondsMetricsChartsnewItem).length > 1) {
          secondsMetricsCharts.push(secondsMetricsChartsnewItem);
        }
      }
    });

    return { percentageMetricsCharts, secondsMetricsCharts, metricsWithExp };
  }, [data]);

  const palette = ['#1890ff', '#52c41a', '#faad14', '#f759ab', '#13c2c2', '#722ed1'];

  return (
    <div className="chart-card large">
      <div className="chart-header">
        <h3>{title}</h3>
        <div className="chart-legend">
          {metricsWithExp?.map((eachmetric, i) => (
            <span
              key={eachmetric?.metricName}
              className="legend-item"
              style={{ color: palette[i % palette.length] }}
            >
              {humanizeMetricKey(eachmetric?.metricName)}
              <Tooltip title={eachmetric?.explanation}>
                <ExclamationCircleOutlined style={{ marginLeft: 4, fontSize: 14 }} />
              </Tooltip>
            </span>
          ))}
        </div>
      </div>

      {/* Percentage Metrics Chart */}
      {percentageMetricsCharts.length > 0 && (
        <div className="chart-content">
          <ResponsiveContainer width="100%" height={350}>
            <LineChart data={percentageMetricsCharts}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="date" stroke="#6b7280" />
              <YAxis 
                stroke="#6b7280" 
                domain={[0, 100]} 
                label={{ value: 'Percentage (%)', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle' } }}
              />
              <RechartsTooltip
                content={({ active, payload, label }) => {
                  if (active && payload && payload.length) {
                    return (
                      <div
                        style={{
                          backgroundColor: '#fff',
                          border: '1px solid #e5e7eb',
                          borderRadius: '8px',
                          color: '#000',
                          padding: 12,
                          minWidth: 180,
                          maxWidth: 600,
                          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
                        }}
                      >
                        <div style={{ fontWeight: 600, marginBottom: 6 }}>{label}</div>
                        {payload.map((entry, idx) => {
                          const k = String(entry.dataKey);
                          const metricLabel = humanizeMetricKey(k);
                          const explanation = metricsWithExp.find(m => m.metricName === k)?.explanation || '';
                          return (
                            <div key={idx} style={{ marginBottom: 8 }}>
                              <div style={{ color: entry.color, fontWeight: 500 }}>
                                {metricLabel}: {entry.value}%
                              </div>
                              {explanation && (
                                <div style={{ fontSize: 12, color: '#6b7280', marginTop: 4 }}>
                                  {explanation}
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    );
                  }
                  return null;
                }}
              />
              {percentageMetricsCharts.length &&
                Object.entries(percentageMetricsCharts[0])
                  .filter(([key]) => !key.includes('date'))
                  .map(([key], index) => {
                    const colors = ['#1890ff', '#52c41a', '#faad14', '#722ed1'];
                    return (
                      <Line
                        key={key}
                        type="monotone"
                        dataKey={key}
                        stroke={colors[index % colors.length]}
                        strokeWidth={2}
                      />
                    );
                  })}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Seconds Metrics Chart */}
      {secondsMetricsCharts.length > 0 && (
        <div className="chart-content" style={{ marginTop: 40 }}>
          <ResponsiveContainer width="100%" height={350}>
            <LineChart data={secondsMetricsCharts}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="date" stroke="#6b7280" />
              <YAxis 
                stroke="#6b7280" 
                label={{ value: 'Seconds (s)', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle' } }}
              />
              <RechartsTooltip
                content={({ active, payload, label }) => {
                  if (active && payload && payload.length) {
                    return (
                      <div
                        style={{
                          backgroundColor: '#fff',
                          border: '1px solid #e5e7eb',
                          borderRadius: '8px',
                          color: '#000',
                          padding: 12,
                          minWidth: 180,
                          maxWidth: 600,
                          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
                        }}
                      >
                        <div style={{ fontWeight: 600, marginBottom: 6 }}>{label}</div>
                        {payload.map((entry, idx) => {
                          const k = String(entry.dataKey);
                          const metricLabel = humanizeMetricKey(k);
                          const explanation = metricsWithExp.find(m => m.metricName === k)?.explanation || '';
                          return (
                            <div key={idx} style={{ marginBottom: 8 }}>
                              <div style={{ color: entry.color, fontWeight: 500 }}>
                                {metricLabel}: {entry.value}s
                              </div>
                              {explanation && (
                                <div style={{ fontSize: 12, color: '#6b7280', marginTop: 4 }}>
                                  {explanation}
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    );
                  }
                  return null;
                }}
              />
              {secondsMetricsCharts.length &&
                Object.entries(secondsMetricsCharts[0])
                  .filter(([key]) => !key.includes('date'))
                  .map(([key], index) => {
                    const colors = ['#1890ff', '#52c41a', '#faad14', '#722ed1'];
                    return (
                      <Line
                        key={key}
                        type="monotone"
                        dataKey={key}
                        stroke={colors[index % colors.length]}
                        strokeWidth={2}
                      />
                    );
                  })}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
};

// Main Monitoring Component
export default function Monitoring() {
  const [rawData, setRawData] = useState<MonitoringData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMonitoringData = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/monitoring/all`);
      
      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('No monitoring data files found. Please add monitoring JSON files to backend/monitoring/ directory.');
        }
        throw new Error(`Failed to fetch monitoring data: ${response.statusText}`);
      }
      
      const data = await response.json();
      // Sort by monitoring window start time in chronological order (oldest to newest)
      const sortedRuns = (data.runs || []).sort((a: MonitoringData, b: MonitoringData) => {
        const timeA = new Date(a.monitoring_window.start_time || a.monitoring_window.timestamp || 0).getTime();
        const timeB = new Date(b.monitoring_window.start_time || b.monitoring_window.timestamp || 0).getTime();
        return timeA - timeB;
      });
      setRawData(sortedRuns);
      setIsLoading(false);
    } catch (err) {
      console.error('[MONITORING] Error fetching data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load monitoring data');
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchMonitoringData();
  }, []);

  const driftData = rawData.map((item) => ({
    date: formatDate(item.monitoring_window),
    drift_magnitude: (item.drift.drift_magnitude * 100).toFixed(1),
    threshold: (item.drift.threshold * 100).toFixed(1),
    has_drift: item.drift.has_drift,
    drift_share: (item.drift.drift_share * 100).toFixed(1),
    drift_summary_explanation: item.drift_summary_explanation || '',
    provider_network_id: item.drift.provider_network_id,
    denial_rate_increase: item.drift.denial_rate_increase,
    affected_claims: item.drift.affected_claims,
    drifted_features: item.drift.drifted_features || []
  }));

  const statusData = [
    { name: 'Success', value: rawData.filter((item) => item.status.includes('Success')).length, color: '#52c41a' },
    { name: 'Partial Failure', value: rawData.filter((item) => item.status.includes('Partial Failure')).length, color: '#faad14' },
    { name: 'Failed', value: rawData.filter((item) => item.status.includes('Failed')).length, color: '#f5222d' }
  ];

  const getStatusIcon = (status: string) => {
    if (status.includes('Success')) return <CheckCircleOutlined className="status-success" />;
    if (status.includes('Partial')) return <ExclamationCircleOutlined className="status-warning" />;
    return <CloseCircleOutlined className="status-error" />;
  };

  const totalAlerts = rawData.reduce((acc, item) => acc + item.alerts.length, 0);

  const metricKeys = rawData[0]
    ? (Object.keys(rawData[0].metrics).filter((k) => !String(k).includes('explanation')))
    : [];

  const primaryMetricKey = metricKeys[0];

  // Calculate average value for the selected metric
  let avgPrimaryMetric = 0;
  if (rawData.length && primaryMetricKey) {
    const sum = rawData.reduce((acc, item) => acc + Number(item.metrics[primaryMetricKey] || 0), 0);
    avgPrimaryMetric = sum / rawData.length;
  }

  const driftDetected = rawData.filter((item) => item.drift.has_drift).length;
  const avgMissingValues = rawData.reduce((acc, item) => acc + item.data_quality.missing_values, 0) / rawData.length;

  const { average, lastIncreaseCount, metricName } = useMemo(() => {
    const metricAvgObj = analyzeMetricRuns(rawData);
    const firstMetricName = primaryMetricKey || '';
    const findone = metricAvgObj[firstMetricName];

    return {
      metricName: humanizeMetricKey(firstMetricName),
      average: findone ? `${findone.average}%` : '0%',
      lastIncreaseCount: findone ? findone.lastIncreaseCount : 0
    };
  }, [rawData, primaryMetricKey]);

  if (isLoading) {
    return (
      <div className="nodata">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        <p style={{ marginTop: 16, color: '#6b7280' }}>Loading monitoring data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="nodata">
        <AlertOutlined style={{ fontSize: 48, color: '#f5222d', marginBottom: 16 }} />
        <p style={{ color: '#f5222d', fontWeight: 600, marginBottom: 8 }}>Error Loading Monitoring Data</p>
        <p style={{ color: '#6b7280', marginBottom: 16 }}>{error}</p>
        <button
          onClick={fetchMonitoringData}
          style={{
            padding: '8px 16px',
            background: '#1890ff',
            color: 'white',
            border: 'none',
            borderRadius: 6,
            cursor: 'pointer',
            fontSize: 14,
            fontWeight: 500
          }}
        >
          <ReloadOutlined style={{ marginRight: 8 }} />
          Retry
        </button>
      </div>
    );
  }

  if (!rawData?.length) {
    return (
      <div className="nodata">
        <DatabaseOutlined style={{ fontSize: 48, color: '#d9d9d9', marginBottom: 16 }} />
        <p style={{ fontWeight: 600, marginBottom: 8 }}>No Monitoring Data Available</p>
        <p style={{ color: '#6b7280', fontSize: 14, maxWidth: 400, textAlign: 'center' }}>
          Add monitoring JSON files to <code>backend/monitoring/</code> directory with the naming pattern <code>monitoring_*.json</code>
        </p>
      </div>
    );
  }

  // Check if there's a critical drift alert
  const hasCriticalDrift = rawData.some((item) => 
    item.drift.has_drift && 
    item.alerts.some((alert) => alert.severity === 'critical' && alert.type === 'drift')
  );

  const latestDriftRun = rawData
    .slice()
    .reverse()
    .find((item) => 
      item.drift.has_drift && 
      item.alerts.some((alert) => alert.severity === 'critical' && alert.type === 'drift')
    );

  return (
    <div className="dashboard">
      {/* Critical Drift Alert Banner */}
      {hasCriticalDrift && latestDriftRun && (
        <div
          style={{
            background: '#ffe4e6',
            border: '1px solid #fecaca',
            borderRadius: '8px',
            padding: '14px 18px',
            marginBottom: '24px'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '10px' }}>
            <span style={{ fontSize: 18, marginTop: 1 }}>🚨</span>
            <div style={{ flex: 1 }}>
              <h3 style={{ margin: 0, fontSize: 14, fontWeight: 600, color: '#1f2937', marginBottom: 6 }}>
                Critical AI Drift Detection Alert
              </h3>
              
              <p style={{ margin: 0, fontSize: 13, color: '#6b7280', lineHeight: 1.5, marginBottom: 10 }}>
                ⚠️ CRITICAL DRIFT ALERT: Model is denying claims from specific provider networks at a significantly higher rate than baseline. Provider network distribution has shifted, with denial rates increasing by 23% for certain network IDs. This triggers an AI GRC risk mitigation workflow requiring immediate investigation.
              </p>
              
              {/* Inline Metrics */}
              <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', fontSize: 13 }}>
                <div>
                  <span style={{ fontWeight: 600, color: '#1f2937' }}>Drift Magnitude:</span>{' '}
                  <span style={{ color: '#6b7280' }}>{(latestDriftRun.drift.drift_magnitude * 100).toFixed(1)}%</span>
                </div>
                <div>
                  <span style={{ fontWeight: 600, color: '#1f2937' }}>Threshold:</span>{' '}
                  <span style={{ color: '#6b7280' }}>{(latestDriftRun.drift.threshold * 100).toFixed(1)}%</span>
                </div>
                <div>
                  <span style={{ fontWeight: 600, color: '#1f2937' }}>Affected Features:</span>{' '}
                  <span style={{ color: '#6b7280' }}>
                    {latestDriftRun.drift.drifted_features?.map(f => 
                      f.replace(/_/g, ' ')
                    ).join(', ') || 'N/A'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Dashboard Header */}
      <div className="dashboard-header">
        <div className="header-content">
          <div style={{ marginBottom: 16 }}>
            <h2 style={{ margin: 0, fontSize: 24, fontWeight: 600 }}>AI Agent Monitoring</h2>
          </div>
          <div className="header-stats">
            <div className="stat-item">
              <span className="stat-label">
                Agent Runs Monitored
                <Tooltip title="Number of recent monitoring periods (runs) for this agent.">
                  <ExclamationCircleOutlined style={{ marginLeft: 4 }} />
                </Tooltip>
              </span>
              <span className="stat-value">{rawData.length}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">
                {primaryMetricKey ? `Average ${humanizeMetricKey(String(primaryMetricKey))}` : 'Average Metric'}
                <Tooltip title="Average value of the primary metric across recent runs.">
                  <ExclamationCircleOutlined style={{ marginLeft: 4 }} />
                </Tooltip>
              </span>
              <span className="stat-value">
                {isNaN(avgPrimaryMetric) ? '0.0' : avgPrimaryMetric.toFixed(1) + '%'}
              </span>
            </div>
            <div className="stat-item">
              <span className="stat-label">
                Active Alerts
                <Tooltip title="Total number of alerts triggered in recent runs.">
                  <ExclamationCircleOutlined style={{ marginLeft: 4 }} />
                </Tooltip>
              </span>
              <span className="stat-value error">{totalAlerts}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="dashboard-content">
        {/* Overview Cards */}
        <div className="overview-section">
          <div className="metric-card">
            <div className="card-header">
              <LineChartOutlined className="card-icon" />
              <h3>
                Agent Performance
                <Tooltip title={`Shows the average of ${metricName} over the last ${rawData.length} runs.`}>
                  <ExclamationCircleOutlined style={{ marginLeft: 6, fontSize: 16 }} />
                </Tooltip>
              </h3>
            </div>
            <div className="card-content">
              <div className="large-metric">
                <span className="metric-value">{average}</span>
                <span className="metric-label">{metricName ? `Average ${metricName}` : 'Average Metric'}</span>
              </div>
              <div className={`trend-indicator ${lastIncreaseCount > 0 ? '' : 'negative'}`}>
                {lastIncreaseCount > 0 ? (
                  <ArrowUpOutlined className="trend-up" />
                ) : (
                  <ArrowDownOutlined className="trend-up" />
                )}
                <span>
                  {lastIncreaseCount > 0 ? '+' : ''}{lastIncreaseCount}% from last run
                </span>
              </div>
            </div>
          </div>

          <div className="metric-card">
            <div className="card-header">
              <AlertOutlined className="card-icon" />
              <h3>
                Drift Detection
                <Tooltip title="Number of runs where data drift was detected.">
                  <ExclamationCircleOutlined style={{ marginLeft: 6, fontSize: 16 }} />
                </Tooltip>
              </h3>
            </div>
            <div className="card-content">
              <div className="large-metric">
                <span className="metric-value">{driftDetected}</span>
                <span className="metric-label">Runs with Drift Detected</span>
              </div>
              
              <div className="drift-features">
                {(() => {
                  const allFeatures = rawData.flatMap((item) => item.drift.drifted_features || []);
                  const uniqueFeatures = Array.from(new Set(allFeatures));
                  const criticalFeatures = ['provider_network', 'claim_denial_rate', 'provider_id'];
                  
                  return uniqueFeatures.slice(0, 5).map((feature, idx) => {
                    const isCritical = criticalFeatures.includes(feature);
                    const formattedFeature = feature
                      .replace(/_/g, ' ')
                      .replace(/\b\w/g, l => l.toUpperCase());
                    
                    return (
                      <span 
                        key={idx} 
                        className="feature-tag"
                        style={isCritical ? {
                          background: '#fee2e2',
                          border: '1px solid #ef4444',
                          color: '#991b1b',
                          fontWeight: 600
                        } : {}}
                      >
                        {formattedFeature}
                      </span>
                    );
                  });
                })()}
              </div>
            </div>
          </div>

          <div className="metric-card">
            <div className="card-header">
              <DatabaseOutlined className="card-icon" />
              <h3>
                Data Quality
                <Tooltip title="Average percentage of missing values per run.">
                  <ExclamationCircleOutlined style={{ marginLeft: 6, fontSize: 16 }} />
                </Tooltip>
              </h3>
            </div>
            <div className="card-content">
              <div className="large-metric">
                <span className="metric-value">
                  {isNaN(avgMissingValues) ? '0.0' : (avgMissingValues * 100).toFixed(1)}%
                </span>
                <span className="metric-label">Avg Missing Values per Run</span>
              </div>
              <div className="drift-features">
                {rawData
                  .flatMap((item) => item.data_quality.constant_columns || [])
                  .slice(0, 3)
                  .map((feature, idx) => (
                    <span key={idx} className="feature-tag">
                      {feature}
                    </span>
                  ))}
              </div>
            </div>
          </div>
        </div>

        {/* Main Charts */}
        <div className="charts-section">
          <MetricsChart data={rawData} />

          <div className="chart-card">
            <div className="chart-header">
              <h3>Data Drift Magnitude (KPI)</h3>
            </div>
            <div className="chart-content">
              <ResponsiveContainer width="100%" height={250}>
                <AreaChart data={driftData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="date" stroke="#6b7280" />
                  <YAxis stroke="#6b7280" />
                  <RechartsTooltip
                    content={({ active, payload, label }) => {
                      if (active && payload && payload.length) {
                        const drift = payload[0]?.payload;
                        return (
                          <div
                            style={{
                              backgroundColor: '#fff',
                              border: '1px solid #e5e7eb',
                              borderRadius: '8px',
                              color: '#000',
                              padding: 12,
                              minWidth: 180,
                              maxWidth: 450,
                              boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
                            }}
                          >
                            <div style={{ fontWeight: 600, marginBottom: 6 }}>{label}</div>
                            <div style={{ marginBottom: 4 }}>
                              <strong>Drift:</strong> {drift.drift_magnitude}%
                            </div>
                            <div style={{ marginBottom: 4 }}>
                              <strong>Threshold:</strong> {drift.threshold}%
                            </div>
                            
                            {/* Provider Network Details */}
                            {drift.provider_network_id && (
                              <div style={{ 
                                marginTop: 8, 
                                paddingTop: 8, 
                                borderTop: '1px solid #e5e7eb' 
                              }}>
                                <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 4, color: '#991b1b' }}>
                                  Provider Network Alert:
                                </div>
                                <div style={{ fontSize: 12, marginBottom: 2 }}>
                                  <strong>Network:</strong> {drift.provider_network_id}
                                </div>
                                {drift.denial_rate_increase && (
                                  <div style={{ fontSize: 12, marginBottom: 2 }}>
                                    <strong>Denial Rate Increase:</strong> +{drift.denial_rate_increase}%
                                  </div>
                                )}
                                {drift.affected_claims && (
                                  <div style={{ fontSize: 12, marginBottom: 2 }}>
                                    <strong>Affected Claims:</strong> {drift.affected_claims.toLocaleString()}
                                  </div>
                                )}
                              </div>
                            )}
                            
                            {/* Drifted Features */}
                            {drift.drifted_features && drift.drifted_features.length > 0 && (
                              <div style={{ 
                                marginTop: 8, 
                                paddingTop: 8, 
                                borderTop: '1px solid #e5e7eb' 
                              }}>
                                <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 4 }}>
                                  Affected Features:
                                </div>
                                <div style={{ fontSize: 11, color: '#6b7280' }}>
                                  {drift.drifted_features.map((f: string) => 
                                    f.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())
                                  ).join(', ')}
                                </div>
                              </div>
                            )}
                            
                            {drift.drift_summary_explanation && (
                              <div style={{ fontSize: 12, color: '#6b7280', marginTop: 8, paddingTop: 8, borderTop: '1px solid #e5e7eb' }}>
                                {drift.drift_summary_explanation}
                              </div>
                            )}
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Area type="monotone" dataKey="drift_magnitude" stroke="#ff4d4f" fill="#ff4d4f" fillOpacity={0.3} />
                  <Area type="monotone" dataKey="threshold" stroke="#faad14" fill="none" strokeDasharray="5 5" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
            {(() => {
              const driftRun = rawData
                .slice()
                .reverse()
                .find((item) => item.drift.has_drift && item.drift_summary_explanation);
              return (
                driftRun &&
                driftRun.drift_summary_explanation && (
                  <div
                    style={{
                      marginTop: 12,
                      background: '#fffbe6',
                      border: '1px solid #ffe58f',
                      borderRadius: 6,
                      padding: 10,
                      color: '#614700',
                      fontSize: 13
                    }}
                  >
                    <div style={{ marginBottom: 4 }}>
                      <strong>Date:</strong>{' '}
                      {formatDate(driftRun.monitoring_window)}
                    </div>
                    <div style={{ marginBottom: 4 }}>
                      <strong>Drift Magnitude:</strong> {(driftRun.drift.drift_magnitude * 100).toFixed(2)}%{'  '}
                      <strong>Threshold:</strong> {(driftRun.drift.threshold * 100).toFixed(2)}%
                    </div>
                    <div style={{ marginBottom: 4 }}>
                      <strong>Drifted Features:</strong>{' '}
                      {driftRun.drift.drifted_features && driftRun.drift.drifted_features.length > 0
                        ? driftRun.drift.drifted_features.join(', ')
                        : 'N/A'}
                    </div>
                    <div>
                      <strong>Drift Summary:</strong> {driftRun.drift_summary_explanation}
                    </div>
                  </div>
                )
              );
            })()}
          </div>

          <div className="chart-card">
            <div className="chart-header">
              <h3>Agent Status Distribution (KPI)</h3>
            </div>
            <div className="chart-content">
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={statusData}
                    cx="50%"
                    cy="50%"
                    innerRadius={40}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {statusData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <RechartsTooltip
                    contentStyle={{
                      backgroundColor: '#fff',
                      border: '1px solid #e5e7eb',
                      borderRadius: '8px',
                      color: '#000',
                      boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
              <div className="pie-legend">
                {statusData.map((item, index) => (
                  <div key={index} className="pie-legend-item">
                    <span className="legend-dot" style={{ backgroundColor: item.color }}></span>
                    <span>
                      {item.name}: {item.value}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Agent Status Table */}
        <div className="status-section">
          <div className="status-card">
            <div className="card-header">
              <h3>Agent Execution Status (KPI)</h3>
            </div>
            <div className="status-table">
              {rawData.map((item, index) => (
                <div key={index} className="status-row">
                  <div className="status-info">
                    <div className="status-icon">{getStatusIcon(item.status)}</div>
                    <div className="status-details">
                      <div className="model-name">Claims Processing Agent</div>
                      <div className="job-info">
                        Run #{index + 1} • {formatDate(item.monitoring_window)}
                      </div>
                    </div>
                  </div>
                  <div className="status-metrics">
                    <div className="metric-pill">
                      <span className="metric-label">
                        {humanizeMetricKey(String(primaryMetricKey))}
                      </span>
                      <span className="metric-value">
                        {item.metrics[primaryMetricKey] ? `${item.metrics[primaryMetricKey]}%` : 'N/A'}
                      </span>
                    </div>
                    <div className="metric-pill">
                      <span className="metric-label">Drift</span>
                      <span className={`metric-value ${item.drift.has_drift ? 'error' : 'success'}`}>
                        {item.drift.has_drift ? 'Yes' : 'No'}
                      </span>
                    </div>
                    <div className="metric-pill">
                      <span className="metric-label">Alerts</span>
                      <span className={`metric-value ${item.alerts.length > 0 ? 'error' : 'success'}`}>
                        {item.alerts.length}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
