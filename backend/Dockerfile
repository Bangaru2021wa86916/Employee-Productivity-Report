# Backend Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Copy only necessary files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

CMD ["python", "app.py"]