# Knowledge Graph Class: TPs Repository

This repository contains all TPs for the Knowledge Graph course.

## General Structure

Each TP follows a similar structure using Docker containers for Neo4j graph database and associated services. Projects include data generation scripts, ETL pipelines, Cypher queries, and optional REST APIs for interaction with the graph database.

## Completed TPs

- # [TP2 - Advanced graph queries and data loading](./TP2/README.md)
- # [TP3 - Twitter Network Analysis with Graph Data Science algorithms](./TP3/README.md)

## Quick Start

Each TP is organized with the following structure:
- `app/` - Application code, ETL scripts, and Cypher queries
- `neo4j/` - Neo4j data, logs, and import directories
- `scripts/` - Utility and health check scripts
- `docker-compose.yml` - Container orchestration configuration

To start any TP, navigate to its directory and run:

```bash
docker-compose up -d
```

For detailed setup instructions and specific requirements, refer to each TP's README.
