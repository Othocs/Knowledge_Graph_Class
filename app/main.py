from fastapi import FastAPI
from neo4j import GraphDatabase
import os

app = FastAPI(title="E-Commerce Graph Recommendations API")

# Neo4j connection
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")


@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify API and Neo4j connectivity.
    Returns {"ok": true} if everything is working.
    """
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        with driver.session() as session:
            result = session.run("RETURN 1 AS num")
            record = result.single()
            if record and record["num"] == 1:
                driver.close()
                return {"ok": True}
        driver.close()
        return {"ok": False}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/")
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "service": "E-Commerce Graph Recommendations",
        "version": "1.0.0",
        "endpoints": {
            "/health": "Health check",
            "/": "API info"
        }
    }
