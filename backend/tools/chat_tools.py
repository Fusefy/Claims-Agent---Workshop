# backend/tools/chat_tools.py
"""
Chat Tools for ClaimWise Agent
Provides tools for fetching claim data and checking for security/fraud issues.
"""
import logging
import re
import json
from database.claim_repository import claim_repository

logger = logging.getLogger(__name__)

from typing import Optional

def fetch_claim_details(claim_id: str, customer_id: Optional[str] = None) -> dict:
    """
    Fetch details for a specific claim from the database.
    
    Args:
        claim_id: The unique claim identifier (e.g., CLM-2024-XXXXXX)
        customer_id: Optional customer ID to verify ownership
        
    Returns:
        Dictionary containing claim details or error message
    """
    try:
        logger.info(f"[ChatTool] Fetching claim: {claim_id}")
        
        # Get claim from repository
        claim = claim_repository.get_by_id(claim_id, id_column="claim_id")
        
        if not claim:
            return {"error": "Claim not found", "found": False}
            
        # Verify ownership if customer_id provided
        # ADMIN BYPASS: Allow customer_id "1" to view all claims
        if customer_id and str(customer_id) != "1" and str(claim.customer_id) != str(customer_id):
            logger.warning(f"[ChatTool] Access denied: Customer {customer_id} tried to access {claim_id} (Owner: {claim.customer_id})")
            return {
                "error": f"Access denied: This claim belongs to user '{claim.customer_id}', but you are logged in as '{customer_id}'.", 
                "found": True
            }
            
        # Return comprehensive claim details
        return {
            "found": True,
            "claim_id": claim.claim_id,
            "claim_name": claim.claim_name,
            "claim_status": claim.claim_status,
            "claim_type": claim.claim_type,
            "policy_id": claim.policy_id,
            "network_status": claim.network_status,
            "approved_amount": float(claim.approved_amount) if claim.approved_amount else 0.0,
            "claim_amount": float(claim.claim_amount) if claim.claim_amount else 0.0,
            "payment_status": claim.payment_status,
            "date_of_service": str(claim.date_of_service) if claim.date_of_service else None,
            "ai_reasoning": claim.ai_reasoning,
            "error_type": claim.error_type,
            "guardrail_summary": claim.guardrail_summary if claim.guardrail_summary else {},
            "created_at": str(claim.created_at) if claim.created_at else None,
            "updated_at": str(claim.updated_at) if claim.updated_at else None
        }
        
    except Exception as e:
        logger.error(f"[ChatTool] Error fetching claim: {e}")
        return {"error": f"System error: {str(e)}", "found": False}


def check_safety(text: str) -> dict:
    """
    Analyze text for prompt injection attempts and fraud patterns.
    
    Args:
        text: The user input text to analyze
        
    Returns:
        Dictionary with safety status and detected issues
    """
    logger.info("[ChatTool] Analyzing text for safety...")
    
    # Prompt injection patterns
    injection_patterns = [
        r"ignore (?:previous|all) instructions",
        r"forget (?:previous|all) instructions",
        r"system prompt",
        r"you are now",
        r"admin mode",
        r"developer mode",
        r"bypass security",
        r"override (?:security|rules)",
        r"delete (?:all|database)",
        r"drop table",
        r"update claim set",
    ]
    
    # Check for matches
    detected_threats = []
    for pattern in injection_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            detected_threats.append(pattern)
            
    if detected_threats:
        logger.warning(f"[ChatTool] 🚨 Safety threat detected: {detected_threats}")
        return {
            "safe": False,
            "threat_level": "HIGH",
            "issues": detected_threats,
            "action": "BLOCK",
            "message": "Security alert: Malicious content detected."
        }
        
    # Check for sensitive data patterns (basic masking check)
    sensitive_patterns = {
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
        "credit_card": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b"
    }
    
    masked_data = []
    for name, pattern in sensitive_patterns.items():
        if re.search(pattern, text):
            masked_data.append(name)
            
    return {
        "safe": True,
        "threat_level": "LOW",
        "issues": [],
        "masked_types": masked_data,
        "action": "ALLOW"
    }

def fetch_user_claims(customer_id: str) -> dict:
    """
    Fetch a summary of claims for a specific user.
    
    Args:
        customer_id: The customer ID to fetch claims for
        
    Returns:
        Dictionary with list of claims
    """
    try:
        logger.info(f"[ChatTool] Fetching claims for customer: {customer_id}")
        
        claims = []
        # ADMIN BYPASS: If user is "1", fetch recent claims from ALL users
        if str(customer_id) == "1":
            logger.info("[ChatTool] Admin user '1' detected - fetching all recent claims")
            # Use search_claims with no filters to get recent ones
            results = claim_repository.search_claims(limit=10)
        else:
            # Normal user - fetch only their claims
            results = claim_repository.get_by_customer(customer_id, limit=10)
            
        if not results:
            return {"found": False, "claims": [], "message": "No claims found."}
            
        # Format results with comprehensive information
        for claim in results:
            claims.append({
                "claim_id": claim.claim_id,
                "claim_name": claim.claim_name,
                "status": claim.claim_status,
                "claim_type": claim.claim_type,
                "network_status": claim.network_status,
                "amount": float(claim.claim_amount) if claim.claim_amount else 0.0,
                "approved_amount": float(claim.approved_amount) if claim.approved_amount else 0.0,
                "payment_status": claim.payment_status,
                "ai_reasoning": claim.ai_reasoning,
                "error_type": claim.error_type,
                "date": str(claim.created_at.date()) if claim.created_at else "Unknown"
            })
            
        return {
            "found": True, 
            "claims": claims, 
            "count": len(claims),
            "message": f"Found {len(claims)} recent claims."
        }
        
    except Exception as e:
        logger.error(f"[ChatTool] Error fetching user claims: {e}")
        return {"error": f"System error: {str(e)}", "found": False}
