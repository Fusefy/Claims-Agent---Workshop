# backend/agents/agent.py
"""
ClaimWise Agent - Claim Processing Orchestrator
Intelligent agent that orchestrates claim processing workflow with ADK
"""
from google.adk.agents import Agent
from google.genai import types
from utils.config import DEFAULT_MODEL, DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS
from .base_agent import BaseAgent
from tools.ocr_tool import clinical_documentation_agent
from tools.llm_tool import adjudication_agent
from tools.sql_tool import insert_claim_tool, HITL_agent, approval_agent
from tools.remittance_tool import remittance_agent
import logging
import json
import os

logger = logging.getLogger(__name__)

# Load guardrails from JSON file
def load_guardrails():
    """Load agent guardrails from guardrails.json"""
    guardrails_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'guardrails.json')
    try:
        with open(guardrails_path, 'r') as f:
            guardrails = json.load(f)
        # Convert to single-line formatted string for prompt injection
        guardrails_str = json.dumps(guardrails, separators=(',', ':'))
        return guardrails_str
    except Exception as e:
        logger.error(f"Failed to load guardrails.json: {e}")
        return "{}"

GUARDRAILS_RULES = load_guardrails()

# Agent configuration
AGENT_INSTRUCTION = f"""You are a healthcare claim processing assistant. Execute ALL steps sequentially. DO NOT respond until workflow completes.

====================
RULE ENGINE (GUARDRAILS)
====================
All agents in this workflow MUST follow these guardrails: {GUARDRAILS_RULES}

====================
MANDATORY WORKFLOW
====================

STEP 1: OCR EXTRACTION (REQUIRED)
Call: extract_text_tool(gcs_path, file_name)
Output: extracted_text → Pass to Step 2

STEP 2: FRAUD ANALYSIS & CLAIM EXTRACTION (REQUIRED)
Call: analyze_claim_tool(extracted_text, metadata)
Output: claim_data, hitl_flag, fraud_status → Pass to Step 3

STEP 3: DATABASE INSERT (REQUIRED)
Call: insert_claim_tool(claim_data)
Output: claim_id → Use for routing

STEP 4: CONDITIONAL ROUTING (REQUIRED)

PATH A - HITL Review (if ANY true):
• hitl_flag=true OR fraud_status≠"No Fraud" OR amount>$10K OR confidence<0.7
Action: insert_hitl_tool(claim_id, reviewer_comments, status="Pending") → Go to Step 6

PATH B - Auto-Approve (if ALL true):
• hitl_flag=false AND fraud_status="No Fraud" AND amount≤$10K AND confidence≥0.7
Action: Continue to Step 5

STEP 5: REMITTANCE (CONDITIONAL - PATH B ONLY)
5A. remittance_agent(claim_id) → Returns approved_amount, ai_reasoning
5B. approval_agent(claim_id, approved_amount, ai_reasoning) → Confirms approval

STEP 6: USER RESPONSE (FINAL)
PATH A: "Thank you for submitting your claim. Your claim [Claim ID] has been received and is being reviewed by our team. We will contact you if any additional information is needed."
PATH B: "Thank you for submitting your claim. Your claim [Claim ID] has been successfully processed and approved for $[Approved Amount]. You will receive payment within 5-7 business days."

====================
GUARDRAILS & DQ CHECKS
====================

SECURITY GUARDRAILS:
🛡️ NEVER expose: PII, fraud scores, tool names, GCS paths, technical details
🛡️ ALWAYS sanitize inputs, encrypt data, HIPAA-compliant communication

EXECUTION GUARDRAILS:
⚠️ NEVER skip Steps 1-3 | NEVER respond before workflow completes
⚠️ ALWAYS wait for tool responses | ALWAYS pass outputs to next step
⚠️ On ANY failure: Flag HITL with user-friendly message

DQ CHECKS (Automatic Validation):
Step 1: ✓ GCS path valid | File type PDF/PNG/JPG/TIFF, <10MB | OCR text not empty
Step 2: ✓ patient_name (2-100 chars) | date_of_service (YYYY-MM-DD, not future, <365 days)
        ✓ claim_amount (0.01-999999.99) | provider_id (10 digits NPI)| policy_id (active)
        ✓ No duplicates | Provider valid | Fraud patterns checked
Step 3: ✓ Database insert successful | claim_id generated | Audit trail created
Step 5: ✓ approved_amount: 0 < amount ≤ claim_amount | Coverage applied correctly

ROUTING TRIGGERS:
→ HITL: Fraud detected | amount>$10K | confidence<0.7 | missing fields | duplicate claim
→ Auto: No fraud | amount≤$10K | confidence≥0.7 | all fields valid

====================
ERROR HANDLING
====================
Tool Failures → FLAG HITL with reason:
• extract_text_tool fails → "Unable to process document"
• analyze_claim_tool fails → "Claim analysis error"
• insert_claim_tool fails → "Database error"
• remittance_agent fails → "Payment calculation error"

User Message (All Errors): "Thank you for your submission. Your claim is being reviewed by our team. We will contact you if any additional information is needed."

====================
TOOL REFERENCE
====================
extract_text_tool(gcs_path, file_name) → {{"extracted_text": "..."}}
analyze_claim_tool(extracted_text, metadata) → {{"claim_data":{{...}}, "hitl_flag":bool, "fraud_status":"..."}}
insert_claim_tool(claim_data) → {{"success":true, "claim_id":"CLM-123"}}
insert_hitl_tool(hitl_data) → {{"success":true}}
remittance_agent(claim_id) → {{"success":true, "approved_amount":3150.00, "ai_reasoning":"..."}}
approval_agent(approval_data) → {{"success":true, "claim_status":"Approved"}}
"""

