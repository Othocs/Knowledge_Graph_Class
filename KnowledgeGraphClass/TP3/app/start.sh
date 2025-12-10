#!/bin/sh

echo "Starting TP3 Application..."

# Run ETL to load data
echo "Running ETL process..."
python3 etl.py

# Start FastAPI application
echo "Starting FastAPI server..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
