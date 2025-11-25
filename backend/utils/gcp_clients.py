# backend/utils/gcp_clients.py
"""
Centralized GCP Client Management

This module provides singleton instances for all GCP clients (GCS and Vision API)
with application-level initialization. Clients are initialized once at app startup
and shared across all tools and services.

Usage:
    # At app startup (in app.py lifespan):
    from utils.gcp_clients import initialize_gcp_clients
    initialize_gcp_clients()
    
    # In tools/services:
    from utils.gcp_clients import get_gcs_client, get_vision_client
    client = get_gcs_client()
"""
from google.cloud import storage, vision
from google.oauth2 import service_account
from google.api_core.client_options import ClientOptions
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class GCPClients:
    """
    Singleton manager for all GCP clients.
    
    This class ensures that GCP clients are initialized once and shared
    across the entire application, following the singleton pattern.
    """
    _instance = None
    _gcs_client: Optional[storage.Client] = None
    _vision_client: Optional[vision.ImageAnnotatorClient] = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def initialize(self, project_id: str, credentials_dict: dict) -> None:
        """
        Initialize all GCP clients at application startup.
        
        Args:
            project_id: GCP project ID
            credentials_dict: Service account credentials dictionary
            
        Raises:
            RuntimeError: If initialization fails
        """
        if self._initialized:
            logger.warning("[GCP] Clients already initialized, skipping...")
            return
        
        try:
            logger.info("[GCP] Initializing GCP clients...")
            
            # Create credentials from service account info
            credentials = service_account.Credentials.from_service_account_info(
                credentials_dict
            )
            
            # Initialize GCS client
            self._gcs_client = storage.Client(
                credentials=credentials,
                project=project_id
            )
            logger.info("[GCP] ✅ GCS Client initialized successfully")
            
            # Initialize Vision API client with explicit project
            self._vision_client = vision.ImageAnnotatorClient(
                credentials=credentials,
                client_options=ClientOptions(quota_project_id=project_id)
            )
            logger.info("[GCP] ✅ Vision API Client initialized successfully")
            
            self._initialized = True
            logger.info("[GCP] All GCP clients initialized successfully")
            
        except Exception as e:
            logger.error(f"[GCP] ❌ Failed to initialize GCP clients: {e}")
            raise RuntimeError(f"GCP initialization failed: {e}")
    
    def get_gcs_client(self) -> storage.Client:
        """
        Get the GCS client instance.
        
        Returns:
            storage.Client: The initialized GCS client
            
        Raises:
            RuntimeError: If client not initialized
        """
        if not self._initialized or self._gcs_client is None:
            raise RuntimeError(
                "GCS client not initialized. Call initialize() first during app startup."
            )
        return self._gcs_client
    
    def get_vision_client(self) -> vision.ImageAnnotatorClient:
        """
        Get the Vision API client instance.
        
        Returns:
            vision.ImageAnnotatorClient: The initialized Vision API client
            
        Raises:
            RuntimeError: If client not initialized
        """
        if not self._initialized or self._vision_client is None:
            raise RuntimeError(
                "Vision API client not initialized. Call initialize() first during app startup."
            )
        return self._vision_client
    
    def is_initialized(self) -> bool:
        """Check if clients are initialized."""
        return self._initialized
    
    def close(self) -> None:
        """Close all GCP clients and cleanup resources."""
        if self._gcs_client:
            self._gcs_client.close()
            logger.info("[GCP] GCS Client closed")
        
        # Vision client doesn't have a close method, but we clear the reference
        self._vision_client = None
        self._initialized = False
        logger.info("[GCP] All GCP clients closed")


# Global singleton instance
gcp_clients = GCPClients()


# Convenience functions for easy access
def get_gcs_client() -> storage.Client:
    """
    Get the GCS client.
    
    Returns:
        storage.Client: The initialized GCS client
        
    Raises:
        RuntimeError: If client not initialized
    """
    return gcp_clients.get_gcs_client()


def get_vision_client() -> vision.ImageAnnotatorClient:
    """
    Get the Vision API client.
    
    Returns:
        vision.ImageAnnotatorClient: The initialized Vision API client
        
    Raises:
        RuntimeError: If client not initialized
    """
    return gcp_clients.get_vision_client()


def initialize_gcp_clients() -> None:
    """
    Initialize GCP clients using configuration from environment.
    
    This should be called once at application startup.
    
    Raises:
        ValueError: If configuration is missing or invalid
        RuntimeError: If initialization fails
    """
    from utils.config import GCP_PROJECT_ID, get_gcp_credentials
    
    credentials_dict = get_gcp_credentials()
    gcp_clients.initialize(GCP_PROJECT_ID, credentials_dict)


def is_gcp_initialized() -> bool:
    """
    Check if GCP clients are initialized.
    
    Returns:
        bool: True if clients are initialized, False otherwise
    """
    return gcp_clients.is_initialized()
