import os
import time
import psycopg2
from neo4j import GraphDatabase
import pandas as pd
from pathlib import Path


# Database connection parameters
POSTGRES_CONFIG = {
    "host": os.getenv("POSTGRES_HOST"),
    "port": os.getenv("POSTGRES_PORT"),
    "database": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD")
}

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")


def wait_for_postgres(max_retries=30, delay=2):
    """
    Waits for PostgreSQL to be ready.
    """
    for i in range(max_retries):
        try:
            conn = psycopg2.connect(**POSTGRES_CONFIG)
            conn.close()
            print("✓ PostgreSQL is ready")
            return
        except psycopg2.OperationalError:
            if i < max_retries - 1:
                print(f"Waiting for PostgreSQL... ({i+1}/{max_retries})")
                time.sleep(delay)
            else:
                raise Exception("PostgreSQL did not become ready in time")


def wait_for_neo4j(max_retries=30, delay=2):
    """
    Waits for Neo4j to be ready.
    """
    for i in range(max_retries):
        try:
            driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
            with driver.session() as session:
                session.run("RETURN 1")
            driver.close()
            print("✓ Neo4j is ready")
            return
        except Exception:
            if i < max_retries - 1:
                print(f"Waiting for Neo4j... ({i+1}/{max_retries})")
                time.sleep(delay)
            else:
                raise Exception("Neo4j did not become ready in time")


def run_cypher(driver, query, parameters=None):
    """
    Executes a single Cypher query.
    """
    with driver.session() as session:
        result = session.run(query, parameters or {})
        return list(result)


def run_cypher_file(driver, file_path):
    """
    Executes multiple Cypher statements from a file.
    Statements are separated by semicolons.
    """
    with open(file_path, 'r') as f:
        content = f.read()

    # Split by semicolon and filter out empty statements
    statements = [stmt.strip() for stmt in content.split(';') if stmt.strip()]

    for statement in statements:
        print(f"Executing: {statement[:60]}...")
        run_cypher(driver, statement)


def chunk(dataframe, size=1000):
    """
    Splits a DataFrame into chunks of specified size for batch processing.
    """
    for i in range(0, len(dataframe), size):
        yield dataframe.iloc[i:i + size]


def etl():
    """
    Main ETL function that migrates data from PostgreSQL to Neo4j.

    This function performs the complete Extract, Transform, Load process:
    1. Waits for both databases to be ready
    2. Sets up Neo4j schema using queries.cypher file
    3. Extracts data from PostgreSQL tables
    4. Transforms relational data into graph format
    5. Loads data into Neo4j with appropriate relationships

    The process creates the following graph structure:
    - Category nodes with name properties
    - Product nodes linked to categories via IN_CATEGORY relationships
    - Customer nodes with name and join_date properties
    - Order nodes linked to customers via PLACED relationships
    - Order-Product relationships via CONTAINS with quantity properties
    - Dynamic event relationships between customers and products
    """
    # Ensure dependencies are ready (useful when running in docker-compose)
    wait_for_postgres()
    wait_for_neo4j()

    # Get path to Cypher schema file
    queries_path = Path(__file__).with_name("queries.cypher")

    # TODO: Implement the ETL logic here
    # 1. Connect to Neo4j
    # 2. Run schema setup from queries.cypher
    # 3. Connect to PostgreSQL and extract data
    # 4. Load data into Neo4j in the correct order:
    #    - Categories
    #    - Products (with IN_CATEGORY relationships)
    #    - Customers
    #    - Orders (with PLACED relationships)
    #    - Order items (with CONTAINS relationships)
    #    - Events (with dynamic relationship types)

    pass
    #  code here


if __name__ == "__main__":
    etl()
    print("ETL done.")
