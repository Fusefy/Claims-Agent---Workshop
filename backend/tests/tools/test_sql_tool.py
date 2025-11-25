"""
Unit tests for SQL tool (tools/sql_tool.py)

Tests cover:
- insert_claim creates record successfully
- insert_claim with invalid status defaults to Pending
- insert_hitl creates HITL record
- update_claim_approval updates status and amount
- patient_id to customer_id mapping
- Database error propagation
"""
import pytest
import json
from unittest.mock import MagicMock
from tools.sql_tool import insert_claim, insert_hitl, update_claim_approval


class TestSQLTool:
    """Tests for SQL database operations tool"""
    
    def test_insert_claim_creates_record_successfully(
        self, mock_claim_repository, mock_history_repository, sample_claim_data
    ):
        """
        Test that insert_claim creates ProposedClaim record
        
        Requirements: 6.1
        """
        # Arrange
        claim_data_str = json.dumps(sample_claim_data)
        
        # Act
        result = insert_claim(claim_data_str)
        
        # Assert
        assert result["success"] is True
        assert result["claim_id"] == sample_claim_data["claim_id"]
        mock_claim_repository.create.assert_called_once()
        mock_history_repository.log_status_change.assert_called_once()

    
    def test_insert_claim_invalid_status_defaults_to_pending(
        self, mock_claim_repository, mock_history_repository
    ):
        """
        Test that invalid claim_status defaults to Pending
        
        Requirements: 6.2
        """
        # Arrange
        claim_data = {
            "claim_id": "CLM-2024-TEST01",
            "claim_name": "Test",
            "patient_id": "CUST123",
            "policy_id": "POL456",
            "claim_type": "Medical",
            "network_status": "In-Network",
            "date_of_service": "2024-01-15",
            "claim_amount": 5000.00,
            "approved_amount": 0.0,
            "claim_status": "InvalidStatus",  # Invalid status
            "error_type": "None",
            "ai_reasoning": "Test",
            "fraud_status": "No Fraud",
            "confidence": 0.95,
            "fraud_reason": None,
            "hitl_flag": False
        }
        
        # Act
        result = insert_claim(json.dumps(claim_data))
        
        # Assert
        assert result["success"] is True
        assert result["status"] == "Pending"  # Should default to Pending
    
    def test_insert_hitl_creates_record(
        self, mock_hitl_repository, mock_history_repository, sample_hitl_data
    ):
        """
        Test that insert_hitl creates HitlQueue record
        
        Requirements: 6.3
        """
        # Arrange
        hitl_data_str = json.dumps(sample_hitl_data)
        
        # Act
        result = insert_hitl(hitl_data_str)
        
        # Assert
        assert result["success"] is True
        assert result["hitl_record_created"] is True
        mock_hitl_repository.create.assert_called_once()
    
    def test_update_claim_approval_updates_status_and_amount(
        self, mock_claim_repository, mock_history_repository, sample_approval_data
    ):
        """
        Test that update_claim_approval updates both status and amount
        
        Requirements: 6.4
        """
        # Arrange
        approval_data_str = json.dumps(sample_approval_data)
        
        # Act
        result = update_claim_approval(approval_data_str)
        
        # Assert
        assert result["success"] is True
        assert result["claim_status"] == "Approved"
        assert result["approved_amount"] == sample_approval_data["approved_amount"]
        mock_claim_repository.update.assert_called_once()
    
    def test_insert_claim_maps_patient_id_to_customer_id(
        self, mock_claim_repository, mock_history_repository
    ):
        """
        Test that patient_id is correctly mapped to customer_id
        
        Requirements: 6.5
        """
        # Arrange - Use patient_id instead of customer_id
        claim_data = {
            "claim_id": "CLM-2024-TEST01",
            "claim_name": "Test",
            "patient_id": "PATIENT123",  # Using patient_id
            "policy_id": "POL456",
            "claim_type": "Medical",
            "network_status": "In-Network",
            "date_of_service": "2024-01-15",
            "claim_amount": 5000.00,
            "approved_amount": 0.0,
            "claim_status": "Pending",
            "error_type": "None",
            "ai_reasoning": "Test",
            "fraud_status": "No Fraud",
            "confidence": 0.95,
            "fraud_reason": None,
            "hitl_flag": False
        }
        
        # Act
        result = insert_claim(json.dumps(claim_data))
        
        # Assert
        assert result["success"] is True
        # Verify create was called with customer_id mapped from patient_id
        call_args = mock_claim_repository.create.call_args[0][0]
        assert call_args.customer_id == "PATIENT123"
    
    def test_insert_claim_database_error_propagates(
        self, mock_claim_repository, mock_history_repository
    ):
        """
        Test that database errors are propagated with context
        
        Requirements: 10.3
        """
        # Arrange
        claim_data = {"claim_id": "CLM-TEST", "patient_id": "CUST123"}
        mock_claim_repository.create.side_effect = Exception("Database connection failed")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            insert_claim(json.dumps(claim_data))
        
        assert "Database insert failed" in str(exc_info.value)
    
    def test_insert_claim_converts_none_error_type(
        self, mock_claim_repository, mock_history_repository
    ):
        """
        Test that string "None" is converted to Python None for error_type
        
        Edge case: LLM returns "None" as string
        """
        # Arrange
        claim_data = {
            "claim_id": "CLM-2024-TEST01",
            "claim_name": "Test",
            "patient_id": "CUST123",
            "policy_id": "POL456",
            "claim_type": "Medical",
            "network_status": "In-Network",
            "date_of_service": "2024-01-15",
            "claim_amount": 5000.00,
            "approved_amount": 0.0,
            "claim_status": "Pending",
            "error_type": "None",  # String "None"
            "ai_reasoning": "Test",
            "fraud_status": "No Fraud",
            "confidence": 0.95,
            "fraud_reason": None,
            "hitl_flag": False
        }
        
        # Act
        result = insert_claim(json.dumps(claim_data))
        
        # Assert
        assert result["success"] is True
        assert result["error_type"] is None  # Should be Python None
