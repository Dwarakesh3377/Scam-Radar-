# ==============================================
# SCAM RADAR - Unified Dockerfile (Hugging Face Spaces)
# ==============================================

# --- Stage 1: Build Frontend ---
FROM node:18-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
# Note: VITE_API_URL is set to /api so it uses the same origin
ENV VITE_API_URL=/api
RUN npm run build

# --- Stage 2: Final Production Image ---
FROM python:3.11-slim

# Install Nginx and other requirements
RUN apt-get update && apt-get install -y \
    nginx \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Backend requirements
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Download NLTK data during build to save memory and time at runtime
RUN python -m nltk.downloader punkt stopwords wordnet

# Copy Backend code
COPY backend/ .

# Copy Dataset directory (required for Reported Victims)
COPY dataset/ ./dataset/

# Ensure directory for models exist (will be filled at runtime)
RUN mkdir -p /app/ml_models

# Copy Frontend build from Stage 1
COPY --from=frontend-build /app/frontend/dist /usr/share/nginx/html

# Copy Nginx config
COPY nginx.conf /etc/nginx/nginx.conf

# Expose the Hugging Face default port
EXPOSE 7860

# Environment variables
ENV PORT=7860
ENV FLASK_ENV=production
ENV GOOGLE_CLOUD_PROJECT=scam-risk-detection
ENV FIREBASE_SERVICE_ACCOUNT_PATH=firebase_setup/firebase-service-account.json

# Script to start both Nginx and Gunicorn
# Reduced threads to 4 for better memory stability on CPU spaces
RUN echo "#!/bin/bash\nnginx -g 'daemon off;' & \ngunicorn --bind 0.0.0.0:5000 --threads 4 --worker-class gthread --workers 1 --timeout 180 --access-logfile - --error-logfile - app:app" > /app/start.sh
RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]
