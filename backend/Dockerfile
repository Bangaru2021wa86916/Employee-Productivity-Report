# backend/Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies including netcat for the wait script
RUN apt-get update && \
    apt-get install -y gcc libssl-dev netcat && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Expose Flask port
EXPOSE 5000

# Run wait-for-db.sh which will start the app when DB is ready
CMD ["bash", "wait-for-db.sh"]
