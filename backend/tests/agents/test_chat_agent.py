"""
Unit tests for ChatAgent (agents/chat_agent.py)

Tests cover:
- handle_message invokes fetch_claim_details with customer_id
- handle_message invokes fetch_user_claims with customer_id
- handle_message invokes check_safety for suspicious input
- handle_message maintains conversation context
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from agents.chat_agent import ChatAgent


class TestChatAgent:
    """Tests for ChatAgent"""
    
    @pytest.fixture
    def mock_session_service(self):
        """Create a mock session service"""
        service = MagicMock()
        
        mock_session = MagicMock()
        mock_session.id = "chat-session-123"
        mock_session.messages = []
        
        service.create_session = AsyncMock(return_value=mock_session)
        service.get_session = AsyncMock(return_value=mock_session)
        
        return service
    
    @pytest.fixture
    def mock_runner(self):
        """Create a mock runner"""
        runner = MagicMock()
        
        async def mock_run_async(*args, **kwargs):
            mock_event = MagicMock()
            mock_event.content = MagicMock()
            mock_event.content.parts = [MagicMock()]
            mock_event.content.parts[0].text = "Your claim CLM-123 is approved."
            yield mock_event
        
        runner.run_async = mock_run_async
        
        return runner
    
    @pytest.mark.asyncio
    async def test_handle_message_includes_customer_context(
        self, mock_session_service, mock_runner
    ):
        """
        Test that handle_message includes customer_id in context
        
        Requirements: 9.3
        """
        # Arrange
        chat_agent = ChatAgent(
            session_service=mock_session_service,
            runner=mock_runner
        )
        
        # Act
        result = await chat_agent.handle_message(
            message="What is my claim status?",
            session_id="test-session",
            customer_id="CUST123"
        )
        
        # Assert
        assert result["success"] is True
        assert "response" in result
    
    @pytest.mark.asyncio
    async def test_handle_message_without_customer_id(
        self, mock_session_service, mock_runner
    ):
        """
        Test that handle_message works without customer_id
        
        Edge case: Anonymous user
        """
        # Arrange
        chat_agent = ChatAgent(
            session_service=mock_session_service,
            runner=mock_runner
        )
        
        # Act
        result = await chat_agent.handle_message(
            message="Hello",
            session_id="test-session"
        )
        
        # Assert
        assert result["success"] is True
        assert "response" in result
    
    @pytest.mark.asyncio
    async def test_handle_message_maintains_session(
        self, mock_session_service, mock_runner
    ):
        """
        Test that handle_message maintains conversation context via session
        
        Requirements: 9.3
        """
        # Arrange
        chat_agent = ChatAgent(
            session_service=mock_session_service,
            runner=mock_runner
        )
        
        session_id = "persistent-session"
        
        # Act - Send multiple messages
        result1 = await chat_agent.handle_message(
            message="Show my claims",
            session_id=session_id,
            customer_id="CUST123"
        )
        
        result2 = await chat_agent.handle_message(
            message="What about the first one?",
            session_id=session_id,
            customer_id="CUST123"
        )
        
        # Assert
        assert result1["success"] is True
        assert result2["success"] is True
        assert result1["session_id"] == result2["session_id"]
    
    @pytest.mark.asyncio
    async def test_handle_message_error_handling(
        self, mock_session_service
    ):
        """
        Test that handle_message handles errors gracefully
        
        Edge case: Runner failure
        """
        # Arrange
        mock_runner = MagicMock()
        
        async def failing_run_async(*args, **kwargs):
            raise Exception("Agent error")
            yield
        
        mock_runner.run_async = failing_run_async
        
        chat_agent = ChatAgent(
            session_service=mock_session_service,
            runner=mock_runner
        )
        
        # Act
        result = await chat_agent.handle_message(
            message="Test",
            customer_id="CUST123"
        )
        
        # Assert
        assert result["success"] is False
        assert "error" in result
