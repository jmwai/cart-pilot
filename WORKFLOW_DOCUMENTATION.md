# Deployment Workflow Documentation

## Overview

Cart Pilot uses a GitHub Actions workflow to automatically build, push, and deploy Docker images to Google Cloud Run. The workflow is designed to deploy only the services that have changed, reducing build time and costs.

## Workflow File Location

`.github/workflows/deploy.yml`

## Workflow Trigger

The workflow is triggered automatically when:
- **Branch**: `main` branch only
- **Paths**: Changes to files in `frontend/**` or `backend/**` directories

### Example Triggers

```yaml
# Triggers backend deployment only
- Modified: backend/app/main.py
- Modified: backend/Dockerfile

# Triggers frontend deployment only
- Modified: frontend/src/components/Header.tsx
- Modified: frontend/package.json

# Triggers both deployments
- Modified: backend/app/main.py AND frontend/src/app/page.tsx

# Does NOT trigger workflow
- Modified: README.md (outside frontend/ or backend/)
- Modified: .github/workflows/deploy.yml
```

## Workflow Architecture

The workflow consists of three jobs that run in sequence:

```
┌─────────────────┐
│  check-changes  │  (Determines which services changed)
└────────┬────────┘
         │
         ├─────────────────┐
         │                 │
         ▼                 ▼
┌─────────────────┐  ┌──────────────────┐
│ deploy-backend  │  │ deploy-frontend  │  (Run in parallel if needed)
└─────────────────┘  └──────────────────┘
```

### Job 1: check-changes

**Purpose**: Analyzes the git diff to determine which directories changed.

**Technology**: Uses `dorny/paths-filter@v3` action

**Outputs**:
- `backend`: `true` if `backend/**` files changed
- `frontend`: `true` if `frontend/**` files changed

**Example Output**:
```yaml
backend: 'true'
frontend: 'false'
```

### Job 2: deploy-backend

**Condition**: Only runs if `needs.check-changes.outputs.backend == 'true'`

**Steps**:

1. **Checkout Code**
   - Checks out the repository code

2. **Authenticate to Google Cloud**
   - Uses `GCP_SERVICE_ACCOUNT_KEY` secret
   - Authenticates GitHub Actions with GCP

3. **Set up Cloud SDK**
   - Installs `gcloud` CLI
   - Sets project to `${{ secrets.PROJECT_ID }}`

4. **Configure Docker for Artifact Registry**
   - Configures Docker to authenticate with `europe-west1-docker.pkg.dev`
   - Required for pushing images

5. **Build Docker Image**
   - **Working Directory**: `./backend`
   - **Image Name**: `europe-west1-docker.pkg.dev/{PROJECT_ID}/cart-pilot/cart-pilot-backend`
   - **Tags**: 
     - `{GITHUB_SHA}` (commit SHA for versioning)
     - `latest` (convenience tag)
   - **Output**: Sets `IMAGE_TAG` and `IMAGE_LATEST` environment variables

6. **Push Docker Image**
   - Pushes both tags to Artifact Registry
   - Both tags point to the same image

7. **Deploy to Cloud Run**
   - **Service Name**: `cart-pilot-backend`
   - **Region**: `europe-west1`
   - **Configuration**:
     - Port: `8080`
     - Memory: `512Mi`
     - CPU: `1`
     - Timeout: `300` seconds
     - Max Instances: `10`
     - Min Instances: `0` (scales to zero)
     - Unauthenticated access enabled
   - **Environment Variables**:
     - `PROJECT_ID`: From GitHub Secrets
     - `REGION`: `europe-west1`
     - `GOOGLE_API_KEY`: From GitHub Secrets

### Job 3: deploy-frontend

**Condition**: Only runs if `needs.check-changes.outputs.frontend == 'true'`

**Steps**:

1. **Checkout Code** (Same as backend)

2. **Authenticate to Google Cloud** (Same as backend)

3. **Set up Cloud SDK** (Same as backend)

4. **Configure Docker for Artifact Registry** (Same as backend)

5. **Get Backend Service URL**
   - Queries Cloud Run to get the backend service URL
   - Uses: `gcloud run services describe cart-pilot-backend`
   - Outputs: `BACKEND_URL` environment variable
   - **Note**: If backend doesn't exist, this step returns empty string (frontend build will fail gracefully)

6. **Build Docker Image**
   - **Working Directory**: `./frontend`
   - **Image Name**: `europe-west1-docker.pkg.dev/{PROJECT_ID}/cart-pilot/cart-pilot-frontend`
   - **Build Arguments** (baked into image at build time):
     - `NEXT_PUBLIC_AGENT_CARD_URL`: `{BACKEND_URL}/.well-known/agent-card.json`
     - `NEXT_PUBLIC_API_BASE_URL`: `{BACKEND_URL}`
     - `NEXT_PUBLIC_DEFAULT_USER_ID`: `user_guest`
   - **Tags**: Same as backend (SHA + latest)

7. **Push Docker Image** (Same as backend)

