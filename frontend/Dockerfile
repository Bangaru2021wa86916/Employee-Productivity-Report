@"
FROM nginx:alpine

# Copy only the frontend files
COPY index.html /usr/share/nginx/html/
COPY style.css /usr/share/nginx/html/
COPY script.js /usr/share/nginx/html/
"@ | Set-Content -Path frontend/Dockerfile