import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# gemini API configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")  # Default if not specified


# Model configuration constants
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 8192  # Increased to support full multi-tool agentic workflows

# GCP Configuration
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "claimwise-claims")
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_CREDENTIALS_PATH = os.getenv("GCP_CREDENTIALS_PATH")  # File path to JSON credentials

def get_gcp_credentials() -> dict:
    """
    Load GCP credentials from JSON file.
    Handles both relative and absolute paths.
    
    Returns:
        dict: GCP service account credentials
        
    Raises:
        ValueError: If credentials path is missing or file is invalid
        FileNotFoundError: If credentials file doesn't exist
    """
    if not GCP_CREDENTIALS_PATH:
        raise ValueError("GCP_CREDENTIALS_PATH is required in environment variables")
    
    # Convert to absolute path if relative
    credentials_path = GCP_CREDENTIALS_PATH
    if not os.path.isabs(credentials_path):
        # If path starts with 'backend/', remove it since we're already in backend
        if credentials_path.startswith('backend/') or credentials_path.startswith('backend\\'):
            credentials_path = credentials_path.replace('backend/', '').replace('backend\\', '')
        
        # Get the directory where this config file is located (backend/utils/)
        config_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up one level to backend/ directory
        backend_dir = os.path.dirname(config_dir)
        credentials_path = os.path.join(backend_dir, credentials_path)
    
    if not os.path.isfile(credentials_path):
        raise FileNotFoundError(
            f"GCP credentials file not found: {credentials_path} (original: {GCP_CREDENTIALS_PATH})"
        )
    
    try:
        with open(credentials_path, 'r') as f:
            credentials_dict = json.load(f)
        
        # Validate required fields
        required_fields = ["type", "project_id", "private_key", "client_email"]
        missing_fields = [field for field in required_fields if field not in credentials_dict]
        if missing_fields:
            raise ValueError(
                f"Missing required fields in GCP credentials: {missing_fields}"
            )
        
        return credentials_dict
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in GCP credentials file: {e}")
    except Exception as e:
        raise ValueError(f"Error loading GCP credentials: {e}")

# Database configuration - unified for both local and Cloud SQL
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST", "localhost")  # Used only for local
DB_PORT = int(os.getenv("DB_PORT", "5432"))  # Used only for local

# Cloud SQL configuration (if present, Cloud SQL is used)
CLOUD_SQL_CONNECTION_NAME = os.getenv("CLOUD_SQL_CONNECTION_NAME")
USE_PRIVATE_IP = os.getenv("USE_PRIVATE_IP", "false").lower() == "true"

# Connection pool settings
DB_POOL_MIN = int(os.getenv("DB_POOL_MIN", "5"))
DB_POOL_MAX = int(os.getenv("DB_POOL_MAX", "20"))

# FastAPI Configuration
API_HOST = os.getenv("API_HOST", "localhost")
API_PORT = int(os.getenv("API_PORT", "8000"))
RELOAD = os.getenv("RELOAD", "false").lower() == "true"
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
FRONTEND_URL = os.getenv("FRONTEND_URL", ALLOWED_ORIGINS[0] if ALLOWED_ORIGINS else "http://localhost:8080")

# Backend URL for OAuth callbacks
BACKEND_URL = os.getenv("BACKEND_URL", f"http://{API_HOST}:{API_PORT}")

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_OAUTH_TOKEN_URL = os.getenv("GOOGLE_OAUTH_TOKEN_URL", "https://oauth2.googleapis.com/token")

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "change-this-in-production-please-use-a-secure-random-string")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_DAYS = int(os.getenv("JWT_EXPIRATION_DAYS", "7"))

def get_cors_config() -> dict:
    """
    Get CORS configuration.
    
    Returns:
        dict: CORS configuration for FastAPI middleware
    """
    return {
        "allow_origins": ALLOWED_ORIGINS,
        "allow_credentials": True,
        "allow_methods": ["*"],
        "allow_headers": ["*"],
    }

# ============================================================================
# METRICS VALIDATION CONFIGURATION
# ============================================================================

# Model information
METRICS_MODEL_NAME = os.getenv("METRICS_MODEL_NAME", "Claims Agent")
METRICS_MODEL_VERSION = os.getenv("METRICS_MODEL_VERSION", "5.2")

# Metric weights for health score calculation (must sum to 1.0)
METRICS_WEIGHTS = {
    "straight_through_rate": float(os.getenv("WEIGHT_STR", "0.25")),
    "error_rate_on_approved_claims": float(os.getenv("WEIGHT_ERROR_RATE", "0.20")),
    "time_to_adjudication_reduction": float(os.getenv("WEIGHT_TIME_REDUCTION", "0.20")),
    "claim_denial_rate": float(os.getenv("WEIGHT_DENIAL_RATE", "0.10")),
    "compliance_dashboard_accuracy": float(os.getenv("WEIGHT_COMPLIANCE", "0.15")),
    "integration_accuracy": float(os.getenv("WEIGHT_INTEGRATION", "0.05")),
    "processing_latency": float(os.getenv("WEIGHT_LATENCY", "0.05"))
}

# Recommendation thresholds
METRICS_THRESHOLDS = {
    "str_threshold": float(os.getenv("THRESHOLD_STR", "70")),
    "str_excellent": float(os.getenv("THRESHOLD_STR_EXCELLENT", "90")),
    "error_threshold": float(os.getenv("THRESHOLD_ERROR_RATE", "10")),
    "denial_threshold_high": float(os.getenv("THRESHOLD_DENIAL_HIGH", "20")),
    "denial_threshold_low": float(os.getenv("THRESHOLD_DENIAL_LOW", "5")),
    "latency_threshold_high": float(os.getenv("THRESHOLD_LATENCY_HIGH", "300")),
    "latency_threshold_low": float(os.getenv("THRESHOLD_LATENCY_LOW", "30"))
}

# Time calculation multiplier (manual processing time vs automated)
METRICS_MANUAL_TIME_MULTIPLIER = float(os.getenv("MANUAL_TIME_MULTIPLIER", "2.0"))

# Version history status
METRICS_STATUS = os.getenv("METRICS_STATUS", "production")
