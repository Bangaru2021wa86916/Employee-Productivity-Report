# Base image with wkhtmltopdf preinstalled
FROM madnight/docker-alpine-wkhtmltopdf:latest

# Set working directory
WORKDIR /app

# Copy app files
COPY . .

# Expose Flask port
EXPOSE 5000

# Start the Flask app
CMD ["python3", "app.py"]
