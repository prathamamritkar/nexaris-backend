"""
Secure input validation and sanitization utilities
"""
import re
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

# Pre-compute control characters translation table for validation
# Removes all ASCII control chars (0-31) except \t (9), \n (10), \r (13)
_CONTROL_CHARS_TO_REMOVE = "".join(chr(i) for i in range(32) if i not in (9, 10, 13))
_CONTROL_CHARS_TABLE = str.maketrans("", "", _CONTROL_CHARS_TO_REMOVE)


class ValidationError(Exception):
    """Custom exception for validation failures"""
    pass


def validate_citizen_id(citizen_id: str, min_length: int = 3, max_length: int = 64) -> str:
    """
    Validate citizen_id: alphanumeric, underscore, hyphen only
    Prevents injection attacks and data corruption
    """
    if not citizen_id or not isinstance(citizen_id, str):
        raise ValidationError("citizen_id must be a non-empty string")

    citizen_id = citizen_id.strip()

    if len(citizen_id) < min_length or len(citizen_id) > max_length:
        raise ValidationError(
            f"citizen_id length must be between {min_length} and {max_length}"
        )

    # Allow alphanumeric, underscore, hyphen only
    if not re.match(r"^[a-zA-Z0-9_-]+$", citizen_id):
        raise ValidationError(
            "citizen_id can only contain alphanumeric characters, underscores, and hyphens"
        )

    return citizen_id


def validate_location_context(location: str, max_length: int = 500) -> str:
    """
    Validate location_context: basic string sanitization
    """
    if not location or not isinstance(location, str):
        raise ValidationError("location_context must be a non-empty string")

    location = location.strip()

    if len(location) > max_length:
        raise ValidationError(f"location_context must be under {max_length} characters")

    # Remove any control characters
    location = location.translate(_CONTROL_CHARS_TABLE)

    return location


def validate_intent(intent: str, max_length: int = 200) -> str:
    """Validate intent value"""
    if not intent or not isinstance(intent, str):
        raise ValidationError("intent must be a non-empty string")

    intent = intent.strip().upper()

    if len(intent) > max_length:
        raise ValidationError(f"intent must be under {max_length} characters")

    # Allow only word characters and underscores
    if not re.match(r"^[A-Z_]+$", intent):
        raise ValidationError("intent can only contain uppercase letters and underscores")

    return intent


def validate_resource_type(resource_type: str, max_length: int = 100) -> str:
    """Validate resource_type from predefined list or format"""
    if not resource_type or not isinstance(resource_type, str):
        raise ValidationError("resource_type must be a non-empty string")

    resource_type = resource_type.strip()

    if len(resource_type) > max_length:
        raise ValidationError(f"resource_type must be under {max_length} characters")

    # Allow alphanumeric, spaces, hyphens, and underscores for readability and UNKNOWN_RESOURCE flags
    if not re.match(r"^[a-zA-Z0-9\s_-]+$", resource_type):
        raise ValidationError(
            "resource_type can only contain letters, numbers, spaces, hyphens, and underscores"
        )

    return resource_type


def validate_urgency(urgency: str) -> str:
    """Validate urgency from predefined set"""
    allowed_values = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"]

    if not urgency or not isinstance(urgency, str):
        raise ValidationError("urgency must be a non-empty string")

    urgency = urgency.upper().strip()

    if urgency not in allowed_values:
        raise ValidationError(f"urgency must be one of: {', '.join(allowed_values)}")

    return urgency


def validate_audio_file(
    filename: str, file_size: int, content_type: str, max_size_bytes: int, allowed_types: List[str]
) -> bool:
    """
    Validate audio file for upload
    Returns True if valid, raises ValidationError otherwise
    """
    if not filename:
        raise ValidationError("filename cannot be empty")

    # Check file size
    if file_size > max_size_bytes:
        max_mb = max_size_bytes / (1024 * 1024)
        raise ValidationError(f"audio file must be smaller than {max_mb}MB")

    # Check MIME type
    if content_type not in allowed_types:
        raise ValidationError(
            f"audio file type must be one of: {', '.join(allowed_types)}"
        )

    # Check filename extension matches MIME type
    allowed_extensions = {
        "audio/mpeg": [".mp3"],
        "audio/wav": [".wav"],
        "audio/ogg": [".ogg", ".oga"],
        "audio/flac": [".flac"],
        "audio/mp4": [".m4a", ".mp4"],
    }

    file_ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if content_type in allowed_extensions:
        if file_ext not in allowed_extensions[content_type]:
            raise ValidationError(f"filename extension must match content type")

    return True
