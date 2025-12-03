#!/usr/bin/env python3
"""
TP5 - Knowledge Graph RAG Data Loading Script

This script:
1. Fetches Wikipedia articles about specified topics
2. Uses Diffbot API to extract entities and relationships
3. Creates a knowledge graph in Neo4j
4. Validates the loaded data
"""

import os
import sys
import time
import json
import requests
from typing import List, Dict, Any
from neo4j import GraphDatabase
from dotenv import load_dotenv
import wikipediaapi

# Load environment variables
load_dotenv()

# Configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")
DIFFBOT_API_KEY = os.getenv("DIFFBOT_API_KEY", "")
WIKIPEDIA_TOPICS = os.getenv("WIKIPEDIA_TOPICS", "Albert Einstein,Marie Curie").split(",")

# Initialize Wikipedia API
wiki_wiki = wikipediaapi.Wikipedia(
    user_agent='TP5-KnowledgeGraph/1.0 (educational purposes)',
    language='en'
)


class KnowledgeGraphETL:
    """ETL pipeline for building knowledge graph from Wikipedia articles"""

    def __init__(self, uri: str, user: str, password: str):
        """Initialize Neo4j connection"""
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            # Test connection
            with self.driver.session() as session:
                result = session.run("RETURN 1 AS test")
                result.single()
            print(f"✓ Connected to Neo4j at {uri}")
        except Exception as e:
            print(f"✗ Failed to connect to Neo4j: {e}")
            sys.exit(1)

    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
            print("✓ Neo4j connection closed")

    def create_schema(self):
        """Create constraints and indexes for the knowledge graph"""
        print("\n📐 Creating Neo4j schema...")

        constraints_and_indexes = [
            # Constraints for uniqueness
            "CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE",
            "CREATE CONSTRAINT person_name IF NOT EXISTS FOR (p:Person) REQUIRE p.name IS UNIQUE",
            "CREATE CONSTRAINT organization_name IF NOT EXISTS FOR (o:Organization) REQUIRE o.name IS UNIQUE",
            "CREATE CONSTRAINT location_name IF NOT EXISTS FOR (l:Location) REQUIRE l.name IS UNIQUE",

            # Indexes for performance
            "CREATE INDEX entity_type IF NOT EXISTS FOR (e:Entity) ON (e.type)",
            "CREATE INDEX entity_name IF NOT EXISTS FOR (e:Entity) ON (e.name)",
        ]

        with self.driver.session() as session:
            for query in constraints_and_indexes:
                try:
                    session.run(query)
                    print(f"  ✓ {query.split()[1]}")
                except Exception as e:
                    print(f"  ⚠ {query.split()[1]}: {str(e)[:50]}")

        print("✓ Schema created successfully")

    def fetch_wikipedia_article(self, title: str) -> Dict[str, str]:
        """Fetch Wikipedia article content"""
        print(f"\n📚 Fetching Wikipedia article: {title}")

        page = wiki_wiki.page(title.strip())

        if not page.exists():
            print(f"  ✗ Article '{title}' not found")
            return None

        print(f"  ✓ Fetched article: {page.title}")
        print(f"  ℹ Length: {len(page.text)} characters")

        return {
            "title": page.title,
            "url": page.fullurl,
            "text": page.text,
            "summary": page.summary
        }

    def extract_entities_with_diffbot(self, text: str, url: str) -> Dict[str, Any]:
        """Extract entities and relationships using Diffbot API"""
        print(f"\n🔍 Extracting entities with Diffbot...")

        if not DIFFBOT_API_KEY or DIFFBOT_API_KEY == "your_diffbot_api_key_here":
            print("  ⚠ Diffbot API key not configured. Using mock data.")
            return self._create_mock_entities(text)

        try:
            # Diffbot Natural Language API endpoint
            api_url = f"https://nl.diffbot.com/v1/?token={DIFFBOT_API_KEY}&content={requests.utils.quote(text[:5000])}"

            response = requests.get(api_url, timeout=30)
            response.raise_for_status()

            data = response.json()
            print(f"  ✓ Extracted {len(data.get('entities', []))} entities")

            return data

        except Exception as e:
            print(f"  ✗ Diffbot extraction failed: {e}")
            print("  ℹ Using mock data instead")
            return self._create_mock_entities(text)

    def _create_mock_entities(self, text: str) -> Dict[str, Any]:
        """Create mock entities for testing when Diffbot is not available"""
        # Simple entity extraction based on capitalized words (very basic)
        import re

        # Find capitalized phrases (potential entities)
        entities = []
        entity_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        matches = re.findall(entity_pattern, text[:2000])

        # Take unique matches and create mock entities
        unique_entities = list(set(matches))[:20]  # Limit to 20 entities

        for i, entity_name in enumerate(unique_entities):
            entities.append({
                "name": entity_name,
                "type": "Person" if i % 3 == 0 else ("Organization" if i % 3 == 1 else "Location"),
                "salience": 0.5,
            })

        print(f"  ✓ Created {len(entities)} mock entities")

        return {"entities": entities, "facts": []}

    def load_entities_to_neo4j(self, article: Dict[str, str], entities_data: Dict[str, Any]):
        """Load extracted entities and relationships into Neo4j"""
        print(f"\n💾 Loading entities to Neo4j...")

        entities = entities_data.get("entities", [])

        if not entities:
            print("  ⚠ No entities to load")
            return

        with self.driver.session() as session:
            # Create Article node
            session.run("""
                MERGE (a:Article {title: $title})
                SET a.url = $url,
                    a.summary = $summary,
                    a.loaded_at = datetime()
            """, title=article["title"], url=article["url"], summary=article["summary"][:500])

            print(f"  ✓ Created Article node: {article['title']}")

            # Load entities
            entity_count = 0
            for entity in entities:
                entity_name = entity.get("name", "Unknown")
                entity_type = entity.get("type", "Entity")
                salience = entity.get("salience", 0.0)

                # Create entity with dynamic label
                session.run(f"""
                    MERGE (e:Entity {{name: $name}})
                    SET e:{entity_type},
                        e.type = $type,
                        e.salience = $salience
                """, name=entity_name, type=entity_type, salience=salience)

                # Create relationship to article
                session.run("""
                    MATCH (a:Article {title: $article_title})
                    MATCH (e:Entity {name: $entity_name})
                    MERGE (a)-[r:MENTIONS]->(e)
                    SET r.salience = $salience
                """, article_title=article["title"], entity_name=entity_name, salience=salience)

                entity_count += 1

            print(f"  ✓ Loaded {entity_count} entities")

            # Load relationships (if available)
            facts = entities_data.get("facts", [])
            if facts:
                rel_count = 0
                for fact in facts[:50]:  # Limit relationships
                    # This would process Diffbot facts into relationships
                    # Implementation depends on Diffbot response structure
                    pass
                print(f"  ✓ Created {rel_count} relationships")

    def print_statistics(self):
        """Print database statistics"""
        print("\n📊 Database Statistics:")

        queries = {
            "Articles": "MATCH (a:Article) RETURN count(a) as count",
            "Entities": "MATCH (e:Entity) RETURN count(e) as count",
            "People": "MATCH (p:Person) RETURN count(p) as count",
            "Organizations": "MATCH (o:Organization) RETURN count(o) as count",
            "Locations": "MATCH (l:Location) RETURN count(l) as count",
            "Relationships": "MATCH ()-[r]->() RETURN count(r) as count",
        }

        with self.driver.session() as session:
            for label, query in queries.items():
                result = session.run(query)
                count = result.single()["count"]
                print(f"  • {label}: {count}")

    def run_etl(self, topics: List[str]):
        """Execute the full ETL pipeline"""
        print("=" * 60)
        print("🚀 Starting Knowledge Graph ETL Pipeline")
        print("=" * 60)

        try:
            # Step 1: Create schema
            self.create_schema()

            # Step 2: Process each Wikipedia topic
            for topic in topics:
                # Fetch Wikipedia article
                article = self.fetch_wikipedia_article(topic)
                if not article:
                    continue

                # Extract entities
                entities_data = self.extract_entities_with_diffbot(
                    article["text"],
                    article["url"]
                )

                # Load to Neo4j
                self.load_entities_to_neo4j(article, entities_data)

                # Brief pause to be respectful of APIs
                time.sleep(1)

            # Step 3: Print statistics
            self.print_statistics()

            print("\n" + "=" * 60)
            print("✅ ETL Pipeline completed successfully!")
            print("=" * 60)

            return True

        except Exception as e:
            print(f"\n❌ ETL Pipeline failed: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main entry point"""
    print("\n🔧 Configuration:")
    print(f"  • Neo4j URI: {NEO4J_URI}")
    print(f"  • Topics: {', '.join(WIKIPEDIA_TOPICS)}")
    print(f"  • Diffbot API Key: {'✓ Configured' if DIFFBOT_API_KEY and DIFFBOT_API_KEY != 'your_diffbot_api_key_here' else '✗ Not configured (using mock data)'}")

    etl = KnowledgeGraphETL(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    try:
        success = etl.run_etl(WIKIPEDIA_TOPICS)
        sys.exit(0 if success else 1)
    finally:
        etl.close()


if __name__ == "__main__":
    main()
