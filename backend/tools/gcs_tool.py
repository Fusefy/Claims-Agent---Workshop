# backend/tools/gcs_tool.py
"""
Google Cloud Storage Tool

Provides functionality to upload files to Google Cloud Storage.
Uses the centralized GCP client from utils.gcp_clients.
"""
import uuid
from datetime import datetime
import logging
from utils.config import GCS_BUCKET_NAME
from utils.gcp_clients import get_gcs_client

logger = logging.getLogger(__name__)


def upload_to_gcs(file_name: str, file_data: bytes, content_type: str = "application/pdf") -> dict:
    """
    Upload file to Google Cloud Storage.
    
    Args:
        file_name: Original filename to upload
        file_data: File content as bytes
        content_type: MIME type of the file (default: application/pdf)
    
    Returns:
        Dictionary containing the GCS path where the file was uploaded
        
    Raises:
        RuntimeError: If GCS client not initialized
        Exception: If upload fails
    """
    try:
        logger.info(f"[GCS] Uploading file: {file_name}")
        
        # Get the shared GCS client
        client = get_gcs_client()
        bucket = client.bucket(GCS_BUCKET_NAME)
        
        # Generate unique path
        timestamp = datetime.utcnow().strftime("%Y%m%d")
        unique_id = str(uuid.uuid4())[:8]
        blob_path = f"claims/{timestamp}/{unique_id}/{file_name}"
        
        blob = bucket.blob(blob_path)
        
        # Ensure file_data is bytes
        if isinstance(file_data, str):
            file_data = file_data.encode()
        
        blob.upload_from_string(file_data, content_type=content_type)
        
        gcs_path = f"gs://{GCS_BUCKET_NAME}/{blob_path}"
        
        logger.info(f"[GCS] ✅ File uploaded: {gcs_path}")
        return {"gcs_path": gcs_path}
        
    except Exception as e:
        logger.error(f"[GCS] ❌ Error: {str(e)}")
        raise Exception(f"GCS upload failed: {str(e)}")
