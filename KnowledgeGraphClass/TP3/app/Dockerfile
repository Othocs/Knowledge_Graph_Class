FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies using uv
RUN uv pip install --system --no-cache -r pyproject.toml

# Copy application files
COPY . .

# Make scripts executable
RUN chmod +x start.sh etl.py main.py

# Expose port
EXPOSE 8000

CMD ["sh", "start.sh"]
