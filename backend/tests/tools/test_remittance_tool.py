"""
Unit tests for remittance tool (tools/remittance_tool.py)

Tests cover:
- process_remittance returns required fields
- Approved amount capping at claim amount
- Non-pending claim rejection
- Invalid claim ID raises ValueError
"""
import pytest
import json
from unittest.mock import MagicMock, patch
from tools.remittance_tool import process_remittance


class TestRemittanceTool:
    """Tests for remittance processing tool"""
    
    def test_process_remittance_returns_required_fields(
        self, mock_remittance_claim_repository
    ):
        """
        Test that process_remittance returns approved_amount and ai_reasoning
        
        Requirements: 7.1
        """
        # Arrange
        claim_id = "CLM-2024-TEST01"
        
        with patch('tools.remittance_tool.remittance_analyzer') as mock_analyzer:
            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.text = json.dumps({
                "approved_amount": 4500.00,
                "approval_percentage": 90,
                "ai_reasoning": "In-network: 90% coverage",
                "coverage_details": {}
            })
            mock_model.generate_content.return_value = mock_response
            mock_analyzer.get_model.return_value = mock_model
            
            # Act
            result = process_remittance(claim_id)
            
            # Assert
            assert result["success"] is True
            assert "approved_amount" in result
            assert "ai_reasoning" in result
            assert result["approved_amount"] == 4500.00

    
    def test_process_remittance_caps_approved_amount(
        self, mock_remittance_claim_repository
    ):
        """
        Test that approved_amount is capped at claim_amount
        
        Requirements: 7.2
        """
        # Arrange
        claim_id = "CLM-2024-TEST01"
        
        with patch('tools.remittance_tool.remittance_analyzer') as mock_analyzer:
            mock_model = MagicMock()
            mock_response = MagicMock()
            # LLM returns amount > claim_amount
            mock_response.text = json.dumps({
                "approved_amount": 6000.00,  # Greater than claim_amount (5000)
                "approval_percentage": 120,
                "ai_reasoning": "Full approval",
                "coverage_details": {}
            })
            mock_model.generate_content.return_value = mock_response
            mock_analyzer.get_model.return_value = mock_model
            
            # Act
            result = process_remittance(claim_id)
            
            # Assert
            assert result["approved_amount"] == 5000.00  # Capped at claim_amount
            assert result["approved_amount"] <= result["original_amount"]
    
    def test_process_remittance_rejects_non_pending_claim(
        self, mock_remittance_claim_repository
    ):
        """
        Test that non-pending claims are rejected
        
        Requirements: 7.3
        """
        # Arrange
        claim_id = "CLM-2024-TEST01"
        
        # Mock claim with non-Pending status
        mock_claim = MagicMock()
        mock_claim.claim_id = claim_id
        mock_claim.claim_status = "Approved"  # Not Pending
        mock_remittance_claim_repository.get_by_id.return_value = mock_claim
        
        # Act
        result = process_remittance(claim_id)
        
        # Assert
        assert result["success"] is False
        assert "cannot process remittance" in result["error"]
    
    def test_process_remittance_invalid_claim_id_raises_error(
        self, mock_remittance_claim_repository
    ):
        """
        Test that invalid claim_id raises ValueError
        
        Requirements: 7.4
        """
        # Arrange
        claim_id = "INVALID-ID"
        mock_remittance_claim_repository.get_by_id.return_value = None
        
        # Act & Assert
        # The tool wraps ValueError in Exception with "Remittance processing failed"
        with pytest.raises(Exception) as exc_info:
            process_remittance(claim_id)
        
        assert "Remittance processing failed" in str(exc_info.value)
        assert "Claim not found" in str(exc_info.value)
    
    def test_process_remittance_llm_error_propagates(
        self, mock_remittance_claim_repository
    ):
        """
        Test that LLM errors are propagated
        
        Edge case: LLM API failure
        """
        # Arrange
        claim_id = "CLM-2024-TEST01"
        
        with patch('tools.remittance_tool.remittance_analyzer') as mock_analyzer:
            mock_model = MagicMock()
            mock_model.generate_content.side_effect = Exception("LLM API error")
            mock_analyzer.get_model.return_value = mock_model
            
            # Act & Assert
            with pytest.raises(Exception) as exc_info:
                process_remittance(claim_id)
            
            assert "Remittance processing failed" in str(exc_info.value)
