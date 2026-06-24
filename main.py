from contextlib import asynccontextmanager
import asyncio
import os
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from neo4j import GraphDatabase
from pydantic import BaseModel, Field
import requests
import json


NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "your_key_here")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        yield
    finally:
        driver.close()


# Initialize the NEXARIS Engine
app = FastAPI(title="NEXARIS Topological Engine", lifespan=lifespan)

# Allow Base44 and your Frontend to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ResourceRequest(BaseModel):
    citizen_id: str = Field(..., description="Unique citizen identifier")
    intent: str = Field(..., description="Intent captured from the voice bridge")
    item: str = Field(..., description="Requested resource type")
    urgency: str = Field(..., description="Priority assigned to the request")
    location_context: str = Field(..., description="Relevant location context")


def run_cypher(query: str, **parameters):
    with driver.session() as session:
        return session.run(query, **parameters)


# Configuration for Temporal-Resilient Execution (TRE)
POLLING_INTERVAL_SECONDS = 30
STALE_THRESHOLD_MINUTES = 5


@app.post("/api/v1/ingest")
async def ingest_resource_request(req: ResourceRequest):
    query = """
    MERGE (c:Citizen {id: $citizen_id})
    MERGE (r:Resource {type: $item})
    MERGE (c)-[:NEEDS {
        intent: $intent,
        urgency: $urgency,
        location: $location_context,
        status: 'PENDING',
        timestamp: $timestamp
    }]->(r)
    RETURN c, r
    """
    try:
        run_cypher(
            query,
            citizen_id=req.citizen_id,
            intent=req.intent,
            item=req.item,
            urgency=req.urgency,
            location_context=req.location_context,
            timestamp=datetime.now().isoformat(),
        )
        return {
            "status": "success",
            "message": "Acoustic-to-Topological Mapping Complete",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/migrate")
async def migrate_relationships():
    """Migrate existing NEEDS relationships to add missing properties"""
    query = """
    MATCH (c:Citizen)-[n:NEEDS]->(r:Resource)
    SET n.urgency = coalesce(n.urgency, 'MEDIUM'),
        n.status = coalesce(n.status, 'PENDING')
    RETURN count(n) AS updated_count
    """
    try:
        result = run_cypher(query)
        record = result.single()
        updated_count = record["updated_count"] if record else 0
        return {
            "status": "success",
            "message": f"Migration complete. Updated {updated_count} relationships.",
            "updated_count": updated_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/graph-state")
async def get_graph_state():
    query = """
    MATCH (c:Citizen)-[n:NEEDS]->(r:Resource)
    RETURN c.id AS citizen, r.type AS resource, coalesce(n.urgency, 'UNKNOWN') AS urgency, coalesce(n.status, 'PENDING') AS status
    """
    try:
        record_data = run_cypher(query)
        results = [record.data() for record in record_data]
        return {"network_state": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def perpetual_state_agent_loop():
    """
    The autonomic loop that runs indefinitely in the background of your server.
    It protects the system from data stagnation and unacknowledged states.
    Continuously sweeps the Neo4j graph for stale PENDING requests and marks them
    as STALE to trigger alternative pathfinding and escalation protocols.
    """
    while True:
        try:
            print(f"[{datetime.now()}] PSA Engine: Commencing graph topology sweep...")

            # Calculate the stale timestamp threshold
            stale_cutoff = (datetime.now() - timedelta(minutes=STALE_THRESHOLD_MINUTES)).isoformat()

            # Cypher query to find requests that have been PENDING too long
            sweep_query = """
            MATCH (c:Citizen)-[r:NEEDS]->(res:Resource)
            WHERE r.status = "PENDING" AND r.timestamp < $stale_cutoff
            SET r.status = "STALE", r.escalation_timestamp = $now
            RETURN count(r) AS stale_count
            """

            result = run_cypher(sweep_query, stale_cutoff=stale_cutoff, now=datetime.now().isoformat())
            record = result.single()

            if record:
                stale_count = record["stale_count"]
                if stale_count > 0:
                    print(f"[{datetime.now()}] PSA Alert: Detected {stale_count} stagnant requests. Topological states shifted to STALE.")
                else:
                    print(f"[{datetime.now()}] PSA Engine: Sweep clean. All active edges within normal parameters.")

        except Exception as e:
            print(f"[{datetime.now()}] PSA Critical Error: Background thread failed to query T-Core: {e}")

        # Put the agent to sleep before the next autonomic heartbeat
        await asyncio.sleep(POLLING_INTERVAL_SECONDS)


@app.post("/api/v1/ingest/audio")
async def process_vernacular_audio(file: UploadFile = File(...)):
    """
    Step 1: The Acoustic-to-Text translation via Sarvam AI
    Accepts raw audio files, transcribes them, and routes to entity extraction.
    """
    sarvam_url = "https://api.sarvam.ai/speech-to-text"
    headers = {"api-subscription-key": SARVAM_API_KEY}

    # Read the audio bytes and ship to Sarvam
    audio_content = await file.read()
    files = {"file": (file.filename, audio_content, file.content_type)}

    try:
        stt_response = requests.post(sarvam_url, headers=headers, files=files)
        if stt_response.status_code != 200:
            return {"error": "Sarvam API rejection", "details": stt_response.text}

        transcript = stt_response.json().get("transcript", "")

        # Step 2: The Intent Extraction Pipeline
        # In production, pipe 'transcript' to an LLM with strict JSON formatting instructions.
        # Simulated Structured Output:
        structured_payload = {
            "intent": "RESOURCE_REQUEST",
            "entities": {
                "item": "Insulin",
                "urgency": "High",
                "location_context": "Extracted from transcript string",
                "raw_text": transcript
            }
        }

        # Step 3: Inject the structured data into the Neo4j T-Core
        query = """
        MERGE (c:Citizen {id: $citizen_id})
        MERGE (r:Resource {type: $item})
        MERGE (c)-[:NEEDS {
            intent: $intent,
            urgency: $urgency,
            location: $location_context,
            status: 'PENDING',
            timestamp: $timestamp,
            transcript: $transcript
        }]->(r)
        RETURN c, r
        """

        run_cypher(
            query,
            citizen_id="citizen_audio_" + str(int(datetime.now().timestamp())),
            intent=structured_payload["intent"],
            item=structured_payload["entities"]["item"],
            urgency=structured_payload["entities"]["urgency"],
            location_context=structured_payload["entities"]["location_context"],
            timestamp=datetime.now().isoformat(),
            transcript=transcript,
        )

        return {"status": "success", "topological_mapping": structured_payload}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio processing failed: {str(e)}")


@app.on_event("startup")
async def start_background_agents():
    """
    Hooks into FastAPI's lifecycle to trigger the background agent
    the exact millisecond the web server boots up on Render.
    """
    asyncio.create_task(perpetual_state_agent_loop())
