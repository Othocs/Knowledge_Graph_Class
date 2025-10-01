set -e

echo "Installing Python dependencies with uv..."
cd /work/app
uv sync

echo "Starting FastAPI server..."
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
