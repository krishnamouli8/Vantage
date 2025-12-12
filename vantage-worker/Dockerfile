FROM python:3.11-slim

# Install sqlite3 CLI tool
RUN apt-get update && apt-get install -y sqlite3 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY worker/ ./worker/

CMD ["python", "-m", "worker.main"]
