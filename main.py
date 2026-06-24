from contextlib import asynccontextmanager
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, HTTPException, File, UploadFile, Depends, Security
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from neo4j import GraphDatabase, exceptions as neo4j_exceptions
from pydantic import BaseModel, Field, validator
import requests
import os

from config import settings
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
                connection_pool_size=settings.NEO4J_CONNECTION_POOL_SIZE,
                encrypted=True,
                trust="TRUST_SYSTEM_CA_SIGNED_CERTIFICATES",
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

    @validator("citizen_id")
    def validate_citizen_id_field(cls, v):
        return validate_citizen_id(v)

    @validator("intent")
    def validate_intent_field(cls, v):
        return validate_intent(v)

    @validator("item")
    def validate_item_field(cls, v):
        return validate_resource_type(v)

    @validator("urgency")
    def validate_urgency_field(cls, v):
        return validate_urgency(v)

    @validator("location_context")
    def validate_location_field(cls, v):
        return validate_location_context(v)


class SuccessResponse(BaseModel):
    """Standard success response"""
    status: str = "success"
    message: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ErrorResponse(BaseModel):
    """Standard error response (no internal details leaked)"""
    status: str = "error"
    message: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


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
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        if driver:
            driver.verify_connectivity()
        return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": "Database unavailable"}
        )


@app.post("/api/v1/ingest", response_model=SuccessResponse)
async def ingest_resource_request(req: ResourceRequest):
    """
    Ingest a structured resource request into the topological network
    CRITICAL: Input validation happens via Pydantic validators
    """
    try:
        query = """
        MERGE (c:Citizen {id: $citizen_id})
        MERGE (r:Resource {type: $item})
        MERGE (c)-[:NEEDS {
            intent: $intent,
            urgency: $urgency,
            location: $location_context,
            status: 'PENDING',
            timestamp: $timestamp,
            created_by: 'ingest_api_v1'
        }]->(r)
        RETURN c.id as citizen_id, r.type as resource_type
        """

        results = run_cypher(
            query,
            citizen_id=req.citizen_id,
            intent=req.intent,
            item=req.item,
            urgency=req.urgency,
            location_context=req.location_context,
            timestamp=datetime.utcnow().isoformat(),
        )

        logger.info(f"✅ Resource request ingested: citizen={req.citizen_id}, item={req.item}, urgency={req.urgency}")

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
async def migrate_relationships():
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

        results = run_cypher(query, now=datetime.utcnow().isoformat())
        updated_count = results[0].get("updated_count", 0) if results else 0

        logger.info(f"Migration completed: {updated_count} relationships updated")

        return SuccessResponse(
            message=f"Migration complete. Updated {updated_count} relationships.",
        )
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise HTTPException(status_code=500, detail="Migration operation failed")


@app.get("/api/v1/graph-state")
async def get_graph_state():
    """
    Retrieve current graph state (AUTHENTICATED ONLY IN PRODUCTION)
    TODO: Add authentication/authorization
    """
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
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Graph state query failed: {e}")
        raise HTTPException(status_code=500, detail="Could not retrieve graph state")


# ==================== ADMIN ENDPOINTS ====================
CRON_SECRET_KEY = os.getenv("CRON_SECRET_KEY", "generate_a_long_random_string_here")
api_key_header = APIKeyHeader(name="X-Cron-Signature", auto_error=True)

async def verify_cron_key(api_key: str = Security(api_key_header)):
    if api_key != CRON_SECRET_KEY:
        raise HTTPException(status_code=403, detail="Invalid Cron Signature")
    return api_key

