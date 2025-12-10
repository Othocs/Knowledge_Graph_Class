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
    for i in range(max_retries):
        try:
            conn = psycopg2.connect(**POSTGRES_CONFIG)
            conn.close()
            return
        except psycopg2.OperationalError:
            if i < max_retries - 1:
                time.sleep(delay)
            else:
                raise Exception("PostgreSQL did not become ready in time")


def wait_for_neo4j(max_retries=30, delay=2):
    for i in range(max_retries):
        try:
            driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
            with driver.session() as session:
                session.run("RETURN 1")
            driver.close()
            return
        except Exception:
            if i < max_retries - 1:
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

    statements = [stmt.strip() for stmt in content.split(';') if stmt.strip()]

    for statement in statements:
        run_cypher(driver, statement)


def chunk(dataframe, size=1000):
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
    wait_for_postgres()
    wait_for_neo4j()

    queries_path = Path(__file__).with_name("queries.cypher")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    try:
        print("Setting up Neo4j schema (constraints and indexes)...")
        run_cypher_file(driver, queries_path)
        print("Schema setup complete")

        print("Connecting to PostgreSQL and extracting data...")
        pg_conn = psycopg2.connect(**POSTGRES_CONFIG)
        categories_df = pd.read_sql("SELECT * FROM categories", pg_conn)
        products_df = pd.read_sql("SELECT * FROM products", pg_conn)
        customers_df = pd.read_sql("SELECT * FROM customers", pg_conn)
        orders_df = pd.read_sql("SELECT * FROM orders", pg_conn)
        order_items_df = pd.read_sql("SELECT * FROM order_items", pg_conn)
        events_df = pd.read_sql("SELECT * FROM events", pg_conn)
        pg_conn.close()
        print(f"Extracted: {len(categories_df)} categories, {len(products_df)} products, "
              f"{len(customers_df)} customers, {len(orders_df)} orders, "
              f"{len(order_items_df)} order items, {len(events_df)} events")


        print("Loading categories...")
        for _, row in categories_df.iterrows():
            run_cypher(driver, """
                MERGE (cat:Category {id: $id})
                SET cat.name = $name
            """, {"id": row["id"], "name": row["name"]})
        print(f"Loaded {len(categories_df)} categories")

        print("Loading products with category relationships...")
        for _, row in products_df.iterrows():
            run_cypher(driver, """
                MERGE (p:Product {id: $id})
                SET p.name = $name, p.price = $price
                WITH p
                MATCH (cat:Category {id: $category_id})
                MERGE (p)-[:IN_CATEGORY]->(cat)
            """, {
                "id": row["id"],
                "name": row["name"],
                "price": float(row["price"]),
                "category_id": row["category_id"]
            })
        print(f"Loaded {len(products_df)} products")

        print("Loading customers...")
        for _, row in customers_df.iterrows():
            run_cypher(driver, """
                MERGE (c:Customer {id: $id})
                SET c.name = $name, c.join_date = $join_date
            """, {
                "id": row["id"],
                "name": row["name"],
                "join_date": str(row["join_date"])
            })
        print(f"Loaded {len(customers_df)} customers")

        print("Loading orders with customer relationships...")
        for _, row in orders_df.iterrows():
            run_cypher(driver, """
                MERGE (o:Order {id: $id})
                SET o.ts = $ts
                WITH o
                MATCH (c:Customer {id: $customer_id})
                MERGE (c)-[:PLACED]->(o)
            """, {
                "id": row["id"],
                "ts": str(row["ts"]),
                "customer_id": row["customer_id"]
            })
        print(f"Loaded {len(orders_df)} orders")

        print("Creating order-product relationships...")
        for _, row in order_items_df.iterrows():
            run_cypher(driver, """
                MATCH (o:Order {id: $order_id})
                MATCH (p:Product {id: $product_id})
                MERGE (o)-[r:CONTAINS]->(p)
                SET r.quantity = $quantity
            """, {
                "order_id": row["order_id"],
                "product_id": row["product_id"],
                "quantity": int(row["quantity"])
            })
        print(f"Created {len(order_items_df)} order-product relationships")

        print("Creating event relationships...")
        event_type_map = {
            "view": "VIEW",
            "click": "CLICK",
            "add_to_cart": "ADD_TO_CART"
        }

        for _, row in events_df.iterrows():
            rel_type = event_type_map.get(row["event_type"], "VIEW")
            run_cypher(driver, f"""
                MATCH (c:Customer {{id: $customer_id}})
                MATCH (p:Product {{id: $product_id}})
                MERGE (c)-[r:{rel_type}]->(p)
                SET r.ts = $ts, r.event_id = $event_id
            """, {
                "customer_id": row["customer_id"],
                "product_id": row["product_id"],
                "ts": str(row["ts"]),
                "event_id": row["id"]
            })
        print(f"Created {len(events_df)} event relationships")

        print("ETL process completed successfully")

    finally:
        driver.close()


if __name__ == "__main__":
    etl()
    print("ETL done.")
