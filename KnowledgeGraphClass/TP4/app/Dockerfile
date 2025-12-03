FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

WORKDIR /workspace

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml ./

# Install Python dependencies using UV
RUN uv pip install --system --no-cache -r pyproject.toml

# Create media directory for outputs
RUN mkdir -p /workspace/media

# Expose Jupyter port
EXPOSE 8888

# Default command (will be overridden by docker-compose)
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]
