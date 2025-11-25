import { MonitoringData } from '@/types/monitoring';

// Mock monitoring data for Claims Processing Agent
export const monitoringMockData: MonitoringData[] = [
  {
    monitoring_window: {
      timestamp: '2025-09-30T10:00:00Z'
    },
    status: 'Success',
    metrics: {
      claimsProcessingStraightThroughRate: 95.5,
      claimsProcessingStraightThroughRate_explanation: 'Percentage of claims processed automatically without manual intervention',
      errorRateOnApprovedClaims: 5.2,
      errorRateOnApprovedClaims_explanation: 'Proportion of processing errors in approved claims',
      timeToAdjudicationReduction: 45.0,
      timeToAdjudicationReduction_explanation: 'Percentage improvement in claim adjudication speed',
      processingLatency: 12,
      processingLatency_explanation: 'Average time in seconds to process a claim'
    },
    drift: {
      drift_magnitude: 0.08,
      threshold: 0.15,
      has_drift: false,
      drift_share: 0.03,
      drifted_features: []
    },
    data_quality: {
      missing_values: 0.002,
      constant_columns: []
    },
    alerts: []
  },
  {
    monitoring_window: {
      timestamp: '2025-10-15T10:00:00Z'
    },
    status: 'Success',
    metrics: {
      claimsProcessingStraightThroughRate: 96.8,
      claimsProcessingStraightThroughRate_explanation: 'Percentage of claims processed automatically without manual intervention',
      errorRateOnApprovedClaims: 4.8,
      errorRateOnApprovedClaims_explanation: 'Proportion of processing errors in approved claims',
      timeToAdjudicationReduction: 47.1,
      timeToAdjudicationReduction_explanation: 'Percentage improvement in claim adjudication speed',
      processingLatency: 10,
      processingLatency_explanation: 'Average time in seconds to process a claim'
    },
    drift: {
      drift_magnitude: 0.12,
      threshold: 0.15,
      has_drift: false,
      drift_share: 0.05,
      drifted_features: []
    },
    data_quality: {
      missing_values: 0.0015,
      constant_columns: []
    },
    alerts: []
  },
  {
    monitoring_window: {
      timestamp: '2025-11-05T10:00:00Z'
    },
    status: 'Partial Failure',
    metrics: {
      claimsProcessingStraightThroughRate: 98.1,
      claimsProcessingStraightThroughRate_explanation: 'Percentage of claims processed automatically without manual intervention',
      errorRateOnApprovedClaims: 4.5,
      errorRateOnApprovedClaims_explanation: 'Proportion of processing errors in approved claims',
      timeToAdjudicationReduction: 49.2,
      timeToAdjudicationReduction_explanation: 'Percentage improvement in claim adjudication speed',
      processingLatency: 9,
      processingLatency_explanation: 'Average time in seconds to process a claim'
    },
    drift: {
      drift_magnitude: 0.18,
      threshold: 0.15,
      has_drift: true,
      drift_share: 0.12,
      drifted_features: ['provider_network', 'claim_denial_rate', 'provider_id']
    },
    drift_summary_explanation: '⚠️ DRIFT ALERT: Model is denying claims from specific provider networks at a higher rate than baseline. Provider network distribution has shifted, with denial rates increasing for certain network IDs. This may indicate potential bias or systematic processing issues requiring investigation.',
    data_quality: {
      missing_values: 0.003,
      constant_columns: ['claim_system_version', 'account_number_masking_failure']
    },
    alerts: [
      {
        type: 'drift',
        severity: 'warning',
        message: 'Data drift detected in multiple features'
      },
      {
        type: 'data_quality',
        severity: 'info',
        message: 'Slight increase in missing values'
      },
      {
        type: 'performance',
        severity: 'info',
        message: 'Processing latency below threshold'
      }
    ]
  },
  {
    monitoring_window: {
      timestamp: '2025-11-20T10:00:00Z'
    },
    status: 'Partial Failure',
    metrics: {
      claimsProcessingStraightThroughRate: 96.3,
      claimsProcessingStraightThroughRate_explanation: 'Percentage of claims processed automatically without manual intervention',
      errorRateOnApprovedClaims: 5.8,
      errorRateOnApprovedClaims_explanation: 'Proportion of processing errors in approved claims',
      timeToAdjudicationReduction: 47.5,
      timeToAdjudicationReduction_explanation: 'Percentage improvement in claim adjudication speed',
      processingLatency: 11,
      processingLatency_explanation: 'Average time in seconds to process a claim'
    },
    drift: {
      drift_magnitude: 0.24,
      threshold: 0.15,
      has_drift: true,
      drift_share: 0.18,
      drifted_features: ['provider_network', 'claim_denial_rate', 'provider_id']
    },
    drift_summary_explanation: '⚠️ CRITICAL DRIFT ALERT: Model is denying claims from specific provider networks at a significantly higher rate than baseline. Provider network distribution has shifted, with denial rates increasing by 23% for certain network IDs. This triggers an AI GRC risk mitigation workflow requiring immediate investigation.',
    data_quality: {
      missing_values: 0.0025,
      constant_columns: []
    },
    alerts: [
      {
        type: 'drift',
        severity: 'critical',
        message: 'Critical drift detected: Provider network denial rate anomaly'
      },
      {
        type: 'bias',
        severity: 'warning',
        message: 'Potential bias detected in provider network processing'
      },
      {
        type: 'grc',
        severity: 'critical',
        message: 'AI GRC risk mitigation workflow triggered'
      },
      {
        type: 'performance',
        severity: 'warning',
        message: 'Processing latency increased above threshold'
      }
    ]
  }
];
