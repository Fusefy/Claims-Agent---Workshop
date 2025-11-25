"""
Real Metrics Validation Script
Validates agent performance metrics and generates KPI report
Calculates the following metrics:
  1. Claims Processing Straight-Through Rate (STR)
  2. Error Rate on Approved Claims
  3. Time to Adjudication Reduction
  4. Claim Denial Rate
  5. Compliance Dashboard Accuracy
  6. Integration Accuracy
  7. Processing Latency
  8. Security Threats Detection
"""

import os
import json
import logging
import sys
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import statistics
from collections import Counter

# Add parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.claim_repository import claim_repository
from database.hitl_repository import hitl_repository
from database.history_repository import history_repository
from database.connection import db_pool
from utils.config import (
    DB_HOST, DB_PORT, DB_NAME, DB_USER,
    METRICS_MODEL_NAME, METRICS_MODEL_VERSION,
    METRICS_WEIGHTS, METRICS_THRESHOLDS,
    METRICS_MANUAL_TIME_MULTIPLIER, METRICS_STATUS
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MetricsValidator:
    """Validates real agent metrics and generates KPI report"""
    
    def __init__(self):
        """Initialize metrics validator"""
        # Validate metric weights
        total_weight = sum(METRICS_WEIGHTS.values())
        if not (0.99 < total_weight < 1.01):  # Allow small floating point errors
            logger.warning(f"⚠️  METRICS_WEIGHTS sum to {total_weight}, expected 1.0. Health score may be skewed.")
        
        self.metrics_report = {
            "timestamp": datetime.now().isoformat(),
            "script_name": "metrics_validation_script.py",
            "description": "Real metrics validation for claim processing agents",
            "database_info": {
                "host": DB_HOST,
                "port": DB_PORT,
                "database": DB_NAME,
                "connection_status": "not_checked"
            },
            "raw_data": {},
            "calculated_metrics": {},
            "kpi_summary": {},
            "errors": []
        }
        self.claims_data = []
        self.hitl_data = []
        self.history_data = []
    
    def initialize_database(self) -> bool:
        """Initialize database connection"""
        logger.info("=" * 80)
        logger.info("DATABASE CONNECTION")
        logger.info("=" * 80)
        
        try:
            db_pool.initialize_pool()
            logger.info("✅ Database pool initialized successfully")
            self.metrics_report["database_info"]["connection_status"] = "connected"
            return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {e}")
            self.metrics_report["database_info"]["connection_status"] = "failed"
            self.metrics_report["errors"].append({
                "step": "Database initialization",
                "error": str(e),
                "traceback": traceback.format_exc()
            })
            return False
    
    def generate_data_quality_report(self) -> None:
        """Generate detailed data quality report"""
        logger.info("\n" + "=" * 80)
        logger.info("DATA QUALITY ASSESSMENT")
        logger.info("=" * 80)
        
        if not self.claims_data:
            logger.warning("❌ No claims data available")
            return
        
        # Check data completeness
        logger.info(f"\n📊 Data Completeness (out of {len(self.claims_data)} claims):\n")
        
        completeness = {
            "error_type": len([c for c in self.claims_data if c.error_type]),
            "ai_reasoning": len([c for c in self.claims_data if c.ai_reasoning]),
            "guardrail_summary": len([c for c in self.claims_data if c.guardrail_summary and len(c.guardrail_summary) > 0]),
            "claim_name": len([c for c in self.claims_data if c.claim_name]),
            "fraud_status": len([c for c in self.claims_data if c.guardrail_summary and c.guardrail_summary.get("fraud_status")])
        }
        
        for field, count in completeness.items():
            pct = (count / len(self.claims_data)) * 100
            status = "✅" if pct == 100 else "⚠️ " if pct >= 50 else "❌"
            logger.info(f"  {status} {field}: {count}/{len(self.claims_data)} ({pct:.1f}%)")
        
        # Check for orphaned data
        logger.info(f"\n🔗 Data Relationships:\n")
        
        hitl_claims = set([h.claim_id for h in self.hitl_data]) if self.hitl_data else set()
        history_claims = set([h.claim_id for h in self.history_data]) if self.history_data else set()
        all_claim_ids = set([c.claim_id for c in self.claims_data])
        
        logger.info(f"  • Total claims: {len(all_claim_ids)}")
        logger.info(f"  • HITL references: {len(hitl_claims)} ({len(hitl_claims)/len(all_claim_ids)*100:.1f}%)")
        logger.info(f"  • History records: {len(history_claims)} ({len(history_claims)/len(all_claim_ids)*100:.1f}%)")
        
        # Find orphaned records
        orphaned_hitl = hitl_claims - all_claim_ids
        orphaned_history = history_claims - all_claim_ids
        
        if orphaned_hitl:
            logger.warning(f"  ⚠️  Orphaned HITL records: {len(orphaned_hitl)}")
        if orphaned_history:
            logger.warning(f"  ⚠️  Orphaned history records: {len(orphaned_history)}")
        
        # Sample data inspection
        logger.info(f"\n🔍 Sample Claim Details (first 3):\n")
        for i, claim in enumerate(self.claims_data[:3], 1):
            logger.info(f"  Claim {i}: {claim.claim_id}")
            logger.info(f"    ├─ Status: {claim.claim_status}")
            logger.info(f"    ├─ Amount: ${claim.claim_amount:.2f}")
            logger.info(f"    ├─ AI Reasoning: {claim.ai_reasoning or '❌ MISSING'}")
            logger.info(f"    ├─ Error Type: {claim.error_type or 'None'}")
            logger.info(f"    └─ Guardrail Data: {len(claim.guardrail_summary or {}) > 0 and '✅ Present' or '❌ MISSING'}")
    
    def fetch_raw_data(self) -> bool:
        """Fetch raw claim data from database"""
        logger.info("\n" + "=" * 80)
        logger.info("FETCHING RAW DATA")
        logger.info("=" * 80)
        
        try:
            # Fetch all claims
            logger.info("Fetching claims from database...")
            self.claims_data = claim_repository.get_all()
            logger.info(f"✅ Fetched {len(self.claims_data)} claims")
            
            # Store raw data
            self.metrics_report["raw_data"]["total_claims"] = len(self.claims_data)
            self.metrics_report["raw_data"]["claims_by_status"] = {}
            
            # Count by status
            for status in ["Approved", "Denied", "Pending"]:
                count = len([c for c in self.claims_data if c.claim_status == status])
                self.metrics_report["raw_data"]["claims_by_status"][status] = count
                logger.info(f"  - {status}: {count}")
            
            # Fetch claim history
            logger.info("Fetching claim history from database...")
            self.history_data = history_repository.get_all() if hasattr(history_repository, 'get_all') else []
            logger.info(f"✅ Fetched {len(self.history_data)} history records")
            
            # Fetch HITL queue
            logger.info("Fetching HITL queue from database...")
            self.hitl_data = hitl_repository.get_all() if hasattr(hitl_repository, 'get_all') else []
            logger.info(f"✅ Fetched {len(self.hitl_data)} HITL records")
            
            # Run data quality check
            self.generate_data_quality_report()
            
            return len(self.claims_data) > 0
            
        except Exception as e:
            logger.error(f"❌ Error fetching data: {e}")
            self.metrics_report["errors"].append({
                "step": "Data fetching",
                "error": str(e),
                "traceback": traceback.format_exc()
            })
            return False
    
    def calculate_straight_through_rate(self) -> Dict[str, Any]:
        """
        Calculate Claims Processing Straight-Through Rate (STR)
        Percentage of claims processed without manual intervention (HITL)
        """
        logger.info("\n" + "-" * 80)
        logger.info("METRIC 1: Claims Processing Straight-Through Rate (STR)")
        logger.info("-" * 80)
        
        try:
            if not self.claims_data:
                return {"value": 0, "unit": "percentage", "status": "insufficient_data"}
            
            # Count claims without HITL intervention
            hitl_claim_ids = set([h.claim_id for h in self.hitl_data]) if self.hitl_data else set()
            
            str_claims = [c for c in self.claims_data if c.claim_id not in hitl_claim_ids]
            str_rate = (len(str_claims) / len(self.claims_data)) * 100 if self.claims_data else 0
            
            metric = {
                "metric_name": "Straight-Through Rate (STR)",
                "definition": "Percentage of claims processed without manual intervention",
                "value": round(str_rate, 2),
                "unit": "percentage",
                "calculation": {
                    "total_claims": len(self.claims_data),
                    "str_claims": len(str_claims),
                    "hitl_claims": len(hitl_claim_ids),
                    "formula": f"{len(str_claims)} / {len(self.claims_data)} * 100"
                },
                "interpretation": "Higher is better - indicates less manual intervention needed",
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Total Claims: {len(self.claims_data)}")
            logger.info(f"STR Claims (no HITL): {len(str_claims)}")
            logger.info(f"HITL Claims: {len(hitl_claim_ids)}")
            logger.info(f"✅ STR: {str_rate:.2f}%")
            
            return metric
            
        except Exception as e:
            logger.error(f"❌ Error calculating STR: {e}")
            self.metrics_report["errors"].append({
                "step": "STR calculation",
                "error": str(e)
            })
            return {"value": 0, "status": "error"}
    
    def calculate_error_rate_on_approved(self) -> Dict[str, Any]:
        """
        Calculate Error Rate on Approved Claims
        Proportion of errors in approved claims
        """
        logger.info("\n" + "-" * 80)
        logger.info("METRIC 2: Error Rate on Approved Claims")
        logger.info("-" * 80)
        
        try:
            approved_claims = [c for c in self.claims_data if c.claim_status == "Approved"]
            
            if not approved_claims:
                logger.warning("⚠️  No approved claims found for error rate calculation")
                return {
                    "metric_name": "Error Rate on Approved Claims",
                    "definition": "Proportion of errors in approved claims showing processing quality",
                    "value": 0,
                    "unit": "percentage",
                    "calculation": {
                        "total_approved": 0,
                        "approved_with_errors": 0,
                        "approved_without_errors": 0
                    },
                    "status": "no_approved_claims",
                    "note": "No approved claims in dataset"
                }
            
            # Check for any error indicators
            error_claims = [c for c in approved_claims if (
                (c.error_type and c.error_type.strip() and c.error_type.lower() != "none") or
                (c.guardrail_summary and c.guardrail_summary.get("fraud_status") == "Fraud")
            )]
            
            error_rate = (len(error_claims) / len(approved_claims)) * 100
            
            metric = {
                "metric_name": "Error Rate on Approved Claims",
                "definition": "Proportion of errors in approved claims showing processing quality",
                "value": round(error_rate, 2),
                "unit": "percentage",
                "calculation": {
                    "total_approved": len(approved_claims),
                    "approved_with_errors": len(error_claims),
                    "approved_without_errors": len(approved_claims) - len(error_claims),
                    "formula": f"{len(error_claims)} / {len(approved_claims)} * 100"
                },
                "interpretation": "Lower is better - indicates fewer processing errors",
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Total Approved Claims: {len(approved_claims)}")
            logger.info(f"Approved with Errors: {len(error_claims)}")
            logger.info(f"Approved without Errors: {len(approved_claims) - len(error_claims)}")
            
            if error_claims:
                logger.info("Error Details:")
                for claim in error_claims:
                    fraud_status = claim.guardrail_summary.get('fraud_status') if claim.guardrail_summary else 'N/A'
                    logger.info(f"  • {claim.claim_id}: error_type={claim.error_type}, fraud={fraud_status}")
            
            logger.info(f"✅ Error Rate: {error_rate:.2f}%")
            
            return metric
            
        except Exception as e:
            logger.error(f"❌ Error calculating error rate: {e}")
            self.metrics_report["errors"].append({
                "step": "Error rate calculation",
                "error": str(e)
            })
            return {"value": 0, "status": "error"}
    
    def calculate_time_to_adjudication(self) -> Dict[str, Any]:
        """
        Calculate Time to Adjudication Reduction
        Percentage reduction in time taken to adjudicate claims
        """
        logger.info("\n" + "-" * 80)
        logger.info("METRIC 3: Time to Adjudication Reduction")
        logger.info("-" * 80)
        
        try:
            if not self.claims_data:
                return {"value": 0, "status": "insufficient_data"}
            
            # Calculate average time from creation to final status
            processing_times = []
            for claim in self.claims_data:
                if claim.created_at and claim.updated_at:
                    time_diff = (claim.updated_at - claim.created_at).total_seconds()  # Keep as seconds
                    processing_times.append(time_diff)
            
            if not processing_times:
                avg_time = 0
                median_time = 0
            else:
                avg_time = statistics.mean(processing_times)
                median_time = statistics.median(processing_times)
            
            # Calculate baseline from actual data: use median if available, otherwise calculate from overall average
            # METRICS_MANUAL_TIME_MULTIPLIER should be in same units (seconds)
            if median_time > 0:
                baseline_manual_time = median_time * METRICS_MANUAL_TIME_MULTIPLIER
            elif avg_time > 0:
                baseline_manual_time = avg_time * METRICS_MANUAL_TIME_MULTIPLIER
            else:
                baseline_manual_time = 0
            
            # Calculate reduction percentage: if baseline is 0, reduction is 0
            if baseline_manual_time > 0:
                reduction_percentage = max(0, min(100, ((baseline_manual_time - avg_time) / baseline_manual_time) * 100))
            else:
                reduction_percentage = 0
            
            metric = {
                "metric_name": "Time to Adjudication Reduction",
                "definition": "Percentage reduction in time taken to adjudicate claims vs manual processing",
                "value": round(reduction_percentage, 2),
                "unit": "percentage",
                "calculation": {
                    "total_processed": len(self.claims_data),
                    "avg_processing_time_seconds": round(avg_time, 2),
                    "median_processing_time_seconds": round(median_time, 2),
                    "baseline_manual_time_seconds": baseline_manual_time,
                    "formula": f"(({baseline_manual_time} - {round(avg_time, 2)}) / {baseline_manual_time}) * 100"
                },
                "interpretation": "Higher is better - indicates faster claim processing",
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Claims Processed: {len(self.claims_data)}")
            logger.info(f"Average Processing Time: {avg_time:.2f} seconds")
            logger.info(f"Median Processing Time: {median_time:.2f} seconds")
            logger.info(f"Baseline Manual Time: {baseline_manual_time} seconds")
            logger.info(f"✅ Time Reduction: {reduction_percentage:.2f}%")
            
            return metric
            
        except Exception as e:
            logger.error(f"❌ Error calculating time to adjudication: {e}")
            self.metrics_report["errors"].append({
                "step": "Time to adjudication calculation",
                "error": str(e)
            })
            return {"value": 0, "status": "error"}
    
    def calculate_denial_rate(self) -> Dict[str, Any]:
        """
        Calculate Claim Denial Rate
        Proportion of claims denied, indicating accuracy in processing
        """
        logger.info("\n" + "-" * 80)
        logger.info("METRIC 4: Claim Denial Rate")
        logger.info("-" * 80)
        
        try:
            if not self.claims_data:
                return {"value": 0, "status": "insufficient_data"}
            
            denied_claims = [c for c in self.claims_data if c.claim_status == "Denied"]
            denial_rate = (len(denied_claims) / len(self.claims_data)) * 100
            
            # Analyze denial reasons more comprehensively
            denial_reasons = {}
            for claim in denied_claims:
                # Check multiple possible reasons
                reason = None
                if claim.guardrail_summary and claim.guardrail_summary.get("fraud_reason"):
                    reason = claim.guardrail_summary.get("fraud_reason")
                elif claim.error_type and claim.error_type != "None":
                    reason = f"Error: {claim.error_type}"
                else:
                    reason = "No specific reason recorded"
                
                denial_reasons[reason] = denial_reasons.get(reason, 0) + 1
            
            metric = {
                "metric_name": "Claim Denial Rate",
                "definition": "Proportion of claims denied, indicating accuracy in processing",
                "value": round(denial_rate, 2),
                "unit": "percentage",
                "calculation": {
                    "total_claims": len(self.claims_data),
                    "denied_claims": len(denied_claims),
                    "approved_claims": len([c for c in self.claims_data if c.claim_status == "Approved"]),
                    "pending_claims": len([c for c in self.claims_data if c.claim_status == "Pending"]),
                    "formula": f"{len(denied_claims)} / {len(self.claims_data)} * 100"
                },
                "denial_reasons": denial_reasons,
                "interpretation": "Should be in line with industry standards (typically 5-15%)",
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Total Claims: {len(self.claims_data)}")
            logger.info(f"Denied Claims: {len(denied_claims)}")
            logger.info(f"✅ Denial Rate: {denial_rate:.2f}%")
            
            if denied_claims:
                logger.info("Denial Reasons Breakdown:")
                for reason, count in sorted(denial_reasons.items(), key=lambda x: x[1], reverse=True):
                    pct = (count / len(denied_claims)) * 100
                    logger.info(f"  • {reason}: {count} ({pct:.1f}%)")
            
            return metric
            
        except Exception as e:
            logger.error(f"❌ Error calculating denial rate: {e}")
            self.metrics_report["errors"].append({
                "step": "Denial rate calculation",
                "error": str(e)
            })
            return {"value": 0, "status": "error"}
    
    def calculate_compliance_accuracy(self) -> Dict[str, Any]:
        """
        Calculate Compliance Dashboard Accuracy
        Accuracy of compliance dashboards in reflecting processed claims data
        """
        logger.info("\n" + "-" * 80)
        logger.info("METRIC 5: Compliance Dashboard Accuracy")
        logger.info("-" * 80)
        
        try:
            if not self.claims_data or not self.history_data:
                return {
                    "metric_name": "Compliance Dashboard Accuracy",
                    "definition": "Accuracy of compliance dashboards in reflecting processed claims data",
                    "value": 0,
                    "unit": "percentage",
                    "status": "insufficient_data",
                    "note": "Cannot calculate without complete claims and history data"
                }
            
            # Check consistency between claims and history records
            claims_with_history = set([h.claim_id for h in self.history_data])
            total_claims = len(self.claims_data)
            
            # Calculate data consistency
            consistency_rate = (len(claims_with_history) / total_claims) * 100 if total_claims > 0 else 0
            
            # Additional validation: check for orphaned records
            orphaned_history = [h for h in self.history_data if not any(c.claim_id == h.claim_id for c in self.claims_data)]
            
            metric = {
                "metric_name": "Compliance Dashboard Accuracy",
                "definition": "Accuracy of compliance dashboards in reflecting processed claims data",
                "value": round(consistency_rate, 2),
                "unit": "percentage",
                "calculation": {
                    "total_claims": total_claims,
                    "claims_with_history": len(claims_with_history),
                    "orphaned_history_records": len(orphaned_history),
                    "formula": f"{len(claims_with_history)} / {total_claims} * 100"
                },
                "data_integrity": {
                    "status": "valid" if len(orphaned_history) == 0 else "issues_found",
                    "orphaned_records": len(orphaned_history)
                },
                "interpretation": "Higher is better - indicates data consistency and integrity",
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Total Claims: {total_claims}")
            logger.info(f"Claims with History: {len(claims_with_history)}")
            logger.info(f"Orphaned History Records: {len(orphaned_history)}")
            logger.info(f"✅ Compliance Accuracy: {consistency_rate:.2f}%")
            
            return metric
            
        except Exception as e:
            logger.error(f"❌ Error calculating compliance accuracy: {e}")
            self.metrics_report["errors"].append({
                "step": "Compliance accuracy calculation",
                "error": str(e)
            })
            return {"value": 0, "status": "error"}
    
    def calculate_integration_accuracy(self) -> Dict[str, Any]:
        """
        Calculate Integration Accuracy
        Degree of correctness in data integration with existing systems
        Includes both structural integrity and data quality checks
        """
        logger.info("\n" + "-" * 80)
        logger.info("METRIC 6: Integration Accuracy")
        logger.info("-" * 80)
        
        try:
            if not self.claims_data:
                return {"value": 0, "status": "insufficient_data"}
            
            # Define valid claim statuses
            valid_statuses = ["Approved", "Denied", "Pending", "Withdrawn", "Appeal", "Under Review"]
            
            # COMPREHENSIVE validation rules - structural + data quality
            validation_rules = {
                # ✅ Structural Validation (Core Fields)
                "has_claim_id": lambda c: bool(c.claim_id),
                "has_customer_id": lambda c: bool(c.customer_id),
                "has_policy_id": lambda c: bool(c.policy_id),
                "has_claim_amount": lambda c: c.claim_amount is not None and c.claim_amount > 0,
                "has_valid_claim_status": lambda c: c.claim_status in valid_statuses,
                "has_timestamps": lambda c: c.created_at is not None and c.updated_at is not None,
                
                # ✅ Data Quality Validation (AI Processing)
                "has_ai_reasoning": lambda c: bool(c.ai_reasoning and str(c.ai_reasoning).strip()),
                "has_error_type": lambda c: c.error_type is not None,
                "has_guardrail_summary": lambda c: (
                    c.guardrail_summary and 
                    isinstance(c.guardrail_summary, dict) and 
                    len(c.guardrail_summary) > 0
                ),
                "has_claim_name": lambda c: bool(c.claim_name and str(c.claim_name).strip()),
                
                # ✅ Consistency Validation
                "claim_amount_positive": lambda c: c.claim_amount is not None and c.claim_amount > 0,
                "approved_amount_valid": lambda c: (
                    c.approved_amount is not None and 
                    0 <= c.approved_amount <= (c.claim_amount or 0)
                ),
                "timestamps_ordered": lambda c: c.created_at <= c.updated_at if c.created_at and c.updated_at else True,
            }
            
            validation_results = {}
            for rule_name, rule_func in validation_rules.items():
                try:
                    valid_count = len([c for c in self.claims_data if rule_func(c)])
                    validation_results[rule_name] = {
                        "valid": valid_count,
                        "total": len(self.claims_data),
                        "percentage": (valid_count / len(self.claims_data)) * 100
                    }
                except Exception as e:
                    logger.warning(f"  ⚠️  Error validating {rule_name}: {e}")
                    validation_results[rule_name] = {
                        "valid": 0,
                        "total": len(self.claims_data),
                        "percentage": 0
                    }
            
            # Calculate overall integration accuracy
            avg_accuracy = statistics.mean([v["percentage"] for v in validation_results.values()])
            
            # Count structural vs quality issues
            structural_rules = [k for k in validation_results.keys() if k in [
                "has_claim_id", "has_customer_id", "has_policy_id", 
                "has_claim_amount", "has_valid_claim_status", "has_timestamps"
            ]]
            quality_rules = [k for k in validation_results.keys() if k not in structural_rules]
            
            structural_accuracy = statistics.mean([
                validation_results[k]["percentage"] for k in structural_rules
            ])
            quality_accuracy = statistics.mean([
                validation_results[k]["percentage"] for k in quality_rules
            ])
            
            metric = {
                "metric_name": "Integration Accuracy",
                "definition": "Degree of correctness in data integration with existing systems",
                "value": round(avg_accuracy, 2),
                "unit": "percentage",
                "calculation": {
                    "total_claims_validated": len(self.claims_data),
                    "validation_rules": len(validation_rules),
                    "structural_accuracy": round(structural_accuracy, 2),
                    "data_quality_accuracy": round(quality_accuracy, 2),
                    "formula": "Average of all field validation percentages"
                },
                "field_validation": validation_results,
                "interpretation": "Higher is better - indicates better data quality and integration",
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Total Claims Validated: {len(self.claims_data)}")
            logger.info(f"Structural Accuracy: {structural_accuracy:.2f}% (core fields)")
            logger.info(f"Data Quality Accuracy: {quality_accuracy:.2f}% (AI processing)")
            logger.info("Field Validation Results:")
            for rule_name, result in validation_results.items():
                status = "✅" if result["percentage"] == 100 else "⚠️ " if result["percentage"] >= 50 else "❌"
                logger.info(f"  {status} {rule_name}: {result['percentage']:.2f}% ({result['valid']}/{result['total']})")
            logger.info(f"✅ Overall Integration Accuracy: {avg_accuracy:.2f}%")
            
            return metric
            
        except Exception as e:
            logger.error(f"❌ Error calculating integration accuracy: {e}")
            self.metrics_report["errors"].append({
                "step": "Integration accuracy calculation",
                "error": str(e)
            })
            return {"value": 0, "status": "error"}
    
    def calculate_processing_latency(self) -> Dict[str, Any]:
        """
        Calculate Processing Latency
        Time taken to process claims showing system efficiency
        """
        logger.info("\n" + "-" * 80)
        logger.info("METRIC 7: Processing Latency")
        logger.info("-" * 80)
        
        try:
            if not self.claims_data:
                return {"value": 0, "status": "insufficient_data"}
            
            # Calculate latency for different claim statuses
            latency_by_status = {}
            overall_latencies = []
            
            for status in ["Approved", "Denied", "Pending"]:
                status_claims = [c for c in self.claims_data if c.claim_status == status]
                if status_claims:
                    latencies = []
                    for claim in status_claims:
                        if claim.created_at and claim.updated_at:
                            latency = (claim.updated_at - claim.created_at).total_seconds()  # Already in seconds
                            latencies.append(latency)
                            overall_latencies.append(latency)
                    
                    if latencies:
                        latency_by_status[status] = {
                            "count": len(status_claims),
                            "avg_latency_seconds": round(statistics.mean(latencies), 2),
                            "median_latency_seconds": round(statistics.median(latencies), 2),
                            "min_latency_seconds": round(min(latencies), 2),
                            "max_latency_seconds": round(max(latencies), 2)
                        }
            
            # Overall latency - safely handle empty data
            overall_avg = statistics.mean(overall_latencies) if overall_latencies else 0
            overall_median = statistics.median(overall_latencies) if overall_latencies else 0
            overall_min = min(overall_latencies) if overall_latencies else 0
            overall_max = max(overall_latencies) if overall_latencies else 0
            
            metric = {
                "metric_name": "Processing Latency",
                "definition": "Time taken to process claims showing system efficiency",
                "value": round(overall_avg, 2),
                "unit": "seconds",
                "calculation": {
                    "total_claims_analyzed": len(self.claims_data),
                    "claims_with_timing_data": len(overall_latencies),
                    "formula": "Average of (updated_at - created_at) for all claims"
                },
                "overall_statistics": {
                    "avg_latency_seconds": round(overall_avg, 2),
                    "median_latency_seconds": round(overall_median, 2),
                    "min_latency_seconds": round(overall_min, 2),
                    "max_latency_seconds": round(overall_max, 2)
                },
                "latency_by_status": latency_by_status,
                "interpretation": "Lower is better - indicates faster claim processing",
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Total Claims Analyzed: {len(self.claims_data)}")
            logger.info(f"Average Processing Latency: {overall_avg:.2f} seconds")
            logger.info(f"Median Processing Latency: {overall_median:.2f} seconds")
            logger.info("Latency by Status:")
            for status, stats in latency_by_status.items():
                logger.info(f"  - {status}: Avg {stats['avg_latency_seconds']}s, Median {stats['median_latency_seconds']}s")
            logger.info(f"✅ Processing Latency: {overall_avg:.2f} seconds")
            
            return metric
            
        except Exception as e:
            logger.error(f"❌ Error calculating processing latency: {e}")
            self.metrics_report["errors"].append({
                "step": "Processing latency calculation",
                "error": str(e)
            })
            return {"value": 0, "status": "error"}
    
    def calculate_security_threats(self) -> Dict[str, Any]:
        """
        Calculate Security Threats Detection
        Analyzes prompt injection, data manipulation, and other security threats
        """
        logger.info("\n" + "-" * 80)
        logger.info("METRIC 8: Security Threats Detection")
        logger.info("-" * 80)
        
        try:
            if not self.claims_data:
                return {"value": 0, "status": "insufficient_data"}
            
            # Extract security threat data from guardrail_summary
            prompt_injection_attempts = 0
            processing_manipulation = 0
            data_access_violation = 0
            integration_abuse = 0
            blocked_threats = 0
            
            threat_patterns = []
            
            for claim in self.claims_data:
                guardrail_summary = claim.guardrail_summary if hasattr(claim, 'guardrail_summary') else {}
                
                if not isinstance(guardrail_summary, dict):
                    continue
                
                # Check for prompt injection
                if claim.error_type == "Prompt Injection":
                    prompt_injection_attempts += 1
                    threat_patterns.append("Prompt Injection Attempt")
                    blocked_threats += 1
                
                # Check fraud detection (potential manipulation)
                if guardrail_summary.get("fraud_status") == "Fraud":
                    if "manipulation" in str(guardrail_summary.get("fraud_reason", "")).lower():
                        processing_manipulation += 1
                    if "unauthorized" in str(guardrail_summary.get("fraud_reason", "")).lower():
                        data_access_violation += 1
                    if "integration" in str(guardrail_summary.get("fraud_reason", "")).lower():
                        integration_abuse += 1
                    
                    # If hitl_flag is set due to security, count as blocked
                    if guardrail_summary.get("hitl_flag"):
                        blocked_threats += 1
            
            # Count threat patterns
            pattern_counter = Counter(threat_patterns)
            
            # Calculate detection rate
            total_detected = (prompt_injection_attempts + processing_manipulation + 
                            data_access_violation + integration_abuse)
            
            # Block rate = successful blocks / total detected
            block_rate = (blocked_threats / total_detected * 100) if total_detected > 0 else 100
            
            # Determine risk level based on detections
            if prompt_injection_attempts > 0:
                risk_level = "high"
            elif total_detected > 5:
                risk_level = "medium"
            else:
                risk_level = "low"
            
            metric = {
                "metric_name": "Security Threats Detection",
                "definition": "Detection and blocking of security threats including prompt injection and data manipulation",
                "value": block_rate,
                "unit": "percentage",
                "calculation": {
                    "total_claims_analyzed": len(self.claims_data),
                    "total_threats_detected": total_detected,
                    "threats_blocked": blocked_threats,
                    "formula": f"{blocked_threats} / {total_detected} * 100 if total_detected > 0 else 100"
                },
                "threat_breakdown": {
                    "prompt_injection_attempts": prompt_injection_attempts,
                    "processing_manipulation": processing_manipulation,
                    "data_access_violations": data_access_violation,
                    "integration_abuse": integration_abuse
                },
                "overall_risk_level": risk_level,
                "interpretation": "Higher is better - indicates effective threat blocking",
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Total Claims Analyzed: {len(self.claims_data)}")
            logger.info(f"Total Threats Detected: {total_detected}")
            logger.info(f"Threats Blocked: {blocked_threats}")
            logger.info(f"Block Rate: {block_rate:.2f}%")
            logger.info(f"Risk Level: {risk_level.upper()}")
            logger.info("Threat Breakdown:")
            logger.info(f"  - Prompt Injection: {prompt_injection_attempts}")
            logger.info(f"  - Processing Manipulation: {processing_manipulation}")
            logger.info(f"  - Data Access Violations: {data_access_violation}")
            logger.info(f"  - Integration Abuse: {integration_abuse}")
            logger.info(f"✅ Security Threats: {block_rate:.2f}% blocked")
            
            return metric
            
        except Exception as e:
            logger.error(f"❌ Error calculating security threats: {e}")
            self.metrics_report["errors"].append({
                "step": "Security threats calculation",
                "error": str(e)
            })
            return {"value": 0, "status": "error"}
    
    def build_threat_detection_chart_data(self) -> List[Dict[str, Any]]:
        """
        Build threat detection chart data for frontend visualization
        Returns data matching: chartData.threatDetection format
        """
        try:
            threat_types = {
                "Processing Manipulation": {"detected": 0, "blocked": 0},
                "Data Access Violation": {"detected": 0, "blocked": 0},
                "Integration Abuse": {"detected": 0, "blocked": 0},
                "Prompt Injection": {"detected": 0, "blocked": 0}
            }
            
            for claim in self.claims_data:
                guardrail_summary = claim.guardrail_summary if hasattr(claim, 'guardrail_summary') else {}
                
                if not isinstance(guardrail_summary, dict):
                    continue
                
                # Prompt Injection
                if claim.error_type == "Prompt Injection":
                    threat_types["Prompt Injection"]["detected"] += 1
                    if guardrail_summary.get("hitl_flag"):
                        threat_types["Prompt Injection"]["blocked"] += 1
                
                # Fraud-based threats
                if guardrail_summary.get("fraud_status") == "Fraud":
                    reason = str(guardrail_summary.get("fraud_reason", "")).lower()
                    
                    if "manipulation" in reason:
                        threat_types["Processing Manipulation"]["detected"] += 1
                        if guardrail_summary.get("hitl_flag"):
                            threat_types["Processing Manipulation"]["blocked"] += 1
                    
                    if "unauthorized" in reason or "access" in reason:
                        threat_types["Data Access Violation"]["detected"] += 1
                        if guardrail_summary.get("hitl_flag"):
                            threat_types["Data Access Violation"]["blocked"] += 1
                    
                    if "integration" in reason:
                        threat_types["Integration Abuse"]["detected"] += 1
                        if guardrail_summary.get("hitl_flag"):
                            threat_types["Integration Abuse"]["blocked"] += 1
            
            # Convert to list format
            chart_data = [
                {
                    "type": threat_type,
                    "detected": data["detected"],
                    "blocked": data["blocked"]
                }
                for threat_type, data in threat_types.items()
            ]
            
            return chart_data
            
        except Exception as e:
            logger.error(f"Error building threat detection chart data: {e}")
            return []
    
    def build_prompt_injection_data(self) -> Dict[str, Any]:
        """
        Build prompt injection threat data for frontend visualization
        Returns data matching: securityThreats.promptInjection format
        """
        try:
            prompt_injection_claims = [
                c for c in self.claims_data 
                if c.error_type == "Prompt Injection"
            ]
            
            blocked_count = sum(
                1 for c in prompt_injection_claims 
                if (c.guardrail_summary or {}).get("hitl_flag")
            )
            
            detected_count = len(prompt_injection_claims)
            
            # Calculate success rate (attempts that weren't blocked)
            success_rate = (
                ((detected_count - blocked_count) / detected_count * 100)
                if detected_count > 0 
                else 0
            )
            
            # Determine risk level
            risk_level = "high" if detected_count > 0 else "low"
            
            # Extract common patterns
            common_patterns = [
                "Claims data manipulation attempts",
                "Processing rule override injection",
                "Fraudulent approval requests",
                "Security guardrail bypasses"
            ]
            
            return {
                "detectedAttempts": detected_count,
                "blockedAttempts": blocked_count,
                "successRate": round(success_rate, 2),
                "riskLevel": risk_level,
                "commonPatterns": common_patterns
            }
            
        except Exception as e:
            logger.error(f"Error building prompt injection data: {e}")
            return {
                "detectedAttempts": 0,
                "blockedAttempts": 0,
                "successRate": 0,
                "riskLevel": "unknown",
                "commonPatterns": []
            }
    
    def generate_kpi_summary(self) -> Dict[str, Any]:
        """Generate overall KPI summary and recommendations"""
        logger.info("\n" + "=" * 80)
        logger.info("KPI SUMMARY")
        logger.info("=" * 80)
        
        metrics = self.metrics_report["calculated_metrics"]
        
        summary = {
            "report_generated": datetime.now().isoformat(),
            "total_metrics_calculated": len(metrics),
            "overall_health_score": self._calculate_health_score(),
            "metrics_overview": {},
            "recommendations": self._generate_recommendations()
        }
        
        # Add overview for each metric
        for metric_name, metric_data in metrics.items():
            if "value" in metric_data and "unit" in metric_data:
                summary["metrics_overview"][metric_name] = {
                    "value": metric_data["value"],
                    "unit": metric_data["unit"],
                    "interpretation": metric_data.get("interpretation", "N/A")
                }
        
        return summary
    
    def _calculate_health_score(self) -> float:
        """Calculate overall system health score using configured weights"""
        metrics = self.metrics_report["calculated_metrics"]
        
        total_score = 0
        total_weight = 0
        
        for metric_name, weight in METRICS_WEIGHTS.items():
            if metric_name in metrics and "value" in metrics[metric_name]:
                value = metrics[metric_name]["value"]
                
                # Invert percentage-based metrics where lower is better
                if metric_name in ["error_rate_on_approved_claims", "claim_denial_rate"]:
                    normalized_value = max(0, 100 - value)  # Invert so higher is better
                # For latency: normalize against a reasonable threshold (e.g., 300 seconds)
                elif metric_name == "processing_latency":
                    latency_threshold = METRICS_THRESHOLDS.get("latency_threshold_high", 300)
                    # Convert latency to a 0-100 score: lower latency = higher score
                    normalized_value = max(0, 100 - min(100, (value / latency_threshold) * 100))
                else:
                    # For percentage metrics that are already 0-100
                    normalized_value = min(100, max(0, value))
                
                total_score += normalized_value * weight
                total_weight += weight
        
        health_score = total_score / total_weight if total_weight > 0 else 0
        return round(health_score, 2)
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on metrics and configured thresholds"""
        recommendations = []
        metrics = self.metrics_report["calculated_metrics"]
        
        # Get thresholds from configuration
        str_threshold = METRICS_THRESHOLDS["str_threshold"]
        str_excellent = METRICS_THRESHOLDS["str_excellent"]
        error_threshold = METRICS_THRESHOLDS["error_threshold"]
        denial_threshold_high = METRICS_THRESHOLDS["denial_threshold_high"]
        denial_threshold_low = METRICS_THRESHOLDS["denial_threshold_low"]
        latency_threshold_high = METRICS_THRESHOLDS["latency_threshold_high"]
        latency_threshold_low = METRICS_THRESHOLDS["latency_threshold_low"]
        
        # Check STR
        if "straight_through_rate" in metrics:
            str_value = metrics["straight_through_rate"].get("value", 0)
            if str_value < str_threshold:
                recommendations.append(f"⚠️  STR below {str_threshold}%: Review HITL cases to reduce manual intervention")
            elif str_value >= str_excellent:
                recommendations.append(f"✅ Excellent STR: System requires minimal manual intervention")
        
        # Check error rate
        if "error_rate_on_approved_claims" in metrics:
            error_rate = metrics["error_rate_on_approved_claims"].get("value", 0)
            if error_rate > error_threshold:
                recommendations.append(f"⚠️  High error rate on approved claims (>{error_threshold}%): Implement additional validation rules")
            elif error_rate == 0:
                recommendations.append("✅ Zero errors on approved claims: Processing quality is excellent")
        
        # Check denial rate
        if "claim_denial_rate" in metrics:
            denial_rate = metrics["claim_denial_rate"].get("value", 0)
            if denial_rate > denial_threshold_high:
                recommendations.append(f"⚠️  High denial rate (>{denial_threshold_high}%): Review denial reasons and adjust criteria")
            elif denial_rate < denial_threshold_low:
                recommendations.append("✅ Low denial rate: Claims are passing validation well")
        
        # Check latency
        if "processing_latency" in metrics:
            latency = metrics["processing_latency"].get("value", 0)
            if latency > latency_threshold_high:
                recommendations.append(f"⚠️  High processing latency (>{latency_threshold_high}s): Optimize processing pipeline")
            elif latency < latency_threshold_low:
                recommendations.append("✅ Excellent processing speed: System is highly efficient")
        
        if not recommendations:
            recommendations.append("✅ All metrics are within acceptable ranges")
        
        return recommendations
    
    def run_validation(self) -> bool:
        """Run complete metrics validation"""
        logger.info("\n")
        logger.info("╔" + "=" * 78 + "╗")
        logger.info("║" + " " * 20 + "METRICS VALIDATION SCRIPT" + " " * 34 + "║")
        logger.info("╚" + "=" * 78 + "╝")
        
        # Step 1: Initialize database
        if not self.initialize_database():
            logger.error("❌ Failed to initialize database. Cannot continue.")
            return False
        
        # Step 2: Fetch raw data
        if not self.fetch_raw_data():
            logger.warning("⚠️  No claims data found. Results may be incomplete.")
        
        # Step 3: Calculate all metrics
        logger.info("\n" + "=" * 80)
        logger.info("CALCULATING METRICS")
        logger.info("=" * 80)
        
        self.metrics_report["calculated_metrics"]["straight_through_rate"] = self.calculate_straight_through_rate()
        self.metrics_report["calculated_metrics"]["error_rate_on_approved_claims"] = self.calculate_error_rate_on_approved()
        self.metrics_report["calculated_metrics"]["time_to_adjudication_reduction"] = self.calculate_time_to_adjudication()
        self.metrics_report["calculated_metrics"]["claim_denial_rate"] = self.calculate_denial_rate()
        self.metrics_report["calculated_metrics"]["compliance_dashboard_accuracy"] = self.calculate_compliance_accuracy()
        self.metrics_report["calculated_metrics"]["integration_accuracy"] = self.calculate_integration_accuracy()
        self.metrics_report["calculated_metrics"]["processing_latency"] = self.calculate_processing_latency()
        self.metrics_report["calculated_metrics"]["security_threats"] = self.calculate_security_threats()
        
        # Step 4: Generate KPI summary
        self.metrics_report["kpi_summary"] = self.generate_kpi_summary()
        
        # Step 5: Save results
        self.save_results()
        
        return True
    
    def _build_standardized_output(self) -> Dict[str, Any]:
        """Build standardized JSON output with real data only"""
        metrics = self.metrics_report["calculated_metrics"]
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Calculate manual vs automated
        hitl_claim_ids = set([h.claim_id for h in self.hitl_data]) if self.hitl_data else set()
        manual_count = len([c for c in self.claims_data if c.claim_id in hitl_claim_ids])
        automated_count = len(self.claims_data) - manual_count
        error_count = len([c for c in self.claims_data if c.error_type and c.error_type.strip()])
        
        # Extract current metric values
        standardized_output = {
            "modelInfo": {
                "name": METRICS_MODEL_NAME,
                "version": METRICS_MODEL_VERSION
            },
            "metrics": {
                "claimsProcessingStraightThroughRate": metrics.get("straight_through_rate", {}).get("value", 0),
                "errorRateOnApprovedClaims": metrics.get("error_rate_on_approved_claims", {}).get("value", 0),
                "timeToAdjudicationReduction": metrics.get("time_to_adjudication_reduction", {}).get("value", 0),
                "claimDenialRate": metrics.get("claim_denial_rate", {}).get("value", 0),
                "complianceDashboardAccuracy": metrics.get("compliance_dashboard_accuracy", {}).get("value", 0),
                "integrationAccuracy": metrics.get("integration_accuracy", {}).get("value", 0),
                "processingLatency": metrics.get("processing_latency", {}).get("value", 0)
            },
            "securityThreats": {
                "promptInjection": self.build_prompt_injection_data()
            },
            "percentageMetricsCharts": [
                {
                    "date": today,
                    "claimsProcessingStraightThroughRate": metrics.get("straight_through_rate", {}).get("value", 0),
                    "errorRateOnApprovedClaims": metrics.get("error_rate_on_approved_claims", {}).get("value", 0),
                    "timeToAdjudicationReduction": metrics.get("time_to_adjudication_reduction", {}).get("value", 0)
                }
            ],
            "secondsMetricsCharts": [
                {
                    "date": today,
                    "processingLatency": metrics.get("processing_latency", {}).get("value", 0)
                }
            ],
            "chartData": {
                "threatDetection": self.build_threat_detection_chart_data(),
                "metricsOverTime": [
                    {
                        "date": today,
                        "manual": manual_count,
                        "automated": automated_count,
                        "errors": error_count
                    }
                ]
            },
            "versionHistory": [
                {
                    "version": METRICS_MODEL_VERSION,
                    "date": today,
                    "status": METRICS_STATUS,
                    "changes": "Real metrics validation with guardrail and AI reasoning analysis"
                }
            ]
        }
        
        return standardized_output
    
    def save_results(self):
        """Save metrics report to JSON file"""
        logger.info("\n" + "=" * 80)
        logger.info("SAVING RESULTS")
        logger.info("=" * 80)
        
        output_path = os.path.join(
            os.path.dirname(__file__),
            f"metrics_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        try:
            # Generate standardized output
            standardized_output = self._build_standardized_output()
            
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(standardized_output, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"✅ Results saved to: {output_path}")
            
            # Print summary to console
            print("\n" + "=" * 80)
            print("METRICS VALIDATION REPORT SUMMARY")
            print("=" * 80)
            print(f"📄 Output File: {output_path}")
            print(f"⏰ Generated: {datetime.now().isoformat()}")
            print(f"🤖 Model: {standardized_output['modelInfo']['name']} v{standardized_output['modelInfo']['version']}")
            print("\n📊 Current Metrics:")
            print(f"  • Claims Processing STR: {standardized_output['metrics']['claimsProcessingStraightThroughRate']}%")
            print(f"  • Error Rate on Approved: {standardized_output['metrics']['errorRateOnApprovedClaims']}%")
            print(f"  • Time to Adjudication Reduction: {standardized_output['metrics']['timeToAdjudicationReduction']}%")
            print(f"  • Claim Denial Rate: {standardized_output['metrics']['claimDenialRate']}%")
            print(f"  • Compliance Dashboard Accuracy: {standardized_output['metrics']['complianceDashboardAccuracy']}%")
            print(f"  • Integration Accuracy: {standardized_output['metrics']['integrationAccuracy']}%")
            print(f"  • Processing Latency: {standardized_output['metrics']['processingLatency']}s")
            
            print("\n📈 Processing Summary:")
            chart_data = standardized_output['chartData']['metricsOverTime'][0]
            print(f"  • Manual Interventions: {chart_data['manual']}")
            print(f"  • Automated Claims: {chart_data['automated']}")
            print(f"  • Claims with Errors: {chart_data['errors']}")
            
            print("\n" + "=" * 80)
            
        except Exception as e:
            logger.error(f"❌ Error saving results: {e}")
            self.metrics_report["errors"].append({
                "step": "Saving results",
                "error": str(e)
            })


def main():
    """Main entry point"""
    try:
        validator = MetricsValidator()
        success = validator.run_validation()
        
        if not success:
            logger.error("❌ Metrics validation failed")
            sys.exit(1)
        else:
            logger.info("✅ Metrics validation completed successfully")
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
