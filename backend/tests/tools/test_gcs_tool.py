"""
Unit tests for GCS upload tool (tools/gcs_tool.py)

Tests cover:
- Upload with bytes data returns valid GCS path
- Upload with string data converts to bytes
- Uninitialized GCS client raises RuntimeError
- Upload failure raises descriptive exception
"""
import pytest
from unittest.mock import MagicMock, patch
from tools.gcs_tool import upload_to_gcs


class TestGCSTool:
    """Tests for GCS file upload tool"""
    
    def test_upload_to_gcs_bytes_returns_valid_path(self, mock_gcs_client):
        """
        Test that uploading bytes data returns valid gs:// path
        
        Requirements: 5.1
        """
        # Arrange
        file_name = "test_claim.pdf"
        file_data = b"PDF file content"
        
        # Act
        result = upload_to_gcs(file_name, file_data)
        
        # Assert
        assert "gcs_path" in result
        assert result["gcs_path"].startswith("gs://")
        assert file_name in result["gcs_path"]

    
    def test_upload_to_gcs_string_converts_to_bytes(self, mock_gcs_client):
        """
        Test that string data is converted to bytes before upload
        
        Requirements: 5.2
        """
        # Arrange
        file_name = "test_claim.txt"
        file_data = "Text file content"
        
        # Act
        result = upload_to_gcs(file_name, file_data)
        
        # Assert
        assert "gcs_path" in result
        # Verify blob.upload_from_string was called with bytes
        bucket = mock_gcs_client.bucket.return_value
        blob = bucket.blob.return_value
        blob.upload_from_string.assert_called_once()
        call_args = blob.upload_from_string.call_args[0]
        assert isinstance(call_args[0], bytes)
    
    def test_upload_to_gcs_uninitialized_client_raises_error(self):
        """
        Test that uninitialized GCS client raises RuntimeError
        
        Requirements: 5.3
        """
        # Arrange
        file_name = "test.pdf"
        file_data = b"content"
        
        with patch('tools.gcs_tool.get_gcs_client') as mock_get_client:
            mock_get_client.side_effect = RuntimeError("GCS client not initialized")
            
            # Act & Assert
            # The tool wraps RuntimeError in Exception with "GCS upload failed"
            with pytest.raises(Exception) as exc_info:
                upload_to_gcs(file_name, file_data)
            
            assert "GCS upload failed" in str(exc_info.value)
    
    def test_upload_to_gcs_failure_raises_descriptive_exception(self, mock_gcs_client):
        """
        Test that upload failure raises exception with descriptive message
        
        Requirements: 5.4, 10.4
        """
        # Arrange
        file_name = "test.pdf"
        file_data = b"content"
        
        bucket = mock_gcs_client.bucket.return_value
        blob = bucket.blob.return_value
        blob.upload_from_string.side_effect = Exception("Network timeout")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            upload_to_gcs(file_name, file_data)
        
        assert "GCS upload failed" in str(exc_info.value)
        assert "Network timeout" in str(exc_info.value)
    
    def test_upload_to_gcs_generates_unique_path(self, mock_gcs_client):
        """
        Test that each upload generates a unique path
        
        Edge case: Multiple uploads of same file
        """
        # Arrange
        file_name = "claim.pdf"
        file_data = b"content"
        
        # Act
        result1 = upload_to_gcs(file_name, file_data)
        result2 = upload_to_gcs(file_name, file_data)
        
        # Assert - Paths should be different due to unique ID
        assert result1["gcs_path"] != result2["gcs_path"]
        assert file_name in result1["gcs_path"]
        assert file_name in result2["gcs_path"]
