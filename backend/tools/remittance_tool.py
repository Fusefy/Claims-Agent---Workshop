# backend/tools/remittance_tool.py
"""
Remittance Tool for Claim Approval and Amount Determination using LLM
"""
import google.generativeai as genai
import logging
import json
from database.claim_repository import claim_repository
from utils.config import GEMINI_API_KEY, DEFAULT_MODEL

logger = logging.getLogger(__name__)

# Initialize Gemini
genai.configure(api_key=GEMINI_API_KEY)

REMITTANCE_PROMPT = """
You are a healthcare claims adjudication specialist responsible for determining approved claim amounts based on policy coverage, network status, and medical necessity.

**Task:** Analyze the claim details and determine the approved amount with clear reasoning.

**Claim Details:**
```json
{claim_data}
```

**Adjudication Guidelines:**

1. **Network Status Rules:**
   - In-Network: Typically 80-100% of claim amount (higher coverage)
   - Out-of-Network: Typically 50-70% of claim amount (lower coverage)
   - Unknown: Default to 60-80% with caution

2. **Claim Type Considerations:**
   - Medical: Check for reasonable and customary charges
   - Dental: Review procedure codes and coverage limits
   - Vision: Verify coverage for exams, frames, lenses
   - Pharmacy: Check formulary status and copay tiers

3. **Amount Validation:**
   - Compare against typical costs for similar procedures
   - Flag unusually high or low amounts
   - Consider date of service and policy coverage period

4. **Approval Logic:**
   - Full approval: When all criteria met, amount reasonable
   - Partial approval: When amount exceeds usual and customary rates
   - Coverage limitations apply based on policy terms

**Output Format:** Return ONLY a valid JSON object (no markdown, no code blocks):

{{
  "approved_amount": numeric value (float),
  "approval_percentage": numeric value (0-100),
  "ai_reasoning": "Clear explanation for the approved amount (max 150 chars)",
  "coverage_details": {{
    "network_adjustment": "explanation of network-based adjustment",
    "policy_coverage": "coverage percentage based on policy type",
    "amount_justification": "why this amount was approved"
  }}
}}

**Examples:**

In-Network Medical Claim $5,000:
{{
  "approved_amount": 4500.00,
  "approval_percentage": 90,
  "ai_reasoning": "In-network medical service: 90% coverage applied per policy terms",
  "coverage_details": {{
    "network_adjustment": "In-network discount applied",
    "policy_coverage": "Standard 90% coverage for in-network medical",
    "amount_justification": "Amount reasonable for procedure code"
  }}
}}

Out-of-Network Dental Claim $2,000:
{{
  "approved_amount": 1200.00,
  "approval_percentage": 60,
  "ai_reasoning": "Out-of-network dental: 60% coverage with usual and customary limits",
  "coverage_details": {{
    "network_adjustment": "Out-of-network penalty applied",
    "policy_coverage": "60% coverage for out-of-network dental",
    "amount_justification": "Amount adjusted to usual and customary rates"
  }}
}}

**Important:**
- Be fair but conservative in approvals
- Always provide clear reasoning
- Consider network status as primary factor
- Approved amount should NEVER exceed claim amount
- Keep ai_reasoning concise (under 150 characters)
"""


class RemittanceAnalyzer:
    """Singleton Gemini client for remittance analysis"""
    _instance = None
    _model = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_model(self):
        """Get or create Gemini model"""
        if self._model is None:
            self._model = genai.GenerativeModel(
                model_name=DEFAULT_MODEL,
                generation_config={
                    "temperature": 0.2,  # Low for consistent adjudication
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 1024,
                }
            )
            logger.info(f"[Remittance] Gemini model initialized: {DEFAULT_MODEL}")
        return self._model


remittance_analyzer = RemittanceAnalyzer()


def process_remittance(claim_id: str) -> dict:
    """
    Process claim remittance - determine approved amount and return approval details.
    
    Args:
        claim_id: The unique claim identifier to process
    
    Returns:
        Dictionary containing approval details including approved_amount and ai_reasoning
    """
    try:
        logger.info(f"[Remittance] Processing claim: {claim_id}")
        
        # Step 1: Query claim from database
        claim = claim_repository.get_by_id(claim_id, id_column="claim_id")
        
        if not claim:
            raise ValueError(f"Claim not found: {claim_id}")
        
        # Validate claim is eligible for remittance
        if claim.claim_status not in ["Pending"]:
            logger.warning(f"[Remittance] Claim {claim_id} status is '{claim.claim_status}', not 'Pending'")
            return {
                "success": False,
                "error": f"Claim status is '{claim.claim_status}', cannot process remittance"
            }
        
        # Convert claim to dict for LLM
        claim_data = {
            "claim_id": claim.claim_id,
            "claim_name": claim.claim_name,
            "customer_id": claim.customer_id,
            "policy_id": claim.policy_id,
            "claim_type": claim.claim_type,
            "network_status": claim.network_status,
            "date_of_service": str(claim.date_of_service) if claim.date_of_service else None,
            "claim_amount": float(claim.claim_amount) if claim.claim_amount else 0.0,
            "current_approved_amount": float(claim.approved_amount) if claim.approved_amount else 0.0,
        }
        
        logger.info(f"[Remittance] Analyzing claim: {claim_id}, Amount: ${claim_data['claim_amount']}, Network: {claim_data['network_status']}")
        
        # Step 2: Use LLM to determine approved amount
        model = remittance_analyzer.get_model()
        
        prompt = REMITTANCE_PROMPT.format(
            claim_data=json.dumps(claim_data, indent=2)
        )
        
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        
        result = json.loads(response_text)
        
        approved_amount = result.get("approved_amount", 0.0)
        ai_reasoning = result.get("ai_reasoning", "Claim approved based on policy coverage")
        
        # Validate approved amount doesn't exceed claim amount
        if approved_amount > claim_data["claim_amount"]:
            logger.warning(f"[Remittance] Approved amount ${approved_amount} exceeds claim amount ${claim_data['claim_amount']}, capping")
            approved_amount = claim_data["claim_amount"]
            ai_reasoning = "Full claim amount approved"
        
        logger.info(
            f"[Remittance] ✅ Approval determined - "
            f"Claim: {claim_id}, "
            f"Original: ${claim_data['claim_amount']}, "
            f"Approved: ${approved_amount} ({result.get('approval_percentage', 0)}%)"
        )
        
        # Step 3: Return approval data for sql_tool to update
        return {
            "success": True,
            "claim_id": claim_id,
            "approved_amount": approved_amount,
            "approval_percentage": result.get("approval_percentage", 0),
            "ai_reasoning": ai_reasoning[:150],  # Ensure max 150 chars
            "coverage_details": result.get("coverage_details", {}),
            "original_amount": claim_data["claim_amount"]
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"[Remittance] JSON parsing error: {e}")
        raise Exception(f"Failed to parse LLM response: {str(e)}")
        
    except Exception as e:
        logger.error(f"[Remittance] ❌ Error: {str(e)}", exc_info=True)
        raise Exception(f"Remittance processing failed: {str(e)}")


# Export the function directly
remittance_agent = process_remittance
