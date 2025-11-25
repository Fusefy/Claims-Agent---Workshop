"""
Unit tests for BaseAgent (agents/base_agent.py)

Tests cover:
- execute_prompt creates or retrieves session
- execute_prompt returns formatted response
- execute_prompt handles exceptions gracefully
- get_session_history retrieves conversation history
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from agents.base_agent import BaseAgent
from google.adk.agents import Agent
from google.genai import types


class TestBaseAgent:
    """Tests for BaseAgent"""
    
    @pytest.fixture
    def mock_agent(self):
        """Create a mock ADK Agent"""
        agent = MagicMock(spec=Agent)
        agent.name = "test_agent"
        return agent
    
    @pytest.fixture
    def mock_session_service(self):
        """Create a mock session service"""
        service = MagicMock()
        
        # Mock session object
        mock_session = MagicMock()
        mock_session.id = "test-session-123"
        mock_session.messages = []
        
        service.create_session = AsyncMock(return_value=mock_session)
        service.get_session = AsyncMock(return_value=mock_session)
        
        return service
    
    @pytest.fixture
    def mock_runner(self):
        """Create a mock runner"""
        runner = MagicMock()
        
        # Mock async generator for run_async
        async def mock_run_async(*args, **kwargs):
            # Simulate agent response event
            mock_event = MagicMock()
            mock_event.content = MagicMock()
            mock_event.content.parts = [MagicMock()]
            mock_event.content.parts[0].text = "Test response from agent"
            yield mock_event
        
        runner.run_async = mock_run_async
        
        return runner

    
    @pytest.mark.asyncio
    async def test_execute_prompt_creates_session(
        self, mock_agent, mock_session_service, mock_runner
    ):
        """
        Test that execute_prompt creates a new session when none exists
        
        Requirements: 9.4
        """
        # Arrange
        base_agent = BaseAgent(
            agent=mock_agent,
            session_service=mock_session_service,
            runner=mock_runner,
            app_name="test_app"
        )
        
        # Act
        result = await base_agent.execute_prompt("Test prompt")
        
        # Assert
        assert result["success"] is True
        assert "response" in result
        assert "session_id" in result
        mock_session_service.create_session.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_prompt_returns_formatted_response(
        self, mock_agent, mock_session_service, mock_runner
    ):
        """
        Test that execute_prompt returns properly formatted response
        
        Requirements: 9.4
        """
        # Arrange
        base_agent = BaseAgent(
            agent=mock_agent,
            session_service=mock_session_service,
            runner=mock_runner,
            app_name="test_app"
        )
        
        # Act
        result = await base_agent.execute_prompt("Test prompt")
        
        # Assert
        assert result["success"] is True
        assert isinstance(result["response"], str)
        assert len(result["response"]) > 0
        assert result["session_id"] == "test-session-123"
    
    @pytest.mark.asyncio
    async def test_execute_prompt_handles_exceptions_gracefully(
        self, mock_agent, mock_session_service
    ):
        """
        Test that execute_prompt handles exceptions and returns error response
        
        Requirements: 9.4
        """
        # Arrange
        mock_runner = MagicMock()
        
        async def failing_run_async(*args, **kwargs):
            raise Exception("Runner error")
            yield  # Make it a generator
        
        mock_runner.run_async = failing_run_async
        
        base_agent = BaseAgent(
            agent=mock_agent,
            session_service=mock_session_service,
            runner=mock_runner,
            app_name="test_app"
        )
        
        # Act
        result = await base_agent.execute_prompt("Test prompt")
        
        # Assert
        assert result["success"] is False
        assert "error" in result
        assert "response" in result
        assert "An error occurred" in result["response"]
    
    @pytest.mark.asyncio
    async def test_execute_prompt_retrieves_existing_session(
        self, mock_agent, mock_session_service, mock_runner
    ):
        """
        Test that execute_prompt retrieves existing session when session_id provided
        
        Requirements: 9.4
        """
        # Arrange
        base_agent = BaseAgent(
            agent=mock_agent,
            session_service=mock_session_service,
            runner=mock_runner,
            app_name="test_app"
        )
        
        # Act
        result = await base_agent.execute_prompt(
            "Test prompt",
            session_id="existing-session-123"
        )
        
        # Assert
        assert result["success"] is True
        mock_session_service.get_session.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_session_history_retrieves_messages(
        self, mock_agent, mock_session_service, mock_runner
    ):
        """
        Test that get_session_history retrieves conversation history
        
        Requirements: 9.4
        """
        # Arrange
        mock_session = MagicMock()
        mock_session.messages = ["message1", "message2", "message3"]
        mock_session_service.get_session = AsyncMock(return_value=mock_session)
        
        base_agent = BaseAgent(
            agent=mock_agent,
            session_service=mock_session_service,
            runner=mock_runner,
            app_name="test_app"
        )
        
        # Act
        history = await base_agent.get_session_history("test-session-123")
        
        # Assert
        assert len(history) == 3
        assert history == ["message1", "message2", "message3"]
    
    @pytest.mark.asyncio
    async def test_get_session_history_handles_errors(
        self, mock_agent, mock_session_service, mock_runner
    ):
        """
        Test that get_session_history returns empty list on error
        
        Edge case: Session not found
        """
        # Arrange
        mock_session_service.get_session = AsyncMock(side_effect=Exception("Session not found"))
        
        base_agent = BaseAgent(
            agent=mock_agent,
            session_service=mock_session_service,
            runner=mock_runner,
            app_name="test_app"
        )
        
        # Act
        history = await base_agent.get_session_history("invalid-session")
        
        # Assert
        assert history == []
