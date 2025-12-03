#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}TP5 - Container Health Check${NC}"
echo -e "${BLUE}======================================${NC}"

# Check if Docker is running
echo -e "\n${YELLOW}[1/6] Checking Docker...${NC}"
if docker info > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Docker is running${NC}"
else
    echo -e "${RED}✗ Docker is not running${NC}"
    echo -e "${YELLOW}Please start Docker and try again${NC}"
    exit 1
fi

# Check Neo4j container
echo -e "\n${YELLOW}[2/6] Checking Neo4j container...${NC}"
if docker ps | grep -q "tp5-neo4j"; then
    echo -e "${GREEN}✓ Neo4j container is running${NC}"

    # Check Neo4j health
    if docker exec tp5-neo4j wget --spider --quiet http://localhost:7474; then
        echo -e "${GREEN}✓ Neo4j HTTP endpoint is healthy${NC}"
    else
        echo -e "${RED}✗ Neo4j HTTP endpoint is not responding${NC}"
    fi
else
    echo -e "${RED}✗ Neo4j container is not running${NC}"
    echo -e "${YELLOW}Start it with: docker-compose up -d neo4j${NC}"
fi

# Check Jupyter container
echo -e "\n${YELLOW}[3/6] Checking Jupyter container...${NC}"
if docker ps | grep -q "tp5-jupyter"; then
    echo -e "${GREEN}✓ Jupyter container is running${NC}"

    # Check Jupyter accessibility
    if curl -s http://localhost:8888 > /dev/null; then
        echo -e "${GREEN}✓ Jupyter Lab is accessible at http://localhost:8888${NC}"
    else
        echo -e "${YELLOW}⚠ Jupyter might still be starting up${NC}"
    fi
else
    echo -e "${RED}✗ Jupyter container is not running${NC}"
    echo -e "${YELLOW}Start it with: docker-compose up -d jupyter${NC}"
fi

# Check Neo4j connectivity from Jupyter
echo -e "\n${YELLOW}[4/6] Testing Neo4j connectivity...${NC}"
if docker ps | grep -q "tp5-jupyter"; then
    TEST_RESULT=$(docker exec tp5-jupyter python3 -c "
from neo4j import GraphDatabase
import sys
try:
    driver = GraphDatabase.driver('bolt://neo4j:7687', auth=('neo4j', 'password123'))
    with driver.session() as session:
        result = session.run('RETURN 1 AS test')
        result.single()
    driver.close()
    print('success')
except Exception as e:
    print(f'error: {e}')
    sys.exit(1)
" 2>&1)

    if echo "$TEST_RESULT" | grep -q "success"; then
        echo -e "${GREEN}✓ Jupyter can connect to Neo4j${NC}"
    else
        echo -e "${RED}✗ Jupyter cannot connect to Neo4j${NC}"
        echo -e "${YELLOW}Error: $TEST_RESULT${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Jupyter container not running, skipping test${NC}"
fi

# Check if data is loaded in Neo4j
echo -e "\n${YELLOW}[5/6] Checking Neo4j data...${NC}"
if docker ps | grep -q "tp5-neo4j"; then
    ARTICLE_COUNT=$(docker exec tp5-neo4j cypher-shell -u neo4j -p password123 "MATCH (a:Article) RETURN count(a) AS count;" --format plain 2>/dev/null | grep -E '^[0-9]+$' | head -1)
    ENTITY_COUNT=$(docker exec tp5-neo4j cypher-shell -u neo4j -p password123 "MATCH (e:Entity) RETURN count(e) AS count;" --format plain 2>/dev/null | grep -E '^[0-9]+$' | head -1)

    if [ -z "$ARTICLE_COUNT" ]; then
        ARTICLE_COUNT=0
    fi
    if [ -z "$ENTITY_COUNT" ]; then
        ENTITY_COUNT=0
    fi

    echo -e "  Articles: ${ARTICLE_COUNT}"
    echo -e "  Entities: ${ENTITY_COUNT}"

    if [ "$ARTICLE_COUNT" -gt 0 ] && [ "$ENTITY_COUNT" -gt 0 ]; then
        echo -e "${GREEN}✓ Data is loaded in Neo4j${NC}"
    else
        echo -e "${YELLOW}⚠ No data found in Neo4j${NC}"
        echo -e "${YELLOW}Load data with: docker exec tp5-jupyter python /workspace/load_data.py${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Neo4j container not running, skipping check${NC}"
fi

# Check Ollama availability
echo -e "\n${YELLOW}[6/6] Checking Ollama...${NC}"
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Ollama is running on host machine${NC}"

    # List available models
    MODELS=$(curl -s http://localhost:11434/api/tags | grep -o '"name":"[^"]*"' | cut -d'"' -f4 | tr '\n' ', ' | sed 's/,$//')
    if [ -n "$MODELS" ]; then
        echo -e "  Available models: ${MODELS}"
    fi

    # Check for recommended model
    if curl -s http://localhost:11434/api/tags | grep -q "llama3:8b"; then
        echo -e "${GREEN}✓ Recommended model (llama3:8b) is available${NC}"
    else
        echo -e "${YELLOW}⚠ Recommended model (llama3:8b) not found${NC}"
        echo -e "${YELLOW}Pull it with: ollama pull llama3:8b${NC}"
    fi
else
    echo -e "${RED}✗ Ollama is not accessible${NC}"
    echo -e "${YELLOW}Install Ollama from: https://ollama.ai/${NC}"
    echo -e "${YELLOW}Then run: ollama pull llama3:8b${NC}"
fi

# Show recent container logs
echo -e "\n${YELLOW}Container logs (last 10 lines):${NC}"
echo -e "\n${BLUE}--- Neo4j logs ---${NC}"
docker logs tp5-neo4j --tail 10 2>&1 | tail -10

echo -e "\n${BLUE}--- Jupyter logs ---${NC}"
docker logs tp5-jupyter --tail 10 2>&1 | tail -10

# Summary
echo -e "\n${BLUE}======================================${NC}"
echo -e "${BLUE}Summary${NC}"
echo -e "${BLUE}======================================${NC}"
echo -e "Neo4j Browser: ${GREEN}http://localhost:7474${NC}"
echo -e "Jupyter Lab:   ${GREEN}http://localhost:8888${NC}"
echo -e "Neo4j Bolt:    ${GREEN}bolt://localhost:7687${NC}"
echo -e "\n${YELLOW}Access credentials:${NC}"
echo -e "  Neo4j: neo4j / password123"
echo -e "  Jupyter: No password required"
echo -e "${BLUE}======================================${NC}"
