FROM nginx:alpine
COPY . /usr/share/nginx/html        
# Copy the Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf          
# Copy the frontend files first (excluding nginx.conf)
COPY index.html script.js style.css /usr/share/nginx/html/  
# Copy only the frontend files
COPY index.html /usr/share/nginx/html/
COPY style.css /usr/share/nginx/html/
COPY script.js /usr/share/nginx/html/       
FROM nginx:alpine
COPY . /usr/share/nginx/html        
# Copy the Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf
# Copy the frontend files first (excluding nginx.conf)
COPY index.html script.js style.css /usr/share/nginx/html/  
# Copy only the frontend files
COPY index.html /usr/share/nginx/html/
COPY style.css /usr/share/nginx/html/
COPY script.js /usr/share/nginx/html/   
FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt         
EXPOSE 5000
CMD ["python", "app.py"]
FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 5000
CMD ["python", "app.py"]