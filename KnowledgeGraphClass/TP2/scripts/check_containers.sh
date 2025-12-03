#!/bin/bash
set -e

if [ "$CONTAINER_MODE" = "true" ]; then
    API_HOST="app"
    POSTGRES_HOST="postgres"
else
    API_HOST="127.0.0.1"
    POSTGRES_HOST="localhost"
fi

echo "Running stack tests..."
echo ""

echo "Testing FastAPI health endpoint..."
HEALTH_RESPONSE=$(curl -s http://${API_HOST}:8000/health)

if echo "$HEALTH_RESPONSE" | grep -q '"ok":true'; then
    echo "FastAPI health OK"
else
    echo "FastAPI health check failed"
    echo "Response: $HEALTH_RESPONSE"
    exit 1
fi

echo "$HEALTH_RESPONSE"
echo ""

echo "Postgres: SELECT * FROM orders LIMIT 5;"
if [ "$CONTAINER_MODE" = "true" ]; then
    PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT * FROM orders LIMIT 5;"
else
    docker compose exec -T postgres psql -U app -d shop -c "SELECT * FROM orders LIMIT 5;"
fi

if [ $? -eq 0 ]; then
    echo "Orders query OK"
else
    echo "Orders query failed"
    exit 1
fi
echo ""

echo "Postgres: SELECT now();"
if [ "$CONTAINER_MODE" = "true" ]; then
    PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT now();"
else
    docker compose exec -T postgres psql -U app -d shop -c "SELECT now();"
fi

if [ $? -eq 0 ]; then
    echo "now() query OK"
else
    echo "now() query failed"
    exit 1
fi
echo ""

echo "Running ETL..."
if [ "$CONTAINER_MODE" = "true" ]; then
    ETL_OUTPUT=$(docker exec tp2-app bash -c "cd /work/app && uv run etl.py" | cat)
else
    ETL_OUTPUT=$(docker compose exec -T app bash -c "cd /work/app && uv run etl.py" | cat)
fi

if echo "$ETL_OUTPUT" | grep -q "ETL done."; then
    echo "ETL completed"
else
    echo "ETL execution failed"
    echo "Output:"
    echo "$ETL_OUTPUT"
    exit 1
fi

echo ""
echo "All tests passed"
