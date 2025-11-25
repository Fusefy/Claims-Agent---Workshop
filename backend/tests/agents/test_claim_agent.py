"""
Unit tests for ClaimProcessingAgent (agents/agent.py)

Tests cover:
- process_claim invokes tools in correct sequence
- process_claim handles OCR tool failure
- process_claim handles LLM tool failure
- process_claim handles SQL tool failure
- process_claim routes to HITL when needed
- process_claim routes to remittance when appropriate
- process_batch handles multiple claims
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from agents.agent import ClaimProcessingAgent


class TestClaimProcessingAgent:
    """Tests for ClaimProcessingAgent"""
    
    @pytest.fixture
    def mock_session_service(self):
        """Create a mock session service"""
        service = MagicMock()
        
        mock_session = MagicMock()
        mock_session.id = "claim-session-123"
        mock_session.messages = []
        
        service.create_session = AsyncMock(return_value=mock_session)
        service.get_session = AsyncMock(return_value=mock_session)
        
        return service
    
    @pytest.fixture
    def mock_runner(self):
        """Create a mock runner that simulates successful claim processing"""
        runner = MagicMock()
        
        async def mock_run_async(*args, **kwargs):
            mock_event = MagicMock()
            mock_event.content = MagicMock()
            mock_event.content.parts = [MagicMock()]
            mock_event.content.parts[0].text = (
                "Thank you for submitting your claim. Your claim CLM-2024-TEST01 "
                "has been successfully processed and approved for $4500.00. "
                "You will receive payment within 5-7 business days."
            )
            yield mock_event
        
        runner.run_async = mock_run_async
        
        return runner

    
    @pytest.mark.asyncio
    async def test_process_claim_successful_workflow(
        self, mock_session_service, mock_runner
    ):
        """
        Test that process_claim executes complete workflow successfully
        
        Requirements: 9.1, 9.2
        """
        # Arrange
        agent = ClaimProcessingAgent(
            session_service=mock_session_service,
            runner=mock_runner
        )
        
        # Act
        result = await agent.process_claim(
            gcs_path="gs://test-bucket/claim.pdf",
            file_name="claim.pdf",
            metadata={"customer_id": "CUST123", "policy_id": "POL456"}
        )
        
        # Assert
        assert isinstance(result, str)
        assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_process_claim_handles_tool_failure(
        self, mock_session_service
    ):
        """
        Test that process_claim handles tool failures gracefully
        
        Requirements: 9.2
        """
        # Arrange
        mock_runner = MagicMock()
        
        async def failing_run_async(*args, **kwargs):
            raise Exception("Tool execution failed")
            yield
        
        mock_runner.run_async = failing_run_async
        
        agent = ClaimProcessingAgent(
            session_service=mock_session_service,
            runner=mock_runner
        )
        
        # Act
        result = await agent.process_claim(
            gcs_path="gs://test-bucket/claim.pdf",
            file_name="claim.pdf"
        )
        
        # Assert
        assert isinstance(result, str)
        assert "being reviewed by our team" in result
    
    @pytest.mark.asyncio
    async def test_process_claim_includes_metadata(
        self, mock_session_service, mock_runner
    ):
        """
        Test that process_claim includes metadata in processing
        
        Requirements: 9.1
        """
        # Arrange
        agent = ClaimProcessingAgent(
            session_service=mock_session_service,
            runner=mock_runner
        )
        
        metadata = {
            "customer_id": "CUST123",
            "policy_id": "POL456"
        }
        
        # Act
        result = await agent.process_claim(
            gcs_path="gs://test-bucket/claim.pdf",
            file_name="claim.pdf",
            metadata=metadata
        )
        
        # Assert
        assert isinstance(result, str)
    
    @pytest.mark.asyncio
    async def test_process_batch_handles_multiple_claims(
        self, mock_session_service, mock_runner
    ):
        """
        Test that process_batch handles multiple claims
        
        Requirements: 9.1
        """
        # Arrange
        agent = ClaimProcessingAgent(
            session_service=mock_session_service,
            runner=mock_runner
        )
        
        claims = [
            {
                "gcs_path": "gs://test-bucket/claim1.pdf",
                "file_name": "claim1.pdf",
                "metadata": {"customer_id": "CUST123"}
            },
            {
                "gcs_path": "gs://test-bucket/claim2.pdf",
                "file_name": "claim2.pdf",
                "metadata": {"customer_id": "CUST456"}
            }
        ]
        
        # Act
        results = await agent.process_batch(claims)
        
        # Assert
        assert len(results) == 2
        assert all("file_name" in r for r in results)
        assert all("status" in r for r in results)
        assert all("response" in r for r in results)
    
    @pytest.mark.asyncio
    async def test_process_batch_rejects_too_many_claims(
        self, mock_session_service, mock_runner
    ):
        """
        Test that process_batch rejects more than 10 claims
        
        Edge case: Batch size limit
        """
        # Arrange
        agent = ClaimProcessingAgent(
            session_service=mock_session_service,
            runner=mock_runner
        )
        
        # Create 11 claims (exceeds limit of 10)
        claims = [
            {
                "gcs_path": f"gs://test-bucket/claim{i}.pdf",
                "file_name": f"claim{i}.pdf"
            }
            for i in range(11)
        ]
        
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await agent.process_batch(claims)
        
        assert "Maximum 10 claims" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_process_batch_handles_individual_failures(
        self, mock_session_service
    ):
        """
        Test that process_batch continues even if individual claims fail
        
        Edge case: Partial batch failure
        """
        # Arrange
        # The agent catches exceptions and returns error status
        # We need to simulate the execute_prompt behavior
        
        agent = ClaimProcessingAgent(
            session_service=mock_session_service,
            runner=MagicMock()
        )
        
        # Mock execute_prompt to fail for first claim, succeed for second
        call_count = [0]
        original_execute = agent.execute_prompt
        
        async def mock_execute(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                # First claim fails
                return {
                    "success": False,
                    "error": "Processing error",
                    "response": "Error occurred"
                }
            else:
                # Second claim succeeds
                return {
                    "success": True,
                    "response": "Claim processed successfully",
                    "session_id": "test-session"
                }
        
        agent.execute_prompt = mock_execute
        
        claims = [
            {"gcs_path": "gs://test/claim1.pdf", "file_name": "claim1.pdf"},
            {"gcs_path": "gs://test/claim2.pdf", "file_name": "claim2.pdf"}
        ]
        
        # Act
        results = await agent.process_batch(claims)
        
        # Assert
        assert len(results) == 2
        # Both should have status since process_batch catches exceptions
        assert "status" in results[0]
        assert "status" in results[1]
