# Cloud Run Deployment Guide

This guide explains how to set up automated deployment to Google Cloud Run via GitHub Actions.

## Architecture Overview

The project deploys as two separate Cloud Run services:
- **Backend Service** (`backend-service`): FastAPI application with A2A protocol support
- **Frontend Service** (`frontend-service`): Next.js standalone application

## Deployment Workflow

The deployment workflow (`.github/workflows/deploy.yml`) automatically:
1. Detects changes in `frontend/` or `backend/` directories
2. Builds Docker images for the changed service(s)
3. Pushes images to Google Artifact Registry
4. Deploys to Cloud Run

## Prerequisites

### 1. Google Cloud Project Setup

Ensure you have:
- GCP Project ID: `gemini-adk-vertex-2025`
- Artifact Registry repository: `cloud-run-agent` (in region `europe-west1`)
- Cloud Run services created or permissions to create them

### 2. Create Artifact Registry Repository

If the repository doesn't exist, create it:

```bash
gcloud artifacts repositories create cloud-run-agent \
  --repository-format=docker \
  --location=europe-west1 \
  --project=gemini-adk-vertex-2025 \
  --description="Docker images for Cloud Run services"
```

### 3. Create Service Account

Create a service account for GitHub Actions:

```bash
# Create service account
gcloud iam service-accounts create github-actions \
  --project=gemini-adk-vertex-2025 \
  --display-name="GitHub Actions Service Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding gemini-adk-vertex-2025 \
  --member="serviceAccount:github-actions@gemini-adk-vertex-2025.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding gemini-adk-vertex-2025 \
  --member="serviceAccount:github-actions@gemini-adk-vertex-2025.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

gcloud projects add-iam-policy-binding gemini-adk-vertex-2025 \
  --member="serviceAccount:github-actions@gemini-adk-vertex-2025.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"
```

### 4. Generate Service Account Key

```bash
gcloud iam service-accounts keys create github-actions-key.json \
  --iam-account=github-actions@gemini-adk-vertex-2025.iam.gserviceaccount.com \
  --project=gemini-adk-vertex-2025
```

## GitHub Secrets Configuration

Add the following secrets to your GitHub repository:

1. Go to your repository → Settings → Secrets and variables → Actions

2. Add these secrets:

   - **`PROJECT_ID`**
     - Value: Your Google Cloud Project ID (e.g., `gemini-adk-vertex-2025`)
     - Used throughout the workflow for GCP project identification

   - **`GCP_SERVICE_ACCOUNT_KEY`**
     - Value: Contents of the `github-actions-key.json` file (entire JSON)
     - This allows GitHub Actions to authenticate with Google Cloud

   - **`GOOGLE_API_KEY`**
     - Value: Your Google API key for Vertex AI
     - Used by the backend service to access Vertex AI services

## Initial Cloud Run Service Setup

### Backend Service

If the backend service doesn't exist, create it manually first:

```bash
gcloud run deploy backend-service \
  --image europe-west1-docker.pkg.dev/gemini-adk-vertex-2025/cloud-run-agent/backend-service:latest \
  --region europe-west1 \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0 \
  --set-env-vars="PROJECT_ID=gemini-adk-vertex-2025,REGION=europe-west1,GOOGLE_API_KEY=<your-api-key>" \
  --project gemini-adk-vertex-2025
```

### Frontend Service

The frontend service can be created automatically by the workflow, but ensure the backend service exists first so the frontend can fetch its URL.

## Workflow Behavior

### Path-Based Triggers

- Changes to `backend/**` → Only `deploy-backend` job runs
- Changes to `frontend/**` → Only `deploy-frontend` job runs
- Changes to both → Both jobs run
- Changes to neither → Workflow is skipped

### Image Tagging

- Images are tagged with: `{GITHUB_SHA}` (commit SHA)
- Latest tag: `latest` is also pushed
- Cloud Run deploys using the commit SHA tag

### Environment Variables

**Backend Service:**
- `PROJECT_ID`: From GitHub Secrets (`${{ secrets.PROJECT_ID }}`)
- `REGION`: Set to `europe-west1`
- `GOOGLE_API_KEY`: From GitHub Secrets

**Frontend Service:**
- `NEXT_PUBLIC_AGENT_CARD_URL`: Auto-detected from backend service URL
- `NEXT_PUBLIC_API_BASE_URL`: Auto-detected from backend service URL
- `NEXT_PUBLIC_DEFAULT_USER_ID`: Set to `user_guest`

## Manual Deployment

If you need to deploy manually:

### Backend

```bash
cd backend
docker build -t europe-west1-docker.pkg.dev/gemini-adk-vertex-2025/cloud-run-agent/backend-service:manual .
docker push europe-west1-docker.pkg.dev/gemini-adk-vertex-2025/cloud-run-agent/backend-service:manual

gcloud run deploy backend-service \
  --image europe-west1-docker.pkg.dev/gemini-adk-vertex-2025/cloud-run-agent/backend-service:manual \
  --region europe-west1 \
  --platform managed \
  --allow-unauthenticated
```

### Frontend

```bash
cd frontend
docker build \
  --build-arg NEXT_PUBLIC_AGENT_CARD_URL="https://backend-service-<hash>-ew.a.run.app/.well-known/agent-card.json" \
  --build-arg NEXT_PUBLIC_API_BASE_URL="https://backend-service-<hash>-ew.a.run.app" \
  --build-arg NEXT_PUBLIC_DEFAULT_USER_ID="user_guest" \
  -t europe-west1-docker.pkg.dev/gemini-adk-vertex-2025/cloud-run-agent/frontend-service:manual .

docker push europe-west1-docker.pkg.dev/gemini-adk-vertex-2025/cloud-run-agent/frontend-service:manual

gcloud run deploy frontend-service \
  --image europe-west1-docker.pkg.dev/gemini-adk-vertex-2025/cloud-run-agent/frontend-service:manual \
  --region europe-west1 \
  --platform managed \
  --allow-unauthenticated
```

## Troubleshooting

### Workflow Not Triggering

- Ensure you're pushing to the `main` branch
- Verify files changed are in `frontend/` or `backend/` directories
- Check GitHub Actions tab for workflow run status

### Authentication Errors

- Verify `GCP_SERVICE_ACCOUNT_KEY` secret is correctly set
- Ensure service account has required IAM roles
- Check service account key hasn't expired

### Build Failures

- Check Dockerfile syntax
- Verify all dependencies are in `requirements.txt` (backend) or `package.json` (frontend)
- Review build logs in GitHub Actions

### Deployment Failures

- Verify Artifact Registry repository exists
- Check Cloud Run service permissions
- Ensure backend service exists before deploying frontend
- Review Cloud Run logs: `gcloud run services logs read backend-service --region europe-west1`

### Frontend Can't Connect to Backend

- Verify backend service URL is correct
- Check CORS settings in backend
- Ensure environment variables are set correctly in frontend build

## Monitoring

View service URLs:
```bash
# Backend URL
gcloud run services describe backend-service --region europe-west1 --format 'value(status.url)'

# Frontend URL
gcloud run services describe frontend-service --region europe-west1 --format 'value(status.url)'
```

View logs:
```bash
gcloud run services logs read backend-service --region europe-west1 --limit 50
gcloud run services logs read frontend-service --region europe-west1 --limit 50
```

