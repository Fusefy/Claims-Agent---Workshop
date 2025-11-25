# backend/routes/chat_routes.py
"""
Chat Routes - AI Assistant endpoints with claim data integration
"""
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import logging
import jwt
from services.chat_service import chat_service
from utils.config import JWT_SECRET, JWT_ALGORITHM
import uuid

router = APIRouter(prefix="/api/chat", tags=["chat"])
logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    """Chat request model"""
    message: str = Field(..., min_length=1, max_length=2000, description="User message")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    context: Optional[Dict[str, Any]] = Field(None, description="Optional context data")


class ChatResponse(BaseModel):
    """Chat response model"""
    success: bool
    response: str
    session_id: str
    claim_ids_detected: Optional[list] = None
    error: Optional[str] = None


def get_customer_id_from_token(authorization: Optional[str]) -> Optional[str]:
    """Extract customer_id (user_id) from JWT token"""
    if not authorization:
        return None
    
    try:
        # Remove 'Bearer ' prefix if present
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        # Return user_id as customer_id (they're the same in your schema)
        return str(payload.get("sub"))
    except Exception as e:
        logger.warning(f"[ChatAPI] Failed to decode token: {e}")
        return None


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    authorization: Optional[str] = Header(None)
) -> ChatResponse:
    """
    Chat with AI assistant about claims
    
    - **message**: User's question or message (required)
    - **session_id**: Optional session ID to maintain conversation context
    - **context**: Optional context (can include customer_id if not using auth)
    
    Returns AI-generated response with claim data integration.
    Automatically detects claim IDs (CLM-*) and fetches relevant data.
    """
    try:
        # Generate session_id if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Build context
        context = request.context or {}
        
        # Try to get customer_id from token first, then from context
        customer_id = get_customer_id_from_token(authorization)
        if customer_id:
            context["customer_id"] = customer_id
        elif not context.get("customer_id"):
            # If no customer_id available, log warning but continue
            logger.info("[ChatAPI] No customer_id provided - limited claim access")
        
        logger.info(f"[ChatAPI] Message (session: {session_id}, customer: {context.get('customer_id', 'none')}): {request.message[:50]}...")
        
        # Get AI response with claim data integration
        result = await chat_service.get_response(
            message=request.message,
            session_id=session_id,
            context=context
        )
        
        if not result.get("success"):
            logger.warning(f"[ChatAPI] Chat service returned error: {result.get('error')}")
        
        return ChatResponse(
            success=result.get("success", False),
            response=result.get("response", ""),
            session_id=session_id,
            claim_ids_detected=result.get("claim_ids_detected"),
            error=result.get("error")
        )
        
    except Exception as e:
        logger.error(f"[ChatAPI] Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """
    Clear a specific chat session history
    
    Useful when user wants to start a fresh conversation.
    """
    try:
        chat_service.clear_session(session_id)
        return {"success": True, "message": f"Session {session_id} cleared"}
    except Exception as e:
        logger.error(f"[ChatAPI] Error clearing session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check for chat service"""
    return {"status": "healthy", "service": "chat"}
