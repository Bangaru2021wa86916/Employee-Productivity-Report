# Use an image that already includes wkhtmltopdf
FROM madnight/docker-alpine-wkhtmltopdf:latest

# Install Python
RUN apk add --no-cache python3 py3-pip

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your source code
COPY . .

EXPOSE 5000
CMD ["python3", "app.py"]