8. **Deploy to Cloud Run**
   - **Service Name**: `cart-pilot-frontend`
   - **Configuration**: Same as backend
   - **Note**: No environment variables needed (all set at build time)

## Image Tagging Strategy

### Commit SHA Tag
- Format: `{GITHUB_SHA}` (e.g., `a1b2c3d4e5f6...`)
- Purpose: Immutable reference to specific commit
- Used for: Cloud Run deployment
- Benefit: Can rollback to exact commit if needed

### Latest Tag
- Format: `latest`
- Purpose: Convenience tag for manual deployments
- Used for: Development/testing
- Note: Not used by automated workflow

## Environment Variables

### Backend Service

Set at runtime via Cloud Run:

| Variable | Source | Value |
|----------|--------|-------|
| `PROJECT_ID` | GitHub Secret | Your GCP Project ID |
| `REGION` | Hardcoded | `europe-west1` |
| `GOOGLE_API_KEY` | GitHub Secret | Your Google API Key |

### Frontend Service

Set at build time via Docker build args:

| Variable | Source | Value |
|----------|--------|-------|
| `NEXT_PUBLIC_AGENT_CARD_URL` | Auto-detected | `{BACKEND_URL}/.well-known/agent-card.json` |
| `NEXT_PUBLIC_API_BASE_URL` | Auto-detected | `{BACKEND_URL}` |
| `NEXT_PUBLIC_DEFAULT_USER_ID` | Hardcoded | `user_guest` |

**Note**: Frontend variables are prefixed with `NEXT_PUBLIC_` because Next.js only exposes variables with this prefix to the browser.

## Required GitHub Secrets

The workflow requires these secrets to be configured in GitHub:

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `PROJECT_ID` | Google Cloud Project ID | `gemini-adk-vertex-2025` |
| `GCP_SERVICE_ACCOUNT_KEY` | Service account JSON key | `{"type":"service_account",...}` |
| `GOOGLE_API_KEY` | Google API Key for Vertex AI | `AIza...` |

### Setting Up Secrets

1. Go to your GitHub repository
2. Navigate to: **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add each secret with its value

## Artifact Registry

### Repository Details

- **Name**: `cart-pilot`
- **Region**: `europe-west1`
- **Format**: Docker
- **Location**: `europe-west1-docker.pkg.dev/{PROJECT_ID}/cart-pilot/`

### Image Paths

- **Backend**: `europe-west1-docker.pkg.dev/{PROJECT_ID}/cart-pilot/cart-pilot-backend`
- **Frontend**: `europe-west1-docker.pkg.dev/{PROJECT_ID}/cart-pilot/cart-pilot-frontend`

## Cloud Run Services

### Service Names

- **Backend**: `cart-pilot-backend`
- **Frontend**: `cart-pilot-frontend`

### Service Configuration

Both services share the same configuration:

```yaml
Region: europe-west1
Platform: managed
Port: 8080
Memory: 512Mi
CPU: 1
Timeout: 300 seconds
Max Instances: 10
Min Instances: 0 (scales to zero)
Authentication: Unauthenticated (public access)
```

## Workflow Execution Flow

### Scenario 1: Backend Change Only

```
1. Developer pushes changes to backend/app/main.py
2. GitHub detects change in backend/** path
3. check-changes job runs:
   - backend: 'true'
   - frontend: 'false'
4. deploy-backend job runs:
   - Builds image
   - Pushes to Artifact Registry
   - Deploys to Cloud Run
5. deploy-frontend job: SKIPPED
```

### Scenario 2: Frontend Change Only

```
1. Developer pushes changes to frontend/src/components/Header.tsx
2. GitHub detects change in frontend/** path
3. check-changes job runs:
   - backend: 'false'
   - frontend: 'true'
4. deploy-backend job: SKIPPED
5. deploy-frontend job runs:
   - Gets backend URL
   - Builds image with backend URL
   - Pushes to Artifact Registry
   - Deploys to Cloud Run
```

### Scenario 3: Both Changed

```
1. Developer pushes changes to both directories
2. GitHub detects changes in both paths
3. check-changes job runs:
   - backend: 'true'
   - frontend: 'true'
4. deploy-backend job runs (parallel)
5. deploy-frontend job runs (parallel)
   - Note: Frontend waits for backend to deploy first
   - Gets backend URL from newly deployed backend
```

## Manual Workflow Trigger

You can manually trigger the workflow from GitHub UI:

1. Go to **Actions** tab
2. Select **Deploy to Cloud Run** workflow
3. Click **Run workflow**
4. Select branch (`main`)
5. Click **Run workflow**

**Note**: Manual trigger will run both jobs regardless of file changes.

## Monitoring Workflow Execution

### View Workflow Runs

1. Go to **Actions** tab in GitHub
2. Click on **Deploy to Cloud Run** workflow
3. Select a run to see details

### Workflow Status Indicators

- ✅ Green checkmark: Job completed successfully
- ❌ Red X: Job failed
- 🟡 Yellow circle: Job in progress
- ⚪ Gray circle: Job skipped (condition not met)

### View Logs

