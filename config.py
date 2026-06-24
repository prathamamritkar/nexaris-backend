"""
Centralized configuration management for NEXARIS Backend
Enforces secure defaults and environment-based overrides
"""
import os
from typing import Optional
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class Settings:
    """Application configuration with security-first design"""

    # ==================== DATABASE ====================
    NEO4J_URI: str = os.getenv("NEO4J_URI", "").strip()
    NEO4J_USER: str = os.getenv("NEO4J_USER", "").strip()
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "").strip()
    NEO4J_CONNECTION_POOL_SIZE: int = int(os.getenv("NEO4J_CONNECTION_POOL_SIZE", "50"))

    # Validate database configuration
    if not all([NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD]):
        raise ValueError(
            "Missing required environment variables: NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD"
        )

    if NEO4J_PASSWORD == "password":
        logger.warning(
            "⚠️ WARNING: Using default Neo4j password. This is insecure in production."
        )

    # ==================== API KEYS ====================
    SARVAM_API_KEY: str = os.getenv("SARVAM_API_KEY", "").strip()
    if not SARVAM_API_KEY:
        raise ValueError("SARVAM_API_KEY environment variable is required")

    # ==================== SECURITY ====================
    # CORS: Restrict to specific origins
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    CORS_ALLOW_CREDENTIALS: bool = os.getenv("CORS_ALLOW_CREDENTIALS", "false").lower() == "true"

    # API Rate limiting
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW_SECONDS: int = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))

    # ==================== AUDIO PROCESSING ====================
    MAX_AUDIO_FILE_SIZE_MB: int = int(os.getenv("MAX_AUDIO_FILE_SIZE_MB", "10"))
    MAX_AUDIO_FILE_SIZE_BYTES: int = MAX_AUDIO_FILE_SIZE_MB * 1024 * 1024
    ALLOWED_AUDIO_MIMETYPES: list = ["audio/mpeg", "audio/wav", "audio/ogg", "audio/flac", "audio/mp4"]
    SARVAM_AUDIO_API_URL: str = os.getenv(
        "SARVAM_AUDIO_API_URL", "https://api.sarvam.ai/speech-to-text"
    )

    # ==================== BACKGROUND AGENT ====================
    PSA_POLLING_INTERVAL_SECONDS: int = int(os.getenv("PSA_POLLING_INTERVAL_SECONDS", "30"))
    PSA_STALE_THRESHOLD_MINUTES: int = int(os.getenv("PSA_STALE_THRESHOLD_MINUTES", "5"))
    PSA_ENABLED: bool = os.getenv("PSA_ENABLED", "true").lower() == "true"

    # ==================== LOGGING ====================
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # ==================== VALIDATION CONSTRAINTS ====================
    CITIZEN_ID_MIN_LENGTH: int = 3
    CITIZEN_ID_MAX_LENGTH: int = 64
    LOCATION_CONTEXT_MAX_LENGTH: int = 500
    INTENT_MAX_LENGTH: int = 200
    RESOURCE_TYPE_MAX_LENGTH: int = 100

    @classmethod
    def validate_all(cls) -> bool:
        """Validates all critical configuration"""
        required_keys = ["NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", "SARVAM_API_KEY"]
        missing = [key for key in required_keys if not os.getenv(key)]

        if missing:
            logger.error(f"Missing critical environment variables: {', '.join(missing)}")
            return False

        if len(cls.CORS_ORIGINS) == 0:
            logger.error("CORS_ORIGINS must contain at least one origin")
            return False

        return True


# Export singleton instance
settings = Settings()
