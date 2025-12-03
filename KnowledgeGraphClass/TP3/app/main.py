#!/usr/bin/env python3
"""
FastAPI Application for TP3 - Neo4j Twitter Network Analysis
Provides REST API endpoints to query the Twitter network graph
"""

import os
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from neo4j import GraphDatabase
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="TP3 Twitter Network Analysis API",
    description="REST API for querying Twitter network data stored in Neo4j",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Neo4j connection
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


def execute_query(query: str, parameters: Dict = None) -> List[Dict[str, Any]]:
    """Execute a Cypher query and return results"""
    try:
        with driver.session() as session:
            result = session.run(query, parameters or {})
            return [dict(record) for record in result]
    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("shutdown")
def shutdown_event():
    """Close Neo4j connection on shutdown"""
    driver.close()
    logger.info("Neo4j connection closed")


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "TP3 Twitter Network Analysis API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "stats": "/stats",
            "users": "/users/random",
            "tweets": "/tweets/distribution",
            "top_users": "/users/top-followed",
            "pagerank": "/analysis/pagerank",
            "communities": "/analysis/communities"
        }
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    try:
        with driver.session() as session:
            session.run("RETURN 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Database unavailable")


@app.get("/stats")
def get_statistics():
    """Get database statistics"""
    queries = {
        "users": "MATCH (u:User) RETURN count(u) AS count",
        "tweets": "MATCH (t:Tweet) RETURN count(t) AS count",
        "follows": "MATCH ()-[r:FOLLOWS]->() RETURN count(r) AS count",
        "retweets": "MATCH ()-[r:RETWEETS]->() RETURN count(r) AS count",
        "mentions": "MATCH ()-[r:MENTIONS]->() RETURN count(r) AS count",
        "replies": "MATCH ()-[r:IN_REPLY_TO]->() RETURN count(r) AS count"
    }

    stats = {}
    for key, query in queries.items():
        result = execute_query(query)
        stats[key] = result[0]["count"] if result else 0

    return stats


@app.get("/users/random")
def get_random_users(limit: int = 5):
    """Get random users (Q1)"""
    query = """
        MATCH (u:User)
        RETURN u.id AS id, u.name AS name, u.username AS username,
               u.registeredAt AS registeredAt
        ORDER BY rand()
        LIMIT $limit
    """
    return execute_query(query, {"limit": limit})


@app.get("/users/top-followed")
def get_top_followed_users(limit: int = 10):
    """Get most followed users (Q13)"""
    query = """
        MATCH (u:User)<-[:FOLLOWS]-(follower:User)
        WITH u, count(follower) AS followerCount
        RETURN u.id AS id, u.name AS name, u.username AS username, followerCount
        ORDER BY followerCount DESC
        LIMIT $limit
    """
    return execute_query(query, {"limit": limit})


@app.get("/users/top-following")
def get_top_following_users(limit: int = 10):
    """Get users who follow the most people (Q14)"""
    query = """
        MATCH (u:User)-[:FOLLOWS]->(following:User)
        WITH u, count(following) AS followingCount
        RETURN u.id AS id, u.name AS name, u.username AS username, followingCount
        ORDER BY followingCount DESC
        LIMIT $limit
    """
    return execute_query(query, {"limit": limit})


@app.get("/users/most-mentioned")
def get_most_mentioned_users(limit: int = 10):
    """Get most mentioned users (Q12)"""
    query = """
        MATCH (u:User)<-[:MENTIONS]-(t:Tweet)
        WITH u, count(t) AS mentionCount
        RETURN u.id AS id, u.name AS name, u.username AS username, mentionCount
        ORDER BY mentionCount DESC
        LIMIT $limit
    """
    return execute_query(query, {"limit": limit})


@app.get("/users/mentioned-no-tweets")
def get_mentioned_users_without_tweets():
    """Get users who were mentioned but never published (Q10)"""
    query = """
        MATCH (u:User)
        WHERE (u)<-[:MENTIONS]-() AND NOT (u)-[:PUBLISH]->()
        RETURN u.id AS id, u.name AS name, u.username AS username,
               count{(u)<-[:MENTIONS]-()} AS mentionCount
        ORDER BY mentionCount DESC
    """
    return execute_query(query)


@app.get("/users/mutual-follows")
def get_mutual_follows(limit: int = 20):
    """Get users with mutual follows (Q15)"""
    query = """
        MATCH (u1:User)-[:FOLLOWS]->(u2:User)-[:FOLLOWS]->(u1)
        RETURN u1.username AS user1, u2.username AS user2
        ORDER BY user1, user2
        LIMIT $limit
    """
    return execute_query(query, {"limit": limit})


@app.get("/tweets/distribution")
def get_tweet_distribution():
    """Get tweet creation distribution by year (Q7)"""
    query = """
        MATCH (t:Tweet)
        RETURN date.truncate('year', t.createdAt) AS year, count(t) AS tweetCount
        ORDER BY year
    """
    return execute_query(query)


@app.get("/tweets/most-active-days")
def get_most_active_days(limit: int = 5):
    """Get most active tweet creation days (Q9)"""
    query = """
        MATCH (t:Tweet)
        WITH date.truncate('day', t.createdAt) AS day, count(t) AS tweetCount
        RETURN day, tweetCount
        ORDER BY tweetCount DESC, day DESC
        LIMIT $limit
    """
    return execute_query(query, {"limit": limit})


