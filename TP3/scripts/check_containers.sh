#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "TP3 - Container Health Check"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running${NC}"
    exit 1
fi

# Check Neo4j container
echo -n "Checking Neo4j container... "
if docker ps | grep -q "tp3-neo4j"; then
    echo -e "${GREEN}Running${NC}"

    # Check Neo4j health
    echo -n "Checking Neo4j health... "
    if docker exec tp3-neo4j wget --no-verbose --tries=1 --spider http://localhost:7474 2>&1 | grep -q "200 OK"; then
        echo -e "${GREEN}Healthy${NC}"
    else
        echo -e "${YELLOW}Starting up...${NC}"
    fi
else
    echo -e "${RED}Not running${NC}"
fi

# Check App container
echo -n "Checking App container... "
if docker ps | grep -q "tp3-app"; then
    echo -e "${GREEN}Running${NC}"
else
    echo -e "${RED}Not running${NC}"
fi

echo ""
echo "Service Endpoints"
echo "Neo4j Browser:  http://localhost:7474"
echo "Neo4j Bolt:     bolt://localhost:7687"
echo "FastAPI:        http://localhost:8000"
echo "API Docs:       http://localhost:8000/docs"
echo ""

# Test Neo4j connection
echo -n "Testing Neo4j connection... "
if curl -s http://localhost:7474 > /dev/null; then
    echo -e "${GREEN}Success${NC}"
else
    echo -e "${RED}Failed${NC}"
fi

# Test FastAPI connection
echo -n "Testing FastAPI connection... "
if curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}Success${NC}"

    # Get database stats
    echo ""
    echo "Database Statistics"
    curl -s http://localhost:8000/stats | python3 -m json.tool
else
    echo -e "${RED}Failed${NC}"
fi

echo ""
echo "Container Logs (last 10 lines)"
echo ""
echo "Neo4j logs:"
docker logs tp3-neo4j --tail 10 2>&1 | tail -10
echo ""
echo "App logs:"
docker logs tp3-app --tail 10 2>&1 | tail -10

echo ""
echo "Health check complete!"
