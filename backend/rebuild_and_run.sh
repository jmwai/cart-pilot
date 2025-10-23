#!/bin/bash

# Rebuild and run the concierge agent container

echo "Stopping existing container..."
docker stop $(docker ps -q --filter ancestor=concierge-agent:latest) 2>/dev/null || true

echo "Building new image..."
docker build -t concierge-agent:latest .

echo "Running container..."
docker run -d -p 8080:8080 \
    -v ~/.config/gcloud:/root/.config/gcloud:ro \
    -e GOOGLE_API_KEY="$GOOGLE_API_KEY" \
    -e PROJECT_ID="$PROJECT_ID" \
    -e REGION="$REGION" \
    -e DB_HOST="$DB_HOST" \
    -e DB_PORT="$DB_PORT" \
    -e DB_NAME="$DB_NAME" \
    -e DB_USER="$DB_USER" \
    -e DB_PASSWORD="$DB_PASSWORD" \
    concierge-agent:latest

echo "Waiting for container to start..."
sleep 3

echo "Checking health..."
curl -s http://localhost:8080/healthz | python3 -m json.tool

echo ""
echo "Container running at http://localhost:8080"
echo "Run ./test_agent.sh to test the agent"

