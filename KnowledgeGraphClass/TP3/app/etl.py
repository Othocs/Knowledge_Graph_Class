#!/usr/bin/env python3
"""
ETL Script for TP3 - Neo4j Twitter Network Analysis
Loads Twitter data from CSV files into Neo4j database
"""

import os
import time
from neo4j import GraphDatabase
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TwitterETL:
    """ETL class for loading Twitter data into Neo4j"""

    def __init__(self, uri: str, user: str, password: str):
        """Initialize Neo4j connection"""
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        logger.info(f"Connected to Neo4j at {uri}")

    def close(self):
        """Close Neo4j connection"""
        self.driver.close()
        logger.info("Closed Neo4j connection")

    def wait_for_neo4j(self, max_retries: int = 30, retry_delay: int = 2):
        """Wait for Neo4j to be ready"""
        for attempt in range(max_retries):
            try:
                with self.driver.session() as session:
                    session.run("RETURN 1")
                logger.info("Neo4j is ready!")
                return True
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}/{max_retries}: Neo4j not ready yet - {e}")
                time.sleep(retry_delay)

        raise Exception("Neo4j failed to become ready")

    def clear_database(self):
        """Clear all nodes and relationships from the database"""
        with self.driver.session() as session:
            logger.info("Clearing database...")
            session.run("MATCH (n) DETACH DELETE n")
            logger.info("Database cleared")

    def create_constraints(self):
        """Create unique constraints for User and Tweet nodes"""
        with self.driver.session() as session:
            logger.info("Creating constraints...")

            # User constraint
            session.run("""
                CREATE CONSTRAINT user_id_unique IF NOT EXISTS
                FOR (u:User) REQUIRE u.id IS UNIQUE
            """)
            logger.info("Created constraint: user_id_unique")

            # Tweet constraint
            session.run("""
                CREATE CONSTRAINT tweet_id_unique IF NOT EXISTS
                FOR (t:Tweet) REQUIRE t.id IS UNIQUE
            """)
            logger.info("Created constraint: tweet_id_unique")

    def create_indexes(self):
        """Create indexes for better query performance"""
        with self.driver.session() as session:
            logger.info("Creating indexes...")

            # Username index
            session.run("""
                CREATE INDEX user_username_idx IF NOT EXISTS
                FOR (u:User) ON (u.username)
            """)
            logger.info("Created index: user_username_idx")

            # Tweet createdAt index
            session.run("""
                CREATE INDEX tweet_created_at_idx IF NOT EXISTS
                FOR (t:Tweet) ON (t.createdAt)
            """)
            logger.info("Created index: tweet_created_at_idx")

    def load_users(self):
        """Load User nodes from CSV"""
        with self.driver.session() as session:
            logger.info("Loading users...")
            result = session.run("""
                LOAD CSV WITH HEADERS FROM 'file:///users.csv' AS row
                CREATE (u:User {
                    id: toInteger(row.id),
                    name: row.name,
                    username: row.username,
                    registeredAt: date(row.registeredAt)
                })
                RETURN count(u) AS count
            """)
            count = result.single()["count"]
            logger.info(f"Loaded {count} users")

    def load_followers(self):
        """Load FOLLOWS relationships from CSV"""
        with self.driver.session() as session:
            logger.info("Loading follower relationships...")
            result = session.run("""
                LOAD CSV WITH HEADERS FROM 'file:///followers.csv' AS row
                MATCH (source:User {id: toInteger(row.sourceId)})
                MATCH (target:User {id: toInteger(row.targetId)})
                CREATE (source)-[:FOLLOWS]->(target)
                RETURN count(*) AS count
            """)
            count = result.single()["count"]
            logger.info(f"Loaded {count} follower relationships")

    def load_tweets(self):
        """Load Tweet nodes from CSV"""
        with self.driver.session() as session:
            logger.info("Loading tweets...")
            result = session.run("""
                LOAD CSV WITH HEADERS FROM 'file:///tweets.csv' AS row
                CREATE (t:Tweet {
                    id: toInteger(row.id),
                    text: row.text,
                    createdAt: datetime(row.createdAt)
                })
                RETURN count(t) AS count
            """)
            count = result.single()["count"]
            logger.info(f"Loaded {count} tweets")

    def load_publish_relationships(self):
        """Connect tweets to their authors"""
        with self.driver.session() as session:
            logger.info("Loading PUBLISH relationships...")
            result = session.run("""
                LOAD CSV WITH HEADERS FROM 'file:///tweets.csv' AS row
                MATCH (u:User {id: toInteger(row.authorId)})
                MATCH (t:Tweet {id: toInteger(row.id)})
                CREATE (u)-[:PUBLISH]->(t)
                RETURN count(*) AS count
            """)
            count = result.single()["count"]
            logger.info(f"Loaded {count} PUBLISH relationships")

    def load_retweets(self):
        """Load RETWEETS relationships"""
        with self.driver.session() as session:
            logger.info("Loading RETWEETS relationships...")
            result = session.run("""
                LOAD CSV WITH HEADERS FROM 'file:///tweet_relationships.csv' AS row
                WITH row
                WHERE row.type = 'RETWEET' AND row.sourceId IS NOT NULL AND row.targetId IS NOT NULL
                MATCH (source:Tweet {id: toInteger(row.sourceId)})
                MATCH (target:Tweet {id: toInteger(row.targetId)})
                CREATE (source)-[:RETWEETS]->(target)
                RETURN count(*) AS count
            """)
            count = result.single()["count"]
            logger.info(f"Loaded {count} RETWEETS relationships")

    def load_replies(self):
        """Load IN_REPLY_TO relationships"""
        with self.driver.session() as session:
            logger.info("Loading IN_REPLY_TO relationships...")
            result = session.run("""
                LOAD CSV WITH HEADERS FROM 'file:///tweet_relationships.csv' AS row
                WITH row
                WHERE row.type = 'REPLY' AND row.sourceId IS NOT NULL AND row.targetId IS NOT NULL
                MATCH (source:Tweet {id: toInteger(row.sourceId)})
                MATCH (target:Tweet {id: toInteger(row.targetId)})
                CREATE (source)-[:IN_REPLY_TO]->(target)
                RETURN count(*) AS count
            """)
            count = result.single()["count"]
            logger.info(f"Loaded {count} IN_REPLY_TO relationships")

    def load_mentions(self):
        """Load MENTIONS relationships"""
        with self.driver.session() as session:
            logger.info("Loading MENTIONS relationships...")
            result = session.run("""
                LOAD CSV WITH HEADERS FROM 'file:///tweet_relationships.csv' AS row
                WITH row
                WHERE row.type = 'MENTION' AND row.sourceId IS NOT NULL AND row.mentionedUserId IS NOT NULL
                MATCH (tweet:Tweet {id: toInteger(row.sourceId)})
                MATCH (user:User {id: toInteger(row.mentionedUserId)})
                CREATE (tweet)-[:MENTIONS]->(user)
                RETURN count(*) AS count
            """)
            count = result.single()["count"]
            logger.info(f"Loaded {count} MENTIONS relationships")

    def get_statistics(self):
        """Get and display database statistics"""
        with self.driver.session() as session:
            logger.info("\n" + "="*50)
            logger.info("DATABASE STATISTICS")
            logger.info("="*50)

            # Count nodes
            result = session.run("MATCH (u:User) RETURN count(u) AS count")
            user_count = result.single()["count"]
            logger.info(f"Users: {user_count}")

            result = session.run("MATCH (t:Tweet) RETURN count(t) AS count")
            tweet_count = result.single()["count"]
            logger.info(f"Tweets: {tweet_count}")

            # Count relationships
            result = session.run("MATCH ()-[r:FOLLOWS]->() RETURN count(r) AS count")
            follows_count = result.single()["count"]
            logger.info(f"FOLLOWS relationships: {follows_count}")

            result = session.run("MATCH ()-[r:PUBLISH]->() RETURN count(r) AS count")
            publish_count = result.single()["count"]
            logger.info(f"PUBLISH relationships: {publish_count}")

            result = session.run("MATCH ()-[r:RETWEETS]->() RETURN count(r) AS count")
            retweets_count = result.single()["count"]
            logger.info(f"RETWEETS relationships: {retweets_count}")

            result = session.run("MATCH ()-[r:IN_REPLY_TO]->() RETURN count(r) AS count")
            replies_count = result.single()["count"]
            logger.info(f"IN_REPLY_TO relationships: {replies_count}")

            result = session.run("MATCH ()-[r:MENTIONS]->() RETURN count(r) AS count")
            mentions_count = result.single()["count"]
            logger.info(f"MENTIONS relationships: {mentions_count}")

            logger.info("="*50 + "\n")

    def run_etl(self):
        """Run the complete ETL process"""
        try:
            logger.info("Starting ETL process...")

            # Wait for Neo4j to be ready
            self.wait_for_neo4j()

            # Clear existing data
            self.clear_database()

            # Create schema
            self.create_constraints()
            self.create_indexes()

            # Load data
            self.load_users()
            self.load_followers()
            self.load_tweets()
            self.load_publish_relationships()
            self.load_retweets()
            self.load_replies()
            self.load_mentions()

            # Display statistics
            self.get_statistics()

            logger.info("ETL process completed successfully!")

        except Exception as e:
            logger.error(f"ETL process failed: {e}")
            raise
        finally:
            self.close()


def main():
    """Main function"""
    # Get connection details from environment variables
    uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password123")

    # Run ETL
    etl = TwitterETL(uri, user, password)
    etl.run_etl()


if __name__ == "__main__":
    main()