1. Click on a workflow run
2. Click on the job name (e.g., `deploy-backend`)
3. Expand individual steps to see logs
4. Look for:
   - Build output
   - Push confirmation
   - Deployment status

## Troubleshooting

### Workflow Not Triggering

**Possible Causes**:
- Changes not in `frontend/` or `backend/` directories
- Pushing to branch other than `main`
- Workflow file has syntax errors

**Solution**:
- Verify file paths in your commit
- Check branch name
- Review workflow file syntax in Actions tab

### Build Failures

**Common Issues**:

1. **Dockerfile not found**
   - Ensure `backend/Dockerfile` or `frontend/Dockerfile` exists
   - Check working directory in workflow

2. **Dependencies missing**
   - Verify `requirements.txt` (backend) or `package.json` (frontend)
   - Check Dockerfile COPY commands

3. **Authentication errors**
   - Verify `GCP_SERVICE_ACCOUNT_KEY` secret is set correctly
   - Check service account has required permissions

### Push Failures

**Common Issues**:

1. **Artifact Registry doesn't exist**
   - Create repository: `cart-pilot` in `europe-west1`
   - Verify repository name matches workflow

2. **Insufficient permissions**
   - Service account needs `roles/artifactregistry.writer`
   - Verify IAM bindings

3. **Docker authentication failed**
   - Check `gcloud auth configure-docker` step
   - Verify region matches repository location

### Deployment Failures

**Common Issues**:

1. **Service doesn't exist**
   - First deployment may need manual creation
   - Check Cloud Run console for errors

2. **Image not found**
   - Verify image was pushed successfully
   - Check image path matches deployment command

3. **Environment variables missing**
   - Verify all secrets are set
   - Check `--set-env-vars` syntax

4. **Backend URL not found (frontend)**
   - Ensure backend service exists before frontend deployment
   - Check backend service name matches: `cart-pilot-backend`

### Frontend Can't Connect to Backend

**Possible Causes**:
- Backend URL not set correctly in build args
- Backend service not deployed yet
- CORS issues in backend

**Solution**:
- Check build logs for `BACKEND_URL` value
- Verify backend service is running
- Review backend CORS configuration

## Best Practices

### 1. Deploy Backend First

Always deploy backend before frontend:
- Frontend build requires backend URL
- Backend must exist for frontend to connect

### 2. Test Locally First

Before pushing to `main`:
- Test Docker builds locally
- Verify Dockerfiles work correctly
- Check environment variables

### 3. Monitor Deployments

After deployment:
- Check Cloud Run logs
- Verify services are running
- Test frontend-to-backend connection

### 4. Use Commit Messages

Write clear commit messages:
- Helps identify deployments
- Makes rollback easier
- Improves debugging

### 5. Review Workflow Logs

Always review workflow logs:
- Catch errors early
- Understand deployment process
- Debug issues quickly

## Rollback Procedure

### Option 1: Redeploy Previous Commit

1. Find previous commit SHA
2. Manually trigger workflow
3. Select previous commit
4. Run workflow

### Option 2: Use Cloud Run Revisions

1. Go to Cloud Run console
2. Select service
3. Go to **Revisions** tab
4. Find previous revision
5. Click **Manage Traffic**
6. Route 100% traffic to previous revision

### Option 3: Manual Deployment

```bash
# Get previous image SHA
gcloud artifacts docker images list \
  europe-west1-docker.pkg.dev/{PROJECT_ID}/cart-pilot/cart-pilot-backend

# Deploy specific image
gcloud run deploy cart-pilot-backend \
  --image europe-west1-docker.pkg.dev/{PROJECT_ID}/cart-pilot/cart-pilot-backend:{SHA} \
  --region europe-west1
```

## Workflow Optimization

### Current Optimizations

1. **Path-based filtering**: Only builds changed services
2. **Parallel execution**: Backend and frontend can run simultaneously
3. **Conditional execution**: Jobs skip when not needed

### Future Enhancements

Potential improvements:
- Caching Docker layers for faster builds
- Matrix builds for multiple regions
- Integration tests before deployment
- Automated rollback on health check failure

## Security Considerations

### Secrets Management

- ✅ Secrets stored in GitHub Secrets (encrypted)
- ✅ Never exposed in logs
- ✅ Rotated periodically

### Service Account Permissions

- ✅ Minimal required permissions
- ✅ Separate service account for CI/CD
- ✅ No production credentials in workflow

### Image Security

- ✅ Images pushed to private Artifact Registry
- ✅ Immutable tags via commit SHA
- ✅ No secrets in Docker images

## Related Documentation

- [DEPLOYMENT.md](./DEPLOYMENT.md) - Complete deployment guide
- [README.md](./README.md) - Project overview
- [frontend/README.md](./frontend/README.md) - Frontend documentation
- [backend/apidoc.md](./backend/apidoc.md) - API documentation

## Support

For issues or questions:
1. Check workflow logs in GitHub Actions
2. Review Cloud Run logs
3. Consult [DEPLOYMENT.md](./DEPLOYMENT.md) troubleshooting section
4. Review this documentation

