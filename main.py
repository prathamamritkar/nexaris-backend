from contextlib import asynccontextmanager
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from neo4j import GraphDatabase
from pydantic import BaseModel, Field


NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

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


@app.post("/api/v1/ingest")
async def ingest_resource_request(req: ResourceRequest):
    query = """
    MERGE (c:Citizen {id: $citizen_id})
    MERGE (r:Resource {type: $item})
    MERGE (c)-[:NEEDS {
        intent: $intent,
        urgency: $urgency,
        location: $location_context,
        status: 'PENDING'
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
        )
        return {
            "status": "success",
            "message": "Acoustic-to-Topological Mapping Complete",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/graph-state")
async def get_graph_state():
    query = """
    MATCH (c:Citizen)-[n:NEEDS]->(r:Resource)
    RETURN c.id AS citizen, r.type AS resource, n.urgency AS urgency, n.status AS status
    """
    try:
        record_data = run_cypher(query)
        results = [record.data() for record in record_data]
        return {"network_state": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
