// Monitoring data types matching Dashboard.tsx structure

export interface MonitoringData {
  run_id: string;
  job_id: string;
  input_dataset: string;
  model_id: string;
  model_type: string;
  is_baseline: boolean;
  monitoring_window: {
    start_time?: string;  // ISO-8601 format
    end_time?: string;    // ISO-8601 format
    timestamp?: string;   // For backward compatibility
  };
  status: string;
  metrics: {
    [key: string]: number | string;
  };
  drift: {
    drift_magnitude: number;
    threshold: number;
    has_drift: boolean;
    drift_share: number;
    drifted_features?: string[];
    data_privacy_issues?: {
      unmasked_fields: string[];
      affected_claims: number;
      severity: string;
      details: string;
    };
    // Enhanced drift metadata fields (optional)
    provider_network_id?: string;
    denial_rate_increase?: number;
    affected_claims?: number;
    baseline_denial_rate?: number;
    current_denial_rate?: number;
    severity?: 'info' | 'warning' | 'critical';
  };
  drift_summary_explanation?: string;
  data_quality: {
    missing_values: number;
    constant_columns?: string[];
  };
  alerts: Array<{
    type: string;
    message: string;
    severity: string;
  }>;
}

export interface MetricAnalysis {
  average: number;
  lastIncreaseCount: number;
}

export type MetricAnalysisResult = Record<string, MetricAnalysis>;

export interface PercentageMetricsChartItem {
  date: string;
  [key: string]: string | number;
}

export interface SecondsMetricsChartItem {
  date: string;
  [key: string]: string | number;
}
