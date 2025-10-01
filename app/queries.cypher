// Neo4j Schema Setup
// This file contains constraints and indexes for the e-commerce graph

// Create constraints to ensure uniqueness
CREATE CONSTRAINT customer_id IF NOT EXISTS FOR (c:Customer) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT product_id IF NOT EXISTS FOR (p:Product) REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT order_id IF NOT EXISTS FOR (o:Order) REQUIRE o.id IS UNIQUE;
CREATE CONSTRAINT category_id IF NOT EXISTS FOR (cat:Category) REQUIRE cat.id IS UNIQUE;

// Create indexes for better query performance
CREATE INDEX customer_name IF NOT EXISTS FOR (c:Customer) ON (c.name);
CREATE INDEX product_name IF NOT EXISTS FOR (p:Product) ON (p.name);
CREATE INDEX product_price IF NOT EXISTS FOR (p:Product) ON (p.price);
CREATE INDEX category_name IF NOT EXISTS FOR (cat:Category) ON (cat.name);
