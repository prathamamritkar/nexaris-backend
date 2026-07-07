from contextlib import asynccontextmanager
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
import secrets

from fastapi import FastAPI, HTTPException, File, UploadFile, Depends, Security, Header
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from neo4j import GraphDatabase, exceptions as neo4j_exceptions
from pydantic import BaseModel, Field, field_validator
import requests
import os

from config import settings
from nlp_engine import nlp
from validators import (
    validate_citizen_id,
    validate_location_context,
    validate_intent,
    validate_resource_type,
    validate_urgency,
    validate_audio_file,
    ValidationError,
)

# ==================== LOGGING SETUP ====================
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format=settings.LOG_FORMAT,
)
logger = logging.getLogger(__name__)

# ==================== DATABASE CONNECTION ====================
driver = None


def get_db_driver():
    """Get or create Neo4j driver with connection pooling"""
    global driver
    if driver is None:
        try:
            driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
                max_connection_pool_size=settings.NEO4J_CONNECTION_POOL_SIZE,
            )
            driver.verify_connectivity()
            logger.info("✅ Connected to Neo4j database")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Neo4j: {e}")
            raise

    return driver


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifecycle manager for startup and shutdown"""
    # Startup
    try:
        global driver
        driver = get_db_driver()

        if settings.PSA_ENABLED:
            logger.info("Starting Perpetual State Agent (PSA)...")
            asyncio.create_task(perpetual_state_agent_loop())
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down NEXARIS Engine...")
    if driver:
        driver.close()
        logger.info("Database connection closed")


# ==================== FASTAPI APP INITIALIZATION ====================
app = FastAPI(
    title="NEXARIS Topological Engine",
    version="2.0.0",
    description="Secure resource network orchestration platform",
    lifespan=lifespan,
)

# ==================== CORS CONFIGURATION (SECURE) ====================
# Only allow specific origins, not "*"
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

# ==================== SECURITY MIDDLEWARE ====================
@app.middleware("http")
async def add_security_headers(request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"

    return response


# ==================== REQUEST/RESPONSE MODELS ====================
class ResourceRequest(BaseModel):
    """Validated resource request model"""
    citizen_id: str = Field(..., min_length=3, max_length=64, description="Unique citizen identifier")
    intent: str = Field(..., description="Intent captured from voice/text")
    item: str = Field(..., description="Requested resource type")
    urgency: str = Field(..., description="Priority level")
    location_context: str = Field(..., description="Relevant location context")

    @field_validator("citizen_id", mode="before")
    @classmethod
    def validate_citizen_id_field(cls, v):
        return validate_citizen_id(v)

    @field_validator("intent", mode="before")
    @classmethod
    def validate_intent_field(cls, v):
        return validate_intent(v)

    @field_validator("item", mode="before")
    @classmethod
    def validate_item_field(cls, v):
        return validate_resource_type(v)

    @field_validator("urgency", mode="before")
    @classmethod
    def validate_urgency_field(cls, v):
        return validate_urgency(v)

    @field_validator("location_context", mode="before")
    @classmethod
    def validate_location_field(cls, v):
        return validate_location_context(v)


class SuccessResponse(BaseModel):
    """Standard success response"""
    status: str = "success"
    message: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ErrorResponse(BaseModel):
    """Standard error response (no internal details leaked)"""
    status: str = "error"
    message: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ==================== DATABASE UTILITIES ====================
def run_cypher(query: str, **parameters) -> Optional[list]:
    """
    Execute Cypher query with error handling
    Returns list of records or None on error
    """
    if driver is None:
        logger.error("Database driver not initialized")
        raise HTTPException(status_code=500, detail="Database connection unavailable")

    try:
        with driver.session() as session:
            result = session.run(query, **parameters)
            return [record.data() for record in result]
    except neo4j_exceptions.AuthError as e:
        logger.error(f"Database authentication failed: {e}")
        raise HTTPException(status_code=500, detail="Database authentication error")
    except neo4j_exceptions.ServiceUnavailable as e:
        logger.error(f"Database service unavailable: {e}")
        raise HTTPException(status_code=503, detail="Database service unavailable")
    except Exception as e:
        logger.error(f"Database query failed: {e}")
        raise HTTPException(status_code=500, detail="Database operation failed")


# ==================== CORE API ENDPOINTS ====================
def _ingest_to_db(req: ResourceRequest, created_by: str) -> None:
    query = """
    MERGE (c:Citizen {id: $citizen_id})
    MERGE (r:Resource {type: $item})
    MERGE (c)-[:NEEDS {
        intent: $intent,
        urgency: $urgency,
        location: $location_context,
        status: 'PENDING',
        timestamp: $timestamp,
        created_by: $created_by
    }]->(r)
    RETURN c.id as citizen_id, r.type as resource_type
    """
    run_cypher(
        query,
        citizen_id=req.citizen_id,
        intent=req.intent,
        item=req.item,
        urgency=req.urgency,
        location_context=req.location_context,
        timestamp=datetime.now(timezone.utc).isoformat(),
        created_by=created_by
    )

def _sweep_stale_requests() -> int:
    stale_cutoff = (datetime.now(timezone.utc) - timedelta(minutes=settings.PSA_STALE_THRESHOLD_MINUTES)).isoformat()
    sweep_query = """
    MATCH (c:Citizen)-[r:NEEDS]->(res:Resource)
    WHERE r.status = 'PENDING' AND r.timestamp < $stale_cutoff
    SET r.status = 'STALE',
        r.escalation_timestamp = $now,
        r.escalation_reason = 'Timeout: Request pending too long'
    RETURN count(r) AS stale_count
    """
    results = run_cypher(sweep_query, stale_cutoff=stale_cutoff, now=datetime.now(timezone.utc).isoformat())
    return results[0].get("stale_count", 0) if results else 0

@app.get("/")
def root():
    return {"name": "NEXARIS Topological Engine", "version": "2.0.0", "status": "operational", "docs": "/docs"}


@app.get("/health")
def health_check():
    """Health check endpoint"""
    try:
        if driver:
            driver.verify_connectivity()
        return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": "Database unavailable"}
        )


@app.post("/api/v1/ingest", response_model=SuccessResponse)
def ingest_resource_request(req: ResourceRequest):
    """
    Ingest a structured resource request into the topological network
    CRITICAL: Input validation happens via Pydantic validators
    """
    try:
        _ingest_to_db(req, created_by='ingest_api_v1')
        masked_citizen = f"{req.citizen_id[:2]}****{req.citizen_id[-2:]}" if len(req.citizen_id) > 4 else "****"
        logger.info(f"✅ Resource request ingested: citizen={masked_citizen}, item={req.item}, urgency={req.urgency}")

        return SuccessResponse(message="Resource request successfully mapped to topological network")

    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in ingest: {e}")
        raise HTTPException(status_code=500, detail="Request processing failed")


@app.post("/api/v1/migrate", response_model=SuccessResponse)
def migrate_relationships():
    """
    Migrate existing NEEDS relationships to add missing properties
    Use with caution in production
    """
    try:
        query = """
        MATCH (c:Citizen)-[n:NEEDS]->(r:Resource)
        WHERE n.urgency IS NULL OR n.status IS NULL
        SET n.urgency = coalesce(n.urgency, 'MEDIUM'),
            n.status = coalesce(n.status, 'PENDING'),
            n.migration_timestamp = $now
        RETURN count(n) AS updated_count
        """

        results = run_cypher(query, now=datetime.now(timezone.utc).isoformat())
        updated_count = results[0].get("updated_count", 0) if results else 0

        logger.info(f"Migration completed: {updated_count} relationships updated")

        return SuccessResponse(
            message=f"Migration complete. Updated {updated_count} relationships.",
        )
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise HTTPException(status_code=500, detail="Migration operation failed")


async def verify_admin_key(x_admin_key: str = Header(None)):
    admin_secret = os.getenv("ADMIN_SECRET_KEY")
    if not admin_secret:
        logger.error("ADMIN_SECRET_KEY is not configured in the environment.")
        raise HTTPException(status_code=500, detail="Server Configuration Error")
    if not x_admin_key or not secrets.compare_digest(x_admin_key, admin_secret):
        raise HTTPException(status_code=401, detail="Unauthorized Command Center Access")
    return x_admin_key

@app.get("/api/v1/graph-state")
def get_graph_state(admin_key: str = Depends(verify_admin_key)):
    """Retrieve current graph state (AUTHENTICATED)"""
    try:
        query = """
        MATCH (c:Citizen)-[n:NEEDS]->(r:Resource)
        RETURN c.id AS citizen, r.type AS resource,
               coalesce(n.urgency, 'UNKNOWN') AS urgency,
               coalesce(n.status, 'PENDING') AS status,
               coalesce(n.timestamp, 'N/A') AS request_time
        ORDER BY n.timestamp DESC
        LIMIT 1000
        """

        results = run_cypher(query)

        logger.debug(f"Graph state retrieved: {len(results)} relationships")

        return {
            "network_state": results,
            "total_records": len(results),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Graph state query failed: {e}")
        raise HTTPException(status_code=500, detail="Could not retrieve graph state")


# ==================== ADMIN ENDPOINTS ====================
api_key_header = APIKeyHeader(name="X-Cron-Signature", auto_error=True)

async def verify_cron_key(api_key: str = Security(api_key_header)):
    if not api_key or not secrets.compare_digest(api_key, settings.CRON_SECRET_KEY):
        raise HTTPException(status_code=403, detail="Invalid Cron Signature")
    return api_key

@app.post("/api/v1/admin/trigger-sweep", include_in_schema=False)
def manual_psa_sweep(api_key: str = Depends(verify_cron_key)):
    """
    Serverless endpoint to trigger the PSA sweep. 
    Hit this via GitHub Actions every 5 minutes.
    """
    try:
        stale_count = _sweep_stale_requests()
        return {"status": "success", "stale_records_updated": stale_count}
    except Exception as e:
        logger.error(f"Cron sweep failed: {e}")
        raise HTTPException(status_code=500, detail="Sweep failed")


@app.post("/api/v1/admin/dispatch")
def manual_dispatch(citizen_id: str, admin_key: str = Depends(verify_admin_key)):
    """Allows Base44 admins to manually force a dispatch"""
    query = """
    MATCH (c:Citizen {id: $citizen_id})-[r:NEEDS]->(res:Resource)
    SET r.status = 'DISPATCHED_BY_ADMIN'
    RETURN c.id
    """
    run_cypher(query, citizen_id=citizen_id)
    return {"status": "success"}

# ==================== BACKGROUND AGENT ====================
async def perpetual_state_agent_loop():
    """
    Perpetual State Agent (PSA): Background autonomic loop
    Monitors Neo4j for stale PENDING requests and escalates them
    SECURITY: Does NOT modify auth/permissions, only status tracking
    """
    logger.info("🤖 Perpetual State Agent started")

    while True:
        try:
            logger.info("PSA: Commencing graph topology sweep...")
            stale_count = _sweep_stale_requests()

            if stale_count > 0:
                logger.warning(f"⚠️  PSA Alert: {stale_count} requests marked STALE - escalation triggered")
            else:
                logger.debug("✅ PSA: All requests within normal parameters")

        except Exception as e:
            logger.error(f"❌ PSA Error: {e}")

        # Sleep before next cycle
        await asyncio.sleep(settings.PSA_POLLING_INTERVAL_SECONDS)


def _transcribe_audio(filename: str, audio_content: bytes, content_type: str) -> str:
    """Helper function to call Sarvam API for speech-to-text"""
    headers = {
        "api-subscription-key": settings.SARVAM_API_KEY,
        "User-Agent": "NEXARIS/2.0",
    }

    files = {"file": (filename, audio_content, content_type)}

    try:
        stt_response = requests.post(
            settings.SARVAM_AUDIO_API_URL,
            headers=headers,
            files=files,
            timeout=30,
        )

        if stt_response.status_code != 200:
            logger.error(f"Sarvam API error: {stt_response.status_code}")
            raise HTTPException(status_code=502, detail="Speech-to-text service error")

        transcript = stt_response.json().get("transcript", "").strip()

        if not transcript:
            raise HTTPException(status_code=400, detail="No speech detected in audio")

        logger.info(f"Transcription successful: {len(transcript)} characters")
        return transcript

    except requests.RequestException as e:
        logger.error(f"Sarvam API connection error: {e}")
        raise HTTPException(status_code=502, detail="Speech-to-text service unavailable")


@app.post("/api/v1/ingest/audio")
def process_vernacular_audio(file: UploadFile = File(...)):
    """
    Process audio file: transcribe via Sarvam AI and ingest into network
    """
    try:
        # Validate file before reading
        validate_audio_file(
            filename=file.filename or "",
            file_size=file.size or 0,
            content_type=file.content_type or "",
            max_size_bytes=settings.MAX_AUDIO_FILE_SIZE_BYTES,
            allowed_types=settings.ALLOWED_AUDIO_MIMETYPES,
        )

        # Read audio file with size limit
        audio_content = file.file.read()

        if len(audio_content) < 1024:
            raise ValidationError("Acoustic payload too small (likely dead-air or corrupted headers)")

        if len(audio_content) > settings.MAX_AUDIO_FILE_SIZE_BYTES:
            raise ValidationError("Audio file exceeds size limit")

        logger.info(f"Processing audio: {file.filename} ({len(audio_content)} bytes)")

        # Step 1: Call Sarvam API for speech-to-text via helper function
        transcript = _transcribe_audio(
            filename=file.filename or "",
            audio_content=audio_content,
            content_type=file.content_type or ""
        )

        # Step 2: Zero-Dependency Deterministic Entity Extraction
        # We process the Sarvam transcript using pure Python logic. No LLM APIs.
        # Instantaneous, free, and perfectly deterministic.

        extracted_entities = nlp.extract_entities(transcript)

        structured_payload = {
            "intent": "RESOURCE_REQUEST",
            "entities": extracted_entities
        }

        req = ResourceRequest(
            citizen_id=f"voice_node_{int(datetime.now(timezone.utc).timestamp())}",
            intent="RESOURCE_REQUEST",
            item=extracted_entities["item"],
            urgency=extracted_entities["urgency"],
            location_context=extracted_entities["location_context"]
        )

        # Step 3: Automatically ingest this into the Topological Graph (Neo4j)
        _ingest_to_db(req, created_by='v2v_audio_bridge')

        logger.info("Acoustic pipeline processed and mapped to T-Core successfully.")

        return {
            "status": "success",
            "message": "Audio processed and mapped to topological network",
            "structured_payload": structured_payload,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except ValidationError as e:
        logger.warning(f"Audio validation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Audio processing failed: {e}")
        raise HTTPException(status_code=500, detail="Audio processing failed")


@app.post("/api/v1/ingest/text")
def process_fallback_text(payload: dict):
    """
    Process manual text override: extract entities and ingest into network
    """
    try:
        text = payload.get("text", "").strip()
        if not text:
            raise HTTPException(status_code=400, detail="No text provided in request")
            
        logger.info(f"Processing text override (content redacted for privacy)")

        # Zero-Dependency Deterministic Entity Extraction
        extracted_entities = nlp.extract_entities(text)

        structured_payload = {
            "intent": "RESOURCE_REQUEST",
            "entities": extracted_entities
        }
        
        req = ResourceRequest(
            citizen_id=f"text_node_{int(datetime.now(timezone.utc).timestamp())}",
            intent="RESOURCE_REQUEST",
            item=extracted_entities["item"],
            urgency=extracted_entities["urgency"],
            location_context=extracted_entities["location_context"]
        )
        
        # Automatically ingest this into the Topological Graph
        _ingest_to_db(req, created_by='text_fallback_bridge')

        logger.info("Text pipeline processed and mapped to T-Core successfully.")

        return {
            "status": "success",
            "message": "Text processed and mapped to topological network",
            "structured_payload": structured_payload,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except ValidationError as e:
        logger.warning(f"Text validation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Text processing failed: {e}")
        raise HTTPException(status_code=500, detail="Text processing failed")


# ==================== ERROR HANDLERS ====================
@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc):
    """Handle validation errors securely"""
    return JSONResponse(
        status_code=400,
        content={"status": "error", "message": str(exc), "timestamp": datetime.now(timezone.utc).isoformat()},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Generic error handler - DO NOT expose internal details"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "An unexpected error occurred. Please try again later.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
