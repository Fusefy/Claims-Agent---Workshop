-- ============================================
-- Seed Data: Drift Detection Demo Claim
-- ============================================
-- This inserts a sample claim that demonstrates AI drift detection
-- for the AI GRC risk mitigation workflow

INSERT INTO proposedclaim (
    claim_id,
    claim_name,
    customer_id,
    policy_id,
    claim_type,
    network_status,
    date_of_service,
    claim_amount,
    approved_amount,
    claim_status,
    error_type,
    ai_reasoning,
    payment_status,
    guardrail_summary,
    created_at,
    updated_at
) VALUES (
    'CLM-DRIFT-2025-001',
    'Provider Network Drift Detection Case',
    'CUST-789456',
    'POL-XYZ-9876',
    'Medical',
    'In-Network',
    '2025-11-18 00:00:00',
    3250.00,
    0.00,
    'Denied',
    NULL,
    '⚠️ DRIFT DETECTION ALERT: This claim was denied as part of an elevated denial rate pattern detected for specific provider networks. The AI model has identified a 23% increase in denial rates for claims from this provider network compared to baseline. This triggers an AI GRC (Governance, Risk, and Compliance) risk mitigation workflow. The claim requires human review to ensure no bias or systematic errors are affecting provider network processing. Denial factors: Provider network ID shows anomalous processing patterns, claim characteristics fall within drifted feature space (provider_network, claim_denial_rate, provider_id).',
    'Not Processed',
    '{"fraud_status": "No Fraud", "hitl_flag": true, "fraud_reason": "Drift detection triggered - requires human review for potential bias", "drift_detected": true, "drift_magnitude": 0.24, "affected_features": ["provider_network", "claim_denial_rate", "provider_id"]}'::jsonb,
    '2025-11-20 10:15:00',
    '2025-11-20 10:15:30'
)
ON CONFLICT (claim_id) DO NOTHING;

-- ============================================
-- Seed Data: Claim History for Drift Claim
-- ============================================

INSERT INTO claimhistory (
    claim_id,
    old_status,
    new_status,
    changed_by,
    role,
    change_reason,
    timestamp
) VALUES 
(
    'CLM-DRIFT-2025-001',
    'New',
    'Pending',
    'Claims Processing Agent',
    'AI Agent',
    'Claim received and entered processing queue',
    '2025-11-20 10:15:00'
),
(
    'CLM-DRIFT-2025-001',
    'Pending',
    'Denied',
    'Claims Processing Agent',
    'AI Agent',
    'Drift detection alert triggered - elevated denial rate for provider network. Requires GRC review.',
    '2025-11-20 10:15:30'
)
ON CONFLICT DO NOTHING;
