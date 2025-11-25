"""
Unit tests for OCR tool (tools/ocr_tool.py)

Tests cover:
- Valid GCS path returns extracted text
- Invalid GCS path raises ValueError
- Uninitialized Vision API client raises RuntimeError
- Vision API errors are propagated
"""
import pytest
from unittest.mock import MagicMock, patch
from tools.ocr_tool import extract_text, _extract_from_gcs


class TestOCRTool:
    """Tests for OCR text extraction tool"""
    
    def test_extract_text_valid_gcs_path_returns_text(self, mock_vision_client):
        """
        Test that valid GCS path returns extracted text in correct format
        
        Requirements: 3.1
        """
        # Arrange
        gcs_path = "gs://test-bucket/claims/test.pdf"
        file_name = "test.pdf"
        
        # Act
        result = extract_text(gcs_path, file_name)
        
        # Assert
        assert "extracted_text" in result
        assert isinstance(result["extracted_text"], str)
        assert len(result["extracted_text"]) > 0
        mock_vision_client.batch_annotate_files.assert_called_once()
    
    def test_extract_text_invalid_path_raises_value_error(self, mock_vision_client):
        """
        Test that invalid GCS path (not starting with gs://) raises Exception with ValueError message
        
        Requirements: 3.2
        """
        # Arrange
        invalid_paths = [
            "/local/path/file.pdf",
            "http://example.com/file.pdf",
            "s3://bucket/file.pdf",
            "file.pdf"
        ]
        
        # Act & Assert
        for invalid_path in invalid_paths:
            with pytest.raises(Exception) as exc_info:
                extract_text(invalid_path, "test.pdf")
            
            # The tool wraps ValueError in Exception
            assert "OCR extraction failed" in str(exc_info.value)
            assert "must start with gs://" in str(exc_info.value)
    
    def test_extract_text_uninitialized_client_raises_runtime_error(self):
        """
        Test that uninitialized Vision API client raises Exception with RuntimeError message
        
        Requirements: 3.3
        """
        # Arrange
        gcs_path = "gs://test-bucket/claims/test.pdf"
        
        with patch('tools.ocr_tool.get_vision_client') as mock_get_client:
            # Simulate uninitialized client
            mock_get_client.side_effect = RuntimeError("Vision API client not initialized")
            
            # Act & Assert
            with pytest.raises(Exception) as exc_info:
                extract_text(gcs_path, "test.pdf")
            
            # The tool wraps RuntimeError in Exception
            assert "OCR extraction failed" in str(exc_info.value)
            assert "Vision API client not initialized" in str(exc_info.value)
    
    def test_extract_text_api_error_propagates_exception(self, mock_vision_client):
        """
        Test that Vision API errors are propagated with context
        
        Requirements: 3.4, 10.5
        """
        # Arrange
        gcs_path = "gs://test-bucket/claims/test.pdf"
        mock_vision_client.batch_annotate_files.side_effect = Exception("Vision API error: quota exceeded")
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            extract_text(gcs_path, "test.pdf")
        
        assert "OCR extraction failed" in str(exc_info.value)
    
    def test_extract_text_empty_response_returns_empty_string(self, mock_vision_client):
        """
        Test that empty OCR response returns empty string
        
        Edge case: Document with no text
        """
        # Arrange
        gcs_path = "gs://test-bucket/claims/blank.pdf"
        
        # Mock empty response
        mock_response = MagicMock()
        mock_response.responses = [MagicMock()]
        mock_response.responses[0].responses = []
        mock_vision_client.batch_annotate_files.return_value = mock_response
        
        # Act
        result = extract_text(gcs_path, "blank.pdf")
        
        # Assert
        assert result["extracted_text"] == ""
    
    def test_extract_text_multiple_pages_concatenates(self, mock_vision_client):
        """
        Test that multi-page documents concatenate text correctly
        
        Edge case: Multi-page PDF
        """
        # Arrange
        gcs_path = "gs://test-bucket/claims/multipage.pdf"
        
        # Mock multi-page response
        mock_response = MagicMock()
        page1 = MagicMock()
        page1.full_text_annotation = MagicMock()
        page1.full_text_annotation.text = "Page 1 text"
        
        page2 = MagicMock()
        page2.full_text_annotation = MagicMock()
        page2.full_text_annotation.text = "Page 2 text"
        
        mock_response.responses = [MagicMock()]
        mock_response.responses[0].responses = [page1, page2]
        mock_vision_client.batch_annotate_files.return_value = mock_response
        
        # Act
        result = extract_text(gcs_path, "multipage.pdf")
        
        # Assert
        assert "Page 1 text" in result["extracted_text"]
        assert "Page 2 text" in result["extracted_text"]
        assert "\n\n" in result["extracted_text"]  # Pages separated by double newline
    
    def test_extract_from_gcs_constructs_correct_request(self, mock_vision_client):
        """
        Test that _extract_from_gcs constructs correct Vision API request
        
        Internal function test
        """
        # Arrange
        gcs_path = "gs://test-bucket/claims/test.pdf"
        
        # Act
        _extract_from_gcs(mock_vision_client, gcs_path)
        
        # Assert
        mock_vision_client.batch_annotate_files.assert_called_once()
        call_args = mock_vision_client.batch_annotate_files.call_args
        
        # Verify request structure
        assert call_args is not None
        assert "requests" in call_args.kwargs or len(call_args.args) > 0
