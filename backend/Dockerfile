    # Use official Python image
    FROM python:3.10-slim

    # Set work directory
    WORKDIR /app

    # Install system dependencies
    RUN apt-get update && apt-get install -y gcc libssl-dev && rm -rf /var/lib/apt/lists/*

    # Copy requirements first for better caching
    COPY requirements.txt .

    # Install dependencies
    RUN pip install --no-cache-dir -r requirements.txt

    # Copy the app code
    COPY . .

    # Expose Flask port
    EXPOSE 5000

    # Run the app
    CMD ["bash", "wait-for-db.sh", "python", "app.py"]
