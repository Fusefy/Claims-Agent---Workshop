# backend/agents/base_agent.py
"""
Base Agent class for all ADK agents
Provides common functionality for session management and prompt execution
"""
import logging
from typing import Any, Dict, Optional
from google.adk.agents import Agent
from google.adk.sessions import Session, InMemorySessionService
from google.adk.runners import Runner
from google.genai import types

logger = logging.getLogger(__name__)


class BaseAgent:
    """Base class for all ADK agents with session management"""
    
    def __init__(
        self,
        agent: Agent,
        session_service: Optional[InMemorySessionService] = None,
        runner: Optional[Runner] = None,
        app_name: str = "claim_processing_app"
    ):
        """
        Initialize base agent
        
        Args:
            agent: The ADK Agent instance
            session_service: Session service for managing conversations
            runner: Runner for executing agent tasks
            app_name: Application name for session management
        """
        self.agent = agent
        self.app_name = app_name
        
        # Initialize session service if not provided
        self.session_service = session_service or InMemorySessionService()
        
        # Initialize runner if not provided (runner needs session_service and app_name)
        self.runner = runner or Runner(
            app_name=self.app_name,
            agent=self.agent,
            session_service=self.session_service
        )
        
        logger.info(f"[BaseAgent] Initialized with agent: {agent.name}")
    
    async def execute_prompt(
        self,
        prompt: str,
        session_id: Optional[str] = None,
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """
        Execute a prompt using the agent
        
        Args:
            prompt: The prompt to execute
            session_id: Optional session ID for conversation continuity
            user_id: User identifier
        
        Returns:
            Dict containing the agent's response and metadata
        """
        try:
            # Create or get session
            session = None
            if session_id:
                session = await self.session_service.get_session(
                    app_name=self.app_name,
                    user_id=user_id,
                    session_id=session_id
                )
            
            # If session not found or not provided, create new one
            if not session:
                session = await self.session_service.create_session(
                    app_name=self.app_name,
                    user_id=user_id,
                    session_id=session_id  # Try to use the provided ID if possible
                )
            
            logger.info(f"[BaseAgent] Executing prompt for session: {session.id}")
            
            # Create Content message from prompt
            new_message = types.Content(
                role='user',
                parts=[types.Part(text=prompt)]
            )
            
            # Execute the prompt using run_async - returns AsyncGenerator
            response_text = ""
            async for event in self.runner.run_async(
                user_id=user_id,
                session_id=session.id,
                new_message=new_message
            ):
                # Process events from the agent
                if hasattr(event, 'content'):
                    # Extract text from agent response
                    if hasattr(event.content, 'parts'):
                        for part in event.content.parts:
                            if hasattr(part, 'text') and part.text:
                                response_text += part.text
                    elif hasattr(event.content, 'text'):
                        response_text += event.content.text
            
            logger.info(f"[BaseAgent] Agent response received for session: {session.id}")
            
            return {
                "success": True,
                "response": response_text,
                "session_id": session.id
            }
            
        except Exception as e:
            logger.error(f"[BaseAgent] Error executing prompt: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "response": "An error occurred while processing your request. Please try again."
            }
    
    async def get_session_history(
        self,
        session_id: str,
        user_id: str = "default_user"
    ) -> list:
        """Get conversation history for a session"""
        try:
            session = await self.session_service.get_session(
                app_name=self.app_name,
                user_id=user_id,
                session_id=session_id
            )
            return session.messages if hasattr(session, 'messages') else []
        except Exception as e:
            logger.error(f"[BaseAgent] Error getting session history: {e}")
            return []
