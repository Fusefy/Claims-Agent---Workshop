# backend/services/chat_service.py
"""
Chat Service - AI Assistant for Claims using ADK Chat Agent
Provides context-aware responses for claims-related queries with claim data integration
"""
import logging
from typing import Optional, Dict, Any
from agents.chat_agent import chat_agent

logger = logging.getLogger(__name__)

class ChatService:
    """Service for handling AI chat interactions using the ADK Chat Agent"""
    
    def __init__(self):
        self.agent = chat_agent
    
    async def get_response(
        self, 
        message: str, 
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get AI response for user message using the Chat Agent
        
        Args:
            message: User's message
            session_id: Optional session ID for conversation continuity
            context: Optional context (customer_id, etc.)
        
        Returns:
            Dict with response and metadata
        """
        try:
            customer_id = context.get("customer_id") if context else None
            
            logger.info(f"[ChatService] Processing message for session: {session_id}")
            
            # Delegate to the ADK agent
            result = await self.agent.handle_message(
                message=message,
                session_id=session_id,
                customer_id=customer_id
            )
            
            if result.get("success"):
                return {
                    "success": True,
                    "response": result.get("response"),
                    "session_id": result.get("session_id"),
                    # We don't explicitly extract claim IDs anymore, the agent handles it
                    "claim_ids_detected": None 
                }
            else:
                logger.error(f"[ChatService] Agent failed: {result.get('error')}")
                return {
                    "success": False,
                    "response": "I apologize, but I'm having trouble processing your request right now. Please try again.",
                    "error": result.get("error")
                }
                
        except Exception as e:
            logger.error(f"[ChatService] Error generating response: {e}", exc_info=True)
            return {
                "success": False,
                "response": "I'm experiencing technical difficulties. Please try again or contact support@claimwise.com.",
                "error": str(e)
            }
    
    def clear_session(self, session_id: str):
        """Clear chat session history"""
        # ADK InMemorySessionService handles this automatically or we can implement explicit clear if needed
        # For now, we just log it as the session service is in-memory
        logger.info(f"[ChatService] Session clear requested for: {session_id}")
    
    def clear_all_sessions(self):
        """Clear all chat sessions (cleanup)"""
        logger.info("[ChatService] All sessions clear requested")


# Singleton instance
chat_service = ChatService()
