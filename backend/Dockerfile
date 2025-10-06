# Base image with wkhtmltopdf preinstalled
FROM madnight/docker-alpine-wkhtmltopdf:latest

# Set working directory
WORKDIR /app

# Copy dependencies and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files
COPY . .

# Expose Flask port
EXPOSE 5000

# Start the Flask app
CMD ["python3", "app.py"]
