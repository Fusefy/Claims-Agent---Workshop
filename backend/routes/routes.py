# backend/routes/routes.py
"""
Main routes file - includes agent processing routes
Import other routers (claim_routes, hitl_routes, user_routes) in app.py
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional, List
import logging
from agents.agent import claim_processing_agent
from tools.gcs_tool import upload_to_gcs

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/hello")
def hello():
    return {"message": "Hello from Claimwise agent"}


@router.post("/api/claims/process")
async def process_claim(
    file: UploadFile = File(..., description="Claim document (PDF or image)"),
    customer_id: Optional[str] = Form(None),
    policy_id: Optional[str] = Form(None),
):
    """
    Process a single claim using the ADK orchestrator agent
    
    The agent will:
    1. Extract text via OCR from GCS
    2. Analyze with LLM for fraud detection
    3. Save to database
    4. Flag for HITL if needed
    5. Return user-friendly confirmation message
    
    Returns:
        Agent's response with processing confirmation
    """
    try:
        logger.info(f"[API] Processing claim: {file.filename}")
        
        # Read file content
        file_content = await file.read()
        
        # Upload to GCS first (before agent processing)
        upload_result = upload_to_gcs(
            file_name=file.filename,
            file_data=file_content,
            content_type=file.content_type or "application/pdf"
        )
        gcs_path = upload_result["gcs_path"]
        logger.info(f"[API] File uploaded to: {gcs_path}")
        
        # Prepare metadata
        metadata = {
            "gcs_path": gcs_path,
            "file_name": file.filename
        }
        if customer_id:
            metadata["customer_id"] = customer_id
        if policy_id:
            metadata["policy_id"] = policy_id
        
        # Process claim using agent orchestrator (OCR -> Analyze -> DB -> HITL)
        result = await claim_processing_agent.process_claim(
            gcs_path=gcs_path,
            file_name=file.filename,
            metadata=metadata
        )
        
        return JSONResponse(status_code=200, content={"response": result})
        
    except Exception as e:
        logger.error(f"[API] Error in process_claim: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/claims/process/batch")
async def process_claims_batch(
    files: List[UploadFile] = File(..., description="Multiple claim documents (max 10)"),
):
    """
    Process multiple claims concurrently (max 10)
    
    Each claim is processed by the agent orchestrator
    
    Returns:
        List of agent responses for each claim
    """
    try:
        if len(files) > 10:
            raise HTTPException(
                status_code=400,
                detail=f"Maximum 10 files allowed, received {len(files)}"
            )
        
        logger.info(f"[API] Batch processing: {len(files)} claims")
        
        # Prepare claims list with pre-uploaded GCS paths
        claims = []
        for file in files:
            file_content = await file.read()
            
            # Upload each file to GCS
            upload_result = upload_to_gcs(
                file_name=file.filename,
                file_data=file_content,
                content_type=file.content_type or "application/pdf"
            )
            gcs_path = upload_result["gcs_path"]
            
            claims.append({
                "gcs_path": gcs_path,
                "file_name": file.filename,
                "metadata": {"gcs_path": gcs_path, "file_name": file.filename}
            })
        
        # Process batch
        results = await claim_processing_agent.process_batch(claims)
        
        return JSONResponse(
            status_code=200,
            content={
                "total": len(results),
                "results": results
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Error in batch processing: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))