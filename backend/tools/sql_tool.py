# backend/tools/sql_tool.py
"""
SQL Tool for database operations using repositories
"""
import logging
import json
from datetime import datetime
from database import claim_repository, hitl_repository, history_repository
from models.proposed_claim import ProposedClaim
from models.hitl_queue import HitlQueue

logger = logging.getLogger(__name__)

# Valid claim status values
VALID_CLAIM_STATUS = ["Approved", "Pending", "Denied"]


def insert_claim(claim_data: str) -> dict:
    """
    Insert claim record into ProposedClaim database table.
    """
    try:
        # Parse JSON string
        if isinstance(claim_data, str):
            claim_data = json.loads(claim_data)
        
        logger.info(f"[SQL] Inserting claim: {claim_data.get('claim_id')}")
        
        # Map patient_id to customer_id (LLM uses patient_id, DB uses customer_id)
        customer_id = claim_data.get("customer_id") or claim_data.get("patient_id")
        
        # Build guardrail_summary with fraud detection data
        guardrail_summary = claim_data.get("guardrail_summary", {})
        guardrail_summary.update({
            "fraud_status": claim_data.get("fraud_status", "No Fraud"),
            "confidence_score": claim_data.get("confidence", 1.0),
            "fraud_reason": claim_data.get("fraud_reason"),
            "hitl_flag": claim_data.get("hitl_flag", False),
            "analyzed_at": datetime.utcnow().isoformat(),
            "analyzer": "gemini-2.0-flash"
        })
        
        # Determine claim status - must be Approved, Pending, or Denied
        claim_status = claim_data.get("claim_status", "Pending")
        if claim_status not in VALID_CLAIM_STATUS:
            logger.warning(f"[SQL] Invalid claim_status '{claim_status}', defaulting to 'Pending'")
            claim_status = "Pending"
        
        # Extract fields from LLM response
        error_type = claim_data.get("error_type")  # ✅ Use LLM's error_type directly
        if error_type == "None":  # Convert string "None" to Python None
            error_type = None
            
        ai_reasoning = claim_data.get("ai_reasoning")
        
        # Build notes from various sources
        notes_parts = []
        if claim_data.get("fraud_reason"):
            notes_parts.append(f"Fraud Analysis: {claim_data.get('fraud_reason')}")
        if claim_data.get("hitl_flag"):
            notes_parts.append("Flagged for human review")
        if claim_data.get("confidence"):
            notes_parts.append(f"Confidence Score: {claim_data.get('confidence')}")
        
        notes = " | ".join(notes_parts) if notes_parts else None
        
        # Create ProposedClaim model
        claim = ProposedClaim(
            claim_id=claim_data["claim_id"],
            claim_name=claim_data.get("claim_name"),
            customer_id=customer_id,
            policy_id=claim_data.get("policy_id"),
            claim_type=claim_data.get("claim_type"),
            network_status=claim_data.get("network_status"),
            date_of_service=claim_data.get("date_of_service"),
            claim_amount=claim_data.get("claim_amount"),
            approved_amount=claim_data.get("approved_amount", 0.0),
            claim_status=claim_status,
            error_type=error_type,  
            ai_reasoning=ai_reasoning,  
            payment_status=claim_data.get("payment_status", "Pending"),
            notes=notes,
            guardrail_summary=guardrail_summary,
        )
        
        # Use repository to insert
        created_claim = claim_repository.create(claim)
        
        # Log to history with AI reasoning
        history_repository.log_status_change(
            claim_id=created_claim.claim_id,
            old_status="New",
            new_status=created_claim.claim_status,
            changed_by="claim_processing_agent",
            role="Agent",
            change_reason=ai_reasoning
        )
        
        logger.info(
            f"[SQL] ✅ Claim inserted: {claim_data['claim_id']} "
            f"with status '{claim_status}', "
            f"error_type: '{error_type}', "
            f"ai_reasoning: {ai_reasoning}"
        )
        return {
            "success": True, 
            "claim_id": claim_data["claim_id"], 
            "status": claim_status,
            "error_type": error_type,
            "ai_reasoning": ai_reasoning
        }
        
    except Exception as e:
        logger.error(f"[SQL] ❌ Error inserting claim: {str(e)}", exc_info=True)
        raise Exception(f"Database insert failed: {str(e)}")


