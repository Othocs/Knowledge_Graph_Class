#!/usr/bin/env python3
"""
TP4 - Twitch Stream Data ETL Script

This script loads Twitch stream data into Neo4j:
1. Reads CSV files from Neo4j import directory
2. Creates constraints and indexes
3. Loads Stream nodes with their properties
4. Creates SHARED_AUDIENCE relationships (undirected)
"""

import os
import sys
from pathlib import Path
from neo4j import GraphDatabase
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")

# CSV file paths in import directory (mounted to Jupyter container)
IMPORT_DIR = Path("/data/import")
STREAMS_CSV = IMPORT_DIR / "twitch_streamer.csv"
RELATIONSHIPS_CSV = IMPORT_DIR / "relationship.csv"


class TwitchETL:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        print(f"✓ Connected to Neo4j at {uri}")

    def close(self):
        self.driver.close()
        print("✓ Closed Neo4j connection")

    def run_query(self, query, parameters=None):
        """Execute a Cypher query"""
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return list(result)

    def check_csv_files(self):
        """Check if CSV files exist"""
        print("\nChecking for CSV files...")

        if not STREAMS_CSV.exists():
            raise FileNotFoundError(f"Streams CSV not found: {STREAMS_CSV}")
        if not RELATIONSHIPS_CSV.exists():
            raise FileNotFoundError(f"Relationships CSV not found: {RELATIONSHIPS_CSV}")

        print(f"✓ Found {STREAMS_CSV.name}")
        print(f"✓ Found {RELATIONSHIPS_CSV.name}")

    def create_schema(self):
        """Create constraints and indexes"""
        print("\nCreating schema...")

        queries = [
            # Unique constraint for Stream nodes
            """
            CREATE CONSTRAINT stream_id_unique IF NOT EXISTS
            FOR (s:Stream) REQUIRE s.id IS UNIQUE
            """,
            # Index on language for filtering
            """
            CREATE INDEX stream_language_idx IF NOT EXISTS
            FOR (s:Stream) ON (s.language)
            """,
            # Index on gameId for analysis
            """
            CREATE INDEX stream_game_idx IF NOT EXISTS
            FOR (s:Stream) ON (s.gameId)
            """
        ]

        for query in queries:
            self.run_query(query)

        print("✓ Schema created")

    def load_streams(self, filepath):
        """Load Stream nodes from CSV"""
        print("\nLoading Stream nodes...")

        df = pd.read_csv(filepath)
        print(f"  Found {len(df)} streams")
        print(f"  Columns: {list(df.columns)}")

        query = """
        UNWIND $streams AS stream
        CREATE (s:Stream {
            id: stream.id,
            language: stream.language
        })
        """

        streams = df.to_dict('records')
        self.run_query(query, {"streams": streams})

        print(f"✓ Loaded {len(df)} Stream nodes")

    def load_shared_audience(self, filepath):
        """Load SHARED_AUDIENCE relationships"""
        print("\nLoading SHARED_AUDIENCE relationships...")

        df = pd.read_csv(filepath)
        print(f"  Found {len(df)} shared audience connections")
        print(f"  Columns: {list(df.columns)}")

        query = """
        UNWIND $relationships AS rel
        MATCH (s1:Stream {id: rel.source})
        MATCH (s2:Stream {id: rel.target})
        CREATE (s1)-[:SHARED_AUDIENCE {weight: rel.weight}]->(s2)
        CREATE (s2)-[:SHARED_AUDIENCE {weight: rel.weight}]->(s1)
        """

        relationships = df.to_dict('records')
        self.run_query(query, {"relationships": relationships})

        print(f"✓ Loaded {len(df) * 2} SHARED_AUDIENCE relationships (bidirectional)")

    def print_stats(self):
        """Print database statistics"""
        print("\n" + "="*50)
        print("DATABASE STATISTICS")
        print("="*50)

        # Count nodes
        result = self.run_query("MATCH (s:Stream) RETURN count(s) AS streamCount")
        print(f"Stream nodes: {result[0]['streamCount']}")

        # Count relationships
        result = self.run_query(
            "MATCH ()-[r:SHARED_AUDIENCE]->() RETURN count(r) AS relCount"
        )
        print(f"SHARED_AUDIENCE relationships: {result[0]['relCount']}")

        # Language distribution
        result = self.run_query("""
            MATCH (s:Stream)
            RETURN s.language AS language, count(s) AS count
            ORDER BY count DESC
        """)
        print("\nLanguage distribution:")
        for row in result[:10]:
            print(f"  {row['language']}: {row['count']}")

        # Average degree
        result = self.run_query("""
            MATCH (s:Stream)
            WITH s, count{(s)-[:SHARED_AUDIENCE]-()} AS degree
            RETURN avg(degree) AS avgDegree, max(degree) AS maxDegree
        """)
        print(f"\nAverage degree: {result[0]['avgDegree']:.2f}")
        print(f"Max degree: {result[0]['maxDegree']}")

        print("="*50)

    def run_etl(self):
        """Execute full ETL pipeline"""
        try:
            # Check if CSV files exist
            self.check_csv_files()

            # Create schema
            self.create_schema()

            # Load data
            self.load_streams(STREAMS_CSV)
            self.load_shared_audience(RELATIONSHIPS_CSV)

            # Print statistics
            self.print_stats()

            print("\n✓ ETL pipeline completed successfully!")
            return True

        except Exception as e:
            print(f"\n✗ Error during ETL: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    print("="*50)
    print("TP4 - Twitch Stream Data ETL")
    print("="*50)

    etl = TwitchETL(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    try:
        success = etl.run_etl()
        sys.exit(0 if success else 1)
    finally:
        etl.close()


if __name__ == "__main__":
    main()
