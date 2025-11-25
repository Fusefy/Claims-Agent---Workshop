# backend/tools/ocr_tool.py
"""
OCR Tool using Google Cloud Vision API

Provides functionality to extract text from PDFs and images.
Uses the centralized GCP client from utils.gcp_clients.
"""
from google.cloud import vision
import logging
from utils.gcp_clients import get_vision_client

logger = logging.getLogger(__name__)


def extract_text(gcs_path: str, file_name: str = "") -> dict:
    """
    Extract text from PDF or image using Google Cloud Vision API.
    
    Args:
        gcs_path: GCS path to the file (format: gs://bucket/path/to/file)
        file_name: Optional filename for logging purposes
    
    Returns:
        Dictionary containing the extracted text from the document
        
    Raises:
        RuntimeError: If Vision API client not initialized
        ValueError: If gcs_path is invalid
        Exception: If text extraction fails
    """
    try:
        # Get the shared Vision API client
        client = get_vision_client()
        
        # Ensure gcs_path starts with gs://
        if not gcs_path.startswith("gs://"):
            raise ValueError(f"gcs_path must start with gs://, got: {gcs_path}")
        
        logger.info(f"[OCR] Extracting text from GCS: {gcs_path}")
        extracted_text = _extract_from_gcs(client, gcs_path)
        
        logger.info(f"[OCR] ✅ Text extraction complete: {len(extracted_text)} characters")
        return {"extracted_text": extracted_text}
        
    except Exception as e:
        logger.error(f"[OCR] ❌ Error: {str(e)}")
        raise Exception(f"OCR extraction failed: {str(e)}")


def _extract_from_gcs(client: vision.ImageAnnotatorClient, gcs_path: str) -> str:
    """Extract text from file in GCS"""
    try:
        gcs_source = vision.GcsSource(uri=gcs_path)
        input_config = vision.InputConfig(
            gcs_source=gcs_source,
            mime_type='application/pdf'
        )
        
        feature = vision.Feature(type_=vision.Feature.Type.DOCUMENT_TEXT_DETECTION)
        request = vision.AnnotateFileRequest(
            features=[feature],
            input_config=input_config,
        )
        
        response = client.batch_annotate_files(requests=[request])
        
        text_parts = []
        for image_response in response.responses[0].responses:
            if image_response.full_text_annotation:
                text_parts.append(image_response.full_text_annotation.text)
        
        return "\n\n".join(text_parts)
    except Exception as e:
        logger.error(f"[OCR] Error in GCS OCR: {e}")
        raise


def _extract_from_bytes(client: vision.ImageAnnotatorClient, file_bytes: bytes) -> str:
    """Extract text directly from file bytes"""
    try:
        image = vision.Image(content=file_bytes)
        response = client.document_text_detection(image=image)
        
        if response.error.message:
            raise Exception(f"Vision API error: {response.error.message}")
        
        if response.full_text_annotation:
            return response.full_text_annotation.text
        else:
            texts = response.text_annotations
            if texts:
                return texts[0].description
            return ""
    except Exception as e:
        logger.error(f"[OCR] Error in bytes OCR: {e}")
        raise


# Export the function directly
clinical_documentation_agent = extract_text
