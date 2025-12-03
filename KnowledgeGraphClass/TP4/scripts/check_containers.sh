#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "TP4 - Container Health Check"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running${NC}"
    exit 1
fi

# Check Neo4j container
echo -n "Checking Neo4j container... "
if docker ps | grep -q "tp4-neo4j"; then
    echo -e "${GREEN}Running${NC}"

    # Check Neo4j health
    echo -n "Checking Neo4j health... "
    if docker exec tp4-neo4j wget --no-verbose --tries=1 --spider http://localhost:7474 2>&1 | grep -q "200 OK"; then
        echo -e "${GREEN}Healthy${NC}"
    else
        echo -e "${YELLOW}Starting up...${NC}"
    fi
else
    echo -e "${RED}Not running${NC}"
fi

# Check Jupyter container
echo -n "Checking Jupyter container... "
if docker ps | grep -q "tp4-jupyter"; then
    echo -e "${GREEN}Running${NC}"
else
    echo -e "${RED}Not running${NC}"
fi

echo ""
echo "Service Endpoints"
echo "Neo4j Browser:  http://localhost:7474"
echo "Neo4j Bolt:     bolt://localhost:7687"
echo "Jupyter Lab:    http://localhost:8888"
echo ""

# Test Neo4j connection
echo -n "Testing Neo4j connection... "
if curl -s http://localhost:7474 > /dev/null; then
    echo -e "${GREEN}Success${NC}"
else
    echo -e "${RED}Failed${NC}"
fi

# Test Jupyter connection
echo -n "Testing Jupyter connection... "
if curl -s http://localhost:8888 > /dev/null; then
    echo -e "${GREEN}Success${NC}"

    # Check if data is loaded
    echo ""
    echo "Database Check"
    echo -n "Checking if data is loaded... "

    STREAM_COUNT=$(docker exec tp4-neo4j cypher-shell -u neo4j -p password123 "MATCH (s:Stream) RETURN count(s) AS count" --format plain 2>/dev/null | grep -v "count" | tr -d ' ')

    if [ ! -z "$STREAM_COUNT" ] && [ "$STREAM_COUNT" -gt 0 ]; then
        echo -e "${GREEN}Yes${NC} (${STREAM_COUNT} streams)"
    else
        echo -e "${YELLOW}No data found${NC}"
        echo "Run: docker exec tp4-jupyter python /workspace/load_data.py"
    fi
else
    echo -e "${RED}Failed${NC}"
fi

echo ""
echo "Container Logs (last 10 lines)"
echo ""
echo "Neo4j logs:"
docker logs tp4-neo4j --tail 10 2>&1 | tail -10
echo ""
echo "Jupyter logs:"
docker logs tp4-jupyter --tail 10 2>&1 | tail -10

echo ""
echo "Health check complete!"