@app.get("/tweets/year/{year}")
def get_tweets_by_year(year: int, limit: int = 10):
    """Filter tweets by year (Q8)"""
    query = """
        MATCH (t:Tweet)
        WHERE date.truncate('year', t.createdAt) = date($year)
        RETURN t.id AS id, t.text AS text, t.createdAt AS createdAt
        ORDER BY t.createdAt
        LIMIT $limit
    """
    return execute_query(query, {"year": f"{year}-01-01", "limit": limit})


@app.get("/tweets/top-retweeted")
def get_top_retweeted_users(limit: int = 5):
    """Get users whose tweets are most retweeted (Q11)"""
    query = """
        MATCH (u:User)-[:PUBLISH]->(t:Tweet)<-[:RETWEETS]-(rt:Tweet)
        WITH u, count(rt) AS retweetCount
        RETURN u.id AS id, u.name AS name, u.username AS username, retweetCount
        ORDER BY retweetCount DESC
        LIMIT $limit
    """
    return execute_query(query, {"limit": limit})


@app.get("/tweets/stats")
def get_tweet_stats():
    """Get tweet statistics including original vs retweets (Q6)"""
    query = """
        MATCH (t:Tweet)
        WHERE NOT (t)-[:RETWEETS]->()
        WITH count(t) AS originalTweets
        MATCH (rt:Tweet)-[:RETWEETS]->()
        WITH originalTweets, count(rt) AS retweets
        RETURN originalTweets, retweets, originalTweets + retweets AS total
    """
    result = execute_query(query)

    # Average tweets per user
    avg_query = """
        MATCH (u:User)-[:PUBLISH]->(t:Tweet)
        WITH u, count(t) AS tweetCount
        RETURN avg(tweetCount) AS avgTweetsPerUser,
               min(tweetCount) AS minTweets,
               max(tweetCount) AS maxTweets
    """
    avg_result = execute_query(avg_query)

    return {
        "original_vs_retweets": result[0] if result else {},
        "user_stats": avg_result[0] if avg_result else {}
    }


@app.get("/analysis/pagerank")
def get_pagerank_analysis(limit: int = 10):
    """Run PageRank analysis to find influential users"""
    # First create the graph projection if it doesn't exist
    try:
        execute_query("""
            CALL gds.graph.exists('userNetwork')
            YIELD exists
            WHERE NOT exists
            CALL gds.graph.project('userNetwork', 'User', 'FOLLOWS', {})
            RETURN exists
        """)
    except:
        pass

    query = """
        CALL gds.pageRank.stream('userNetwork')
        YIELD nodeId, score
        RETURN gds.util.asNode(nodeId).username AS username,
               gds.util.asNode(nodeId).name AS name,
               score
        ORDER BY score DESC
        LIMIT $limit
    """
    return execute_query(query, {"limit": limit})


@app.get("/analysis/betweenness")
def get_betweenness_centrality(limit: int = 10):
    """Find bridge users using betweenness centrality"""
    # Ensure graph projection exists
    try:
        execute_query("""
            CALL gds.graph.exists('userNetwork')
            YIELD exists
            WHERE NOT exists
            CALL gds.graph.project('userNetwork', 'User', 'FOLLOWS', {})
            RETURN exists
        """)
    except:
        pass

    query = """
        CALL gds.betweenness.stream('userNetwork')
        YIELD nodeId, score
        RETURN gds.util.asNode(nodeId).username AS username,
               gds.util.asNode(nodeId).name AS name,
               score
        ORDER BY score DESC
        LIMIT $limit
    """
    return execute_query(query, {"limit": limit})


@app.get("/analysis/communities")
def get_communities():
    """Detect communities using Louvain algorithm"""
    # Ensure graph projection exists
    try:
        execute_query("""
            CALL gds.graph.exists('userNetwork')
            YIELD exists
            WHERE NOT exists
            CALL gds.graph.project('userNetwork', 'User', 'FOLLOWS', {})
            RETURN exists
        """)
    except:
        pass

    query = """
        CALL gds.louvain.stream('userNetwork')
        YIELD nodeId, communityId
        RETURN communityId,
               collect(gds.util.asNode(nodeId).username) AS members,
               count(*) AS memberCount
        ORDER BY memberCount DESC
    """
    return execute_query(query)


@app.get("/analysis/triangles")
def get_triangle_count(limit: int = 10):
    """Count triangles to measure network cohesion"""
    # Ensure graph projection exists
    try:
        execute_query("""
            CALL gds.graph.exists('userNetwork')
            YIELD exists
            WHERE NOT exists
            CALL gds.graph.project('userNetwork', 'User', 'FOLLOWS', {})
            RETURN exists
        """)
    except:
        pass

    query = """
        CALL gds.triangleCount.stream('userNetwork')
        YIELD nodeId, triangleCount
        RETURN gds.util.asNode(nodeId).username AS username,
               triangleCount
        ORDER BY triangleCount DESC
        LIMIT $limit
    """
    return execute_query(query, {"limit": limit})


@app.get("/analysis/shortest-path")
def get_shortest_path(source: str, target: str):
    """Find shortest path between two users"""
    query = """
        MATCH (source:User {username: $source})
        MATCH (target:User {username: $target})
        MATCH path = shortestPath((source)-[:FOLLOWS*]-(target))
        RETURN [node IN nodes(path) | node.username] AS pathNodes,
               length(path) AS pathLength
    """
    return execute_query(query, {"source": source, "target": target})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