def insert_hitl(hitl_data: str) -> dict:
    """
    Insert record into HITL (Human-In-The-Loop) queue for manual review.
    
    Args:
        hitl_data: JSON string containing HITL queue fields including claim_id, status, and optional assigned_to and decision fields
    
    Returns:
        Dictionary confirming successful creation of HITL record
    """
    try:
        # Parse JSON string
        if isinstance(hitl_data, str):
            hitl_data = json.loads(hitl_data)
        
        logger.info(f"[SQL] Inserting HITL record for: {hitl_data.get('claim_id')}")
        
        # Map reason/hitl_reason to reviewer_comments
        reviewer_comments = (
            hitl_data.get("reviewer_comments") or 
            hitl_data.get("reason") or 
            hitl_data.get("hitl_reason") or
            hitl_data.get("ai_reasoning") or  
            "Flagged for manual review"
        )
        
        # Validate and normalize status
        status = hitl_data.get("status", "Pending")
        if status not in VALID_CLAIM_STATUS:
            logger.warning(f"[SQL] Invalid HITL status '{status}', defaulting to 'Pending'")
            status = "Pending"
        
        # Create HitlQueue model
        hitl = HitlQueue(
            claim_id=hitl_data["claim_id"],
            assigned_to=hitl_data.get("assigned_to"),
            status=status,
            reviewer_comments=reviewer_comments,
            decision=hitl_data.get("decision"),
        )
        
        # Use repository to insert
        created_hitl = hitl_repository.create(hitl)
        
        # Log to history
        history_repository.log_status_change(
            claim_id=hitl_data["claim_id"],
            old_status="Pending",
            new_status="Pending",  # ✅ VALID STATUS (Approved/Pending/Denied only)
            changed_by="claim_processing_agent",
            role="Agent",
            change_reason=f"Flagged for HITL review: {reviewer_comments}"
        )
        
        logger.info(f"[SQL] ✅ HITL record created for: {hitl_data['claim_id']}")
        return {"success": True, "hitl_record_created": True, "status": status}
        
    except Exception as e:
        logger.error(f"[SQL] ❌ Error inserting HITL record: {str(e)}", exc_info=True)
        raise Exception(f"HITL queue insert failed: {str(e)}")


def update_claim_approval(approval_data: str) -> dict:
    """
    Update claim with approved amount and change status to Approved.
    
    Args:
        approval_data: JSON string containing claim_id, approved_amount, and ai_reasoning
    
    Returns:
        Dictionary confirming successful approval update
    """
    try:
        # Parse JSON string
        if isinstance(approval_data, str):
            approval_data = json.loads(approval_data)
        
        claim_id = approval_data["claim_id"]
        approved_amount = approval_data["approved_amount"]
        ai_reasoning = approval_data.get("ai_reasoning", "Claim approved")
        
        logger.info(f"[SQL] Updating claim approval: {claim_id}, Amount: ${approved_amount}")
        
        # Update claim in database
        updated_claim = claim_repository.update(
            claim_id,
            {
                "approved_amount": approved_amount,
                "claim_status": "Approved",
                "payment_status": "Approved",
                "ai_reasoning": ai_reasoning,
                "updated_at": datetime.utcnow()
            },
            id_column="claim_id"
        )
        
        if not updated_claim:
            raise Exception(f"Failed to update claim: {claim_id}")
        
        # Log to history
        history_repository.log_status_change(
            claim_id=claim_id,
            old_status="Pending",
            new_status="Approved",
            changed_by="remittance_agent",
            role="Agent",
            change_reason=f"Approved ${approved_amount}: {ai_reasoning}"
        )
        
        logger.info(f"[SQL] ✅ Claim approved: {claim_id}, Amount: ${approved_amount}")
        return {
            "success": True,
            "claim_id": claim_id,
            "approved_amount": approved_amount,
            "claim_status": "Approved",
            "payment_status": "Approved"
        }
        
    except Exception as e:
        logger.error(f"[SQL] ❌ Error updating approval: {str(e)}", exc_info=True)
        raise Exception(f"Approval update failed: {str(e)}")


# Export the functions directly
insert_claim_tool = insert_claim
HITL_agent = insert_hitl
approval_agent = update_claim_approval
