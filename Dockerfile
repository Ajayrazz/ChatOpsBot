FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install dependencies first (layer caching)
COPY ChatOpsBot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ChatOpsBot/ .

# Fly.io sets PORT env var — default to 8000
ENV PORT=8000

EXPOSE ${PORT}

# Run with uvicorn
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT}
