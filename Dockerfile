FROM python:3.12-slim

WORKDIR /app

# Install dependencies first (layer-cached separately from source)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source (includes src/img/ rank images)
COPY src/ ./src/
COPY pyproject.toml .

# Persistent data directory for the SQLite database
RUN mkdir -p /data

EXPOSE 80

CMD ["python", "-m", "src.main"]