@app.post("/api/v1/admin/trigger-sweep", include_in_schema=False)
async def manual_psa_sweep(api_key: str = Depends(verify_cron_key)):
    """
    Serverless endpoint to trigger the PSA sweep. 
    Hit this via GitHub Actions every 5 minutes.
    """
    try:
        stale_cutoff = (datetime.utcnow() - timedelta(minutes=settings.PSA_STALE_THRESHOLD_MINUTES)).isoformat()
        
        sweep_query = """
        MATCH (c:Citizen)-[r:NEEDS]->(res:Resource)
        WHERE r.status = 'PENDING' AND r.timestamp < $stale_cutoff
        SET r.status = 'STALE',
            r.escalation_timestamp = $now,
            r.escalation_reason = 'Timeout: Request pending too long'
        RETURN count(r) AS stale_count
        """
        
        results = run_cypher(sweep_query, stale_cutoff=stale_cutoff, now=datetime.utcnow().isoformat())
        stale_count = results[0].get("stale_count", 0) if results else 0
        
        return {"status": "success", "stale_records_updated": stale_count}
    except Exception as e:
        logger.error(f"Cron sweep failed: {e}")
        raise HTTPException(status_code=500, detail="Sweep failed")

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

            # Calculate stale cutoff with UTC timezone
            stale_cutoff = (
                datetime.utcnow() - timedelta(minutes=settings.PSA_STALE_THRESHOLD_MINUTES)
            ).isoformat()

            # Query for stale PENDING requests
            sweep_query = """
            MATCH (c:Citizen)-[r:NEEDS]->(res:Resource)
            WHERE r.status = 'PENDING' AND r.timestamp < $stale_cutoff
            SET r.status = 'STALE',
                r.escalation_timestamp = $now,
                r.escalation_reason = 'Timeout: Request pending too long'
            RETURN count(r) AS stale_count
            """

            results = run_cypher(
                sweep_query,
                stale_cutoff=stale_cutoff,
                now=datetime.utcnow().isoformat(),
            )

            if results:
                stale_count = results[0].get("stale_count", 0)
                if stale_count > 0:
                    logger.warning(f"⚠️  PSA Alert: {stale_count} requests marked STALE - escalation triggered")
                else:
                    logger.debug("✅ PSA: All requests within normal parameters")

        except Exception as e:
            logger.error(f"❌ PSA Error: {e}")

        # Sleep before next cycle
        await asyncio.sleep(settings.PSA_POLLING_INTERVAL_SECONDS)


@app.post("/api/v1/ingest/audio")
async def process_vernacular_audio(file: UploadFile = File(...)):
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
        audio_content = await file.read()

        if len(audio_content) > settings.MAX_AUDIO_FILE_SIZE_BYTES:
            raise ValidationError("Audio file exceeds size limit")

        logger.info(f"Processing audio: {file.filename} ({len(audio_content)} bytes)")

        # Step 1: Call Sarvam API for speech-to-text
        headers = {
            "api-subscription-key": settings.SARVAM_API_KEY,
            "User-Agent": "NEXARIS/2.0",
        }

        files = {"file": (file.filename, audio_content, file.content_type)}

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

            # Step 2: Structure output (TODO: add LLM-based entity extraction)
            structured_payload = {
                "intent": "RESOURCE_REQUEST",
                "entities": {
                    "item": "Pending_LLM_Extraction",
                    "urgency": "HIGH",
                    "location_context": "Pending_LLM_Extraction",
                    "transcript_preview": transcript[:100] + "..." if len(transcript) > 100 else transcript,
                }
            }

            # Step 3: Log but don't store raw transcript (privacy)
            logger.debug("Audio processing pipeline complete")

            return {
                "status": "success",
                "message": "Audio processed and queued for entity extraction",
                "structured_payload": structured_payload,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except requests.RequestException as e:
            logger.error(f"Sarvam API connection error: {e}")
            raise HTTPException(status_code=502, detail="Speech-to-text service unavailable")

    except ValidationError as e:
        logger.warning(f"Audio validation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Audio processing failed: {e}")
        raise HTTPException(status_code=500, detail="Audio processing failed")


# ==================== ERROR HANDLERS ====================
@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc):
    """Handle validation errors securely"""
    return JSONResponse(
        status_code=400,
        content={"status": "error", "message": str(exc), "timestamp": datetime.utcnow().isoformat()},
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
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


# ==================== STARTUP VERIFICATION ====================
@app.on_event("startup")
async def startup_event():
    """Verify configuration and database on startup"""
    logger.info("🚀 NEXARIS Engine starting up...")

    if not settings.validate_all():
        logger.error("Configuration validation failed")
        raise RuntimeError("Invalid configuration")

    logger.info("✅ Configuration validated")