# Create the root agent with ADK
root_agent = Agent(
    model=DEFAULT_MODEL,
    name="claim_processing_agent",
    description="Healthcare claim processing agent: OCR, fraud detection, remittance, database operations",
    instruction=AGENT_INSTRUCTION,
    generate_content_config=types.GenerateContentConfig(
        temperature=DEFAULT_TEMPERATURE,
        max_output_tokens=DEFAULT_MAX_TOKENS
    ),
    tools=[
        clinical_documentation_agent,
        adjudication_agent,
        insert_claim_tool,
        HITL_agent,
        remittance_agent,
        approval_agent
    ]
)


class ClaimProcessingAgent(BaseAgent):
    """ADK-based Claim Processing Agent with full orchestration"""
    
    def __init__(self, session_service=None, runner=None, app_name="claim_processing_app"):
        super().__init__(
            agent=root_agent,
            session_service=session_service,
            runner=runner,
            app_name=app_name
        )
    
    async def process_claim(self, gcs_path: str, file_name: str, metadata: dict = None):
        """
        Process a claim submission using the ADK agent
        
        Args:
            gcs_path: GCS path where file is already uploaded
            file_name: Name of the file
            metadata: Optional metadata (customer_id, policy_id, gcs_path, etc.)
        
        Returns:
            Agent response with processing results
        """
        if metadata is None:
            metadata = {}
        
        # Ensure gcs_path is in metadata
        metadata["gcs_path"] = gcs_path
        
        logger.info(f"[ClaimAgent] Processing claim: {file_name} from {gcs_path}")
        
        # Construct prompt for the agent
        prompt = f"""
I have received a new healthcare claim submission that has been uploaded to cloud storage.

File: {file_name}
GCS Path: {gcs_path}
Customer ID: {metadata.get('customer_id', 'Not provided')}
Policy ID: {metadata.get('policy_id', 'Not provided')}

Please process this claim through the complete workflow:
1. Extract text from {gcs_path} using extract_text_tool
2. Analyze for fraud and extract claim details using analyze_claim_tool
3. Save to database using insert_claim_tool
4. Determine routing:
   - If fraud detected or high amount: Flag for HITL review using insert_hitl_tool
   - If no issues: Process remittance using remittance_agent and approval_agent
5. Provide a professional confirmation message once complete

Execute the complete workflow now.
"""
        
        # Execute the prompt using the base agent
        result = await self.execute_prompt(prompt)
        
        if result.get("success"):
            logger.info(f"[ClaimAgent] ✅ Claim processed successfully: {file_name}")
            return result.get("response")
        else:
            logger.error(f"[ClaimAgent] ❌ Error processing claim: {result.get('error')}")
            # Return user-friendly error message
            return "Thank you for your submission. Your claim is being reviewed by our team. We will contact you if any additional information is needed."
    
    async def process_batch(self, claims: list):
        """
        Process multiple claims (max 10 concurrent)
        
        Args:
            claims: List of dicts with gcs_path, file_name, metadata
        
        Returns:
            List of processing results
        """
        if len(claims) > 10:
            raise ValueError("Maximum 10 claims can be processed concurrently")
        
        logger.info(f"[ClaimAgent] Processing batch of {len(claims)} claims")
        
        results = []
        for claim in claims:
            try:
                result = await self.process_claim(
                    gcs_path=claim.get('gcs_path'),
                    file_name=claim.get('file_name'),
                    metadata=claim.get('metadata', {})
                )
                results.append({
                    "file_name": claim.get('file_name'),
                    "status": "success",
                    "response": result
                })
            except Exception as e:
                logger.error(f"[ClaimAgent] Error in batch processing: {e}")
                results.append({
                    "file_name": claim.get('file_name'),
                    "status": "error",
                    "response": "Your claim is being reviewed by our team."
                })
        
        return results


# Singleton instance
claim_processing_agent = ClaimProcessingAgent()
