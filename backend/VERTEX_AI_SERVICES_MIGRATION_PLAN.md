# Plan: Migrate to Vertex AI Services (GCS Artifacts, Sessions, and Memory)

## Overview
Migrate from in-memory services to production-ready Vertex AI services:
1. **GcsArtifactService**: Persistent artifact storage in Google Cloud Storage
2. **VertexAiSessionService**: Scalable session management via Vertex AI Agent Engine
3. **VertexAiMemoryBankService**: Persistent memory storage for cross-session context

This migration enables:
- **Persistence**: All data survives application restarts
- **Scalability**: Services accessible across multiple Cloud Run instances
- **Production Ready**: Enterprise-grade reliability and performance
- **Better Architecture**: Aligns with ADK best practices for production deployments

## Current State Analysis

### Current Implementation
**Location**: `backend/app/agent_executor.py` lines 20-23, 63-65

**Current Services**:
- **Artifact Service**: `InMemoryArtifactService()` - in-memory only, data lost on restart
- **Session Service**: `InMemorySessionService()` - sessions don't persist across restarts
- **Memory Service**: `InMemoryMemoryService()` - memory not persisted

**Limitations**: 
- All data lost on application restart
- Not suitable for production
- Can't share data across multiple Cloud Run instances
- No cross-session memory capabilities
- Limited scalability

### Current Image Handling
- Images are stored in session state (`current_image_bytes`, `current_image_mime_type`)
- Images are passed to tools via `tool_context.state`
- This approach works but doesn't leverage ADK's artifact system

## Benefits of Migration

### Artifacts (GcsArtifactService)
1. **Persistence**: Artifacts survive application restarts
2. **Scalability**: Artifacts accessible across multiple Cloud Run instances
3. **Versioning**: Automatic versioning of artifacts
4. **Cost Effective**: Pay only for storage used

### Sessions (VertexAiSessionService)
1. **Persistent Sessions**: Conversation history survives restarts
2. **Scalable**: Handles high concurrency across instances
3. **Managed Service**: No database management required
4. **Integration**: Seamless integration with Vertex AI features

### Memory (VertexAiMemoryBankService)
1. **Cross-Session Memory**: Users' preferences and history persist across conversations
2. **Semantic Search**: Find relevant memories using natural language queries
3. **Long-Term Context**: Build relationships with users over time
4. **Personalization**: Enable personalized experiences based on past interactions

## Migration Plan

### Phase 1: Configuration Setup

#### 1.1 Add Vertex AI Configuration to Settings
**File**: `backend/app/common/config.py`

**Changes**:
- Add required configuration fields for Vertex AI services
- Note: PROJECT_ID and REGION already exist in Settings

```python
# GCS Artifact Service Configuration
GCS_ARTIFACT_BUCKET: str = Field(
    ..., 
    description="GCS bucket name for artifact storage"
)

# Vertex AI Session and Memory Service Configuration
VERTEXAI_AGENT_ENGINE_ID: str = Field(
    ...,
    description="Vertex AI Agent Engine ID. Format: projects/PROJECT_ID/locations/LOCATION/reasoningEngines/ENGINE_ID"
)
# Note: PROJECT_ID and REGION already exist in Settings
```

#### 1.2 Environment Variables
Add to `.env` and deployment configuration:
```bash
# GCS Artifact Storage (Required)
GCS_ARTIFACT_BUCKET=your-project-artifacts-bucket

# Vertex AI Services (Required)
VERTEXAI_AGENT_ENGINE_ID=projects/YOUR_PROJECT_ID/locations/YOUR_REGION/reasoningEngines/YOUR_ENGINE_ID
```

### Phase 2: Infrastructure Setup

#### 2.1 Prerequisites
- GCP project with billing enabled
- Vertex AI API enabled
- Vertex AI Agent Engine created (Reasoning Engine)
- GCS bucket for artifacts

#### 2.2 Create Vertex AI Agent Engine
**Purpose**: Required for VertexAiSessionService and VertexAiMemoryBankService

**Steps**:
1. Enable Vertex AI API:
   ```bash
   gcloud services enable aiplatform.googleapis.com --project=YOUR_PROJECT_ID
   ```

2. Create Reasoning Engine (Agent Engine):
   - Via Console: Go to Vertex AI → Agent Builder → Create Agent Engine
   - Via API: Use Vertex AI API to create Reasoning Engine
   - Note the Engine ID: `projects/YOUR_PROJECT_ID/locations/YOUR_REGION/reasoningEngines/YOUR_ENGINE_ID`

**Documentation**: [Vertex AI Agent Engine Setup](https://cloud.google.com/vertex-ai/docs/agent-builder/create-agent-engine)

#### 2.3 Create GCS Bucket (For Artifacts)
**Steps**:
1. Create GCS bucket (via Console or gcloud):
   ```bash
   gsutil mb -p YOUR_PROJECT_ID -l YOUR_REGION gs://YOUR_PROJECT_ID-artifacts
   ```

2. Configure bucket settings:
   - **Location**: Same region as Cloud Run service (e.g., `us-central1`)
   - **Storage Class**: Standard (for frequent access)
   - **Access Control**: Uniform bucket-level access
   - **Lifecycle Policy**: Optional - configure retention if needed

#### 2.4 IAM Permissions
**Required Permissions** for Cloud Run service account:

**For Artifacts (GCS)**:
- `storage.objects.create` - To save artifacts
- `storage.objects.get` - To load artifacts
- `storage.objects.list` - To list artifacts

**For Sessions & Memory (Vertex AI)**:
- `aiplatform.sessions.create`
- `aiplatform.sessions.get`
- `aiplatform.sessions.list`
- `aiplatform.memoryBanks.create`
- `aiplatform.memoryBanks.get`
- `aiplatform.memoryBanks.search`

**Grant Permissions**:
```bash
# Get Cloud Run service account email
SERVICE_ACCOUNT=$(gcloud run services describe SERVICE_NAME \
  --region=REGION \
  --format="value(spec.template.spec.serviceAccountName)")

# Grant Storage Object Admin role (for artifacts)
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/storage.objectAdmin"

# Grant Vertex AI User role (for sessions and memory)
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/aiplatform.user"
```

**Alternative**: Use Application Default Credentials (ADC) if running locally or with Workload Identity.

#### 2.5 Install Required Packages
**File**: `backend/requirements.txt` or `backend/pyproject.toml`

**Add**:
```bash
# For Vertex AI services
google-adk[vertexai]>=0.1.0
```

**Note**: If already installed, ensure version includes Vertex AI support.

### Phase 3: Code Implementation

#### 3.1 Update Imports
**File**: `backend/app/agent_executor.py`

**Changes**:
```python
# Artifact Services
from google.adk.artifacts import GcsArtifactService

# Session Services
from google.adk.sessions import VertexAiSessionService

# Memory Services
from google.adk.memory import VertexAiMemoryBankService

from app.common.config import get_settings
```

#### 3.2 Create Service Factory Methods
**File**: `backend/app/agent_executor.py`

**Add factory methods**:
```python
def _create_artifact_service(self) -> GcsArtifactService:
    """Create GCS artifact service."""
    settings = get_settings()
    return GcsArtifactService(bucket_name=settings.GCS_ARTIFACT_BUCKET)

def _create_session_service(self) -> VertexAiSessionService:
    """Create Vertex AI session service."""
    settings = get_settings()
    return VertexAiSessionService(
        project=settings.PROJECT_ID,
        location=settings.REGION,
        agent_engine_id=settings.VERTEXAI_AGENT_ENGINE_ID
    )

def _create_memory_service(self) -> VertexAiMemoryBankService:
    """Create Vertex AI memory bank service."""
    settings = get_settings()
    return VertexAiMemoryBankService(
        project=settings.PROJECT_ID,
        location=settings.REGION,
        agent_engine_id=settings.VERTEXAI_AGENT_ENGINE_ID
    )

def _get_app_name(self) -> str:
    """Get app_name for Runner.
    
    For VertexAiSessionService, app_name should be the Reasoning Engine resource name.
    """
    settings = get_settings()
    return settings.VERTEXAI_AGENT_ENGINE_ID
```

#### 3.3 Update `__init__` Method
**File**: `backend/app/agent_executor.py`

**Changes**:
```python
def __init__(
    self,
    agent=None,
    status_message='Processing your shopping request...',
    artifact_name='response',
):
    """Initialize the shopping agent executor.

    Args:
        agent: The ADK agent instance (defaults to shopping_agent)
        status_message: Message to display while processing
        artifact_name: Name for the response artifact
    """
    self.agent = agent or shopping_agent
    self.status_message = status_message
    self.artifact_name = artifact_name

    # Create Vertex AI services
    artifact_service = self._create_artifact_service()
    session_service = self._create_session_service()
    memory_service = self._create_memory_service()
    app_name = self._get_app_name()

    # Initialize ADK Runner with Vertex AI services
    self.runner = Runner(
        app_name=app_name,
        agent=self.agent,
        artifact_service=artifact_service,
        session_service=session_service,
        memory_service=memory_service,
    )
    
    logger.info(f"Initialized Runner with app_name={app_name}")
    logger.info(f"Artifact Service: {type(artifact_service).__name__}")
    logger.info(f"Session Service: {type(session_service).__name__}")
    logger.info(f"Memory Service: {type(memory_service).__name__}")
```

#### 3.2 Optional: Migrate Image Storage to Artifacts
**Current**: Images stored in session state
**Proposed**: Store images as artifacts and reference them

**Benefits**:
- Better separation of concerns (binary data vs. state)
- Leverages ADK artifact versioning
- Reduces session state size

**Implementation** (Optional - can be done later):
1. Save image as artifact when received:
   ```python
   if image_bytes:
       artifact_filename = f"user:{user_id}/images/{session_id}_{timestamp}.{ext}"
       image_part = types.Part.from_bytes(
           data=image_bytes,
           mime_type=image_mime_type
       )
       await session.artifact_service.save_artifact(
           filename=artifact_filename,
           part=image_part
       )
       # Store artifact filename in state instead of bytes
       initial_state["current_image_artifact"] = artifact_filename
   ```

2. Load image from artifact when needed:
   ```python
   artifact_filename = tool_context.state.get("current_image_artifact")
   if artifact_filename:
       image_part = await tool_context.load_artifact(artifact_filename)
       image_bytes = image_part.inline_data.data
   ```

### Phase 4: Error Handling

#### 4.1 Error Handling
**File**: `backend/app/agent_executor.py`

**Add**:
- Try-catch around service initialization in `__init__`
- Log errors with context (bucket name, project, region, agent_engine_id)
- Provide clear error messages if services fail to initialize
- Fail fast on initialization errors (services are required)

**Example**:
```python
def __init__(self, ...):
    try:
        artifact_service = self._create_artifact_service()
        session_service = self._create_session_service()
        memory_service = self._create_memory_service()
        app_name = self._get_app_name()
        
        self.runner = Runner(...)
    except Exception as e:
        logger.error(f"Failed to initialize Vertex AI services: {e}")
        raise  # Fail fast - services are required
```

### Phase 5: Testing Strategy

#### 5.1 Unit Tests
**File**: `backend/tests/unit/test_agent_executor.py` (new)

**Test Cases for Artifact Service**:
1. Test `_create_artifact_service()` returns `GcsArtifactService` with correct bucket name
2. Test `_create_artifact_service()` with missing bucket in settings → raises `ValueError`

**Test Cases for Session Service**:
3. Test `_create_session_service()` returns `VertexAiSessionService` with correct project/location/engine_id
4. Test `_create_session_service()` with missing agent_engine_id → raises `ValueError`

**Test Cases for Memory Service**:
5. Test `_create_memory_service()` returns `VertexAiMemoryBankService` with correct project/location/engine_id
6. Test `_create_memory_service()` with missing agent_engine_id → raises `ValueError`

**Test Cases for App Name**:
7. Test `_get_app_name()` returns `VERTEXAI_AGENT_ENGINE_ID` from settings

**Test Cases for Runner Initialization**:
8. Test that Runner is initialized with all Vertex AI services
9. Test that Runner uses Reasoning Engine resource name as app_name
10. Test that initialization fails gracefully if services can't be created

#### 5.2 Integration Tests
**Test Cases for Artifacts**:
1. Save artifact to GCS and verify it exists
2. Load artifact from GCS and verify content
3. Test artifact versioning (save same filename twice)
4. Test artifact namespacing (session vs. user)

**Test Cases for Sessions**:
5. Create session with VertexAiSessionService and verify persistence
6. Retrieve existing session and verify state is preserved
7. Test session state updates persist across requests
8. Test multiple sessions for same user (different session_ids)
9. Test session listing for a user

**Test Cases for Memory**:
10. Add session to memory bank and verify it's stored
11. Search memory bank with natural language query
12. Verify memories persist across sessions
13. Test memory retrieval for specific user

**Test Cases for Combined Services**:
14. Test full flow: create session → save artifact → add to memory → retrieve in new session
15. Test cross-session memory retrieval
16. Test session state with artifacts and memory together

#### 5.3 Local Testing

**Setup**:
1. Create test GCS bucket
2. Create Vertex AI Agent Engine (Reasoning Engine)
3. Set up Application Default Credentials:
   ```bash
   gcloud auth application-default login
   ```
4. Set environment variables:
   ```bash
   export PROJECT_ID=your-test-project
   export REGION=us-central1
   export GOOGLE_API_KEY=your-api-key
   export GCS_ARTIFACT_BUCKET=test-artifacts-bucket
   export VERTEXAI_AGENT_ENGINE_ID=projects/YOUR_PROJECT_ID/locations/YOUR_REGION/reasoningEngines/YOUR_ENGINE_ID
   ```
5. Run application and verify:
   - Artifacts are saved to GCS
   - Sessions persist across restarts
   - Memory is searchable

### Phase 6: Deployment Strategy

#### 6.1 Deployment Plan

**Prerequisites**:
1. Create GCS bucket and set permissions
2. Create Vertex AI Agent Engine (Reasoning Engine)
3. Set up IAM permissions for Cloud Run service account
4. Configure environment variables in deployment

**Deployment Steps**:
1. Deploy to staging environment first
2. Verify all services initialize correctly
3. Test artifact save/load operations
4. Test session persistence across restarts
5. Test memory search functionality
6. Monitor for 1-2 weeks
7. Deploy to production
8. Monitor production metrics

#### 6.2 Monitoring
**Metrics to Monitor**:

**Artifacts (GCS)**:
- Artifact save/load success rates
- GCS API latency
- Error rates (permission errors, bucket not found, etc.)
- Storage costs and growth

**Sessions (Vertex AI)**:
- Session creation/retrieval success rates
- Vertex AI API latency
- Session state update success rates
- Number of active sessions
- Error rates (API errors, quota exceeded, etc.)

**Memory (Vertex AI)**:
- Memory add/search success rates
- Memory search latency
- Number of memories per user
- Memory storage costs
- Cross-session memory retrieval success

**Alerts**:
- High error rate for any service operations
- GCS bucket or Vertex AI API access failures
- Unusual storage growth or costs
- Vertex AI quota exceeded
- Service initialization failures

### Phase 7: Documentation Updates

#### 7.1 Environment Variables
Update `.env.example`:
```bash
# Artifact Storage Configuration
USE_GCS_ARTIFACTS=false
GCS_ARTIFACT_BUCKET=your-project-artifacts-bucket
```

#### 7.2 Deployment Guide
Add to deployment documentation:
- GCS bucket creation steps
- IAM permission setup
- Environment variable configuration
- Troubleshooting guide

## Implementation Checklist

### Configuration
- [ ] Add `GCS_ARTIFACT_BUCKET` to `Settings` class (required)
- [ ] Add `VERTEXAI_AGENT_ENGINE_ID` to `Settings` class (required)
- [ ] Update `.env.example` with new variables
- [ ] Ensure `google-adk[vertexai]` package is installed

### Infrastructure
- [ ] Enable Vertex AI API
- [ ] Create Vertex AI Agent Engine (Reasoning Engine)
- [ ] Create GCS bucket for artifacts
- [ ] Configure bucket settings (location, storage class, lifecycle)
- [ ] Grant IAM permissions to Cloud Run service account:
  - [ ] Storage Object Admin (for artifacts)
  - [ ] Vertex AI User (for sessions and memory)
- [ ] Test bucket access from Cloud Run
- [ ] Test Vertex AI API access from Cloud Run

### Code Changes
- [ ] Import Vertex AI services (`GcsArtifactService`, `VertexAiSessionService`, `VertexAiMemoryBankService`)
- [ ] Create `_create_artifact_service()` factory method (returns `GcsArtifactService`)
- [ ] Create `_create_session_service()` factory method (returns `VertexAiSessionService`)
- [ ] Create `_create_memory_service()` factory method (returns `VertexAiMemoryBankService`)
- [ ] Create `_get_app_name()` method (returns `VERTEXAI_AGENT_ENGINE_ID`)
- [ ] Update `__init__` to use all factory methods
- [ ] Add error handling in `__init__` (fail fast on initialization errors)
- [ ] Add logging for service initialization
- [ ] Update `SessionManager` if needed (app_name handling for Reasoning Engine)

### Testing
- [ ] Write unit tests for all service factory methods
- [ ] Write unit tests for `_get_app_name()` method
- [ ] Write integration tests for artifacts (save/load/versioning)
- [ ] Write integration tests for sessions (create/retrieve/persistence)
- [ ] Write integration tests for memory (add/search/cross-session)
- [ ] Test locally with Application Default Credentials
- [ ] Test in staging environment
- [ ] Test error scenarios (missing config, API failures, etc.)

### Deployment
- [ ] Deploy to staging environment
- [ ] Verify all services initialize correctly
- [ ] Test all functionality (artifacts, sessions, memory)
- [ ] Monitor staging for 1-2 weeks
- [ ] Deploy to production
- [ ] Monitor production metrics for all services
- [ ] Set up alerts for service failures

### Documentation
- [ ] Update README with Vertex AI setup instructions
- [ ] Document all environment variables
- [ ] Document Reasoning Engine creation process
- [ ] Add troubleshooting guide for all services
- [ ] Update deployment guide
- [ ] Document IAM permissions required
- [ ] Add cost estimation guide

## Risk Mitigation

### Risks

**Artifacts (GCS)**:
1. **GCS Bucket Not Found**: Application will fail to start (fail fast)
2. **Permission Errors**: Application will fail to start (fail fast)
3. **Cost Overruns**: Monitor storage usage, set lifecycle policies
4. **Performance Issues**: Monitor latency, consider caching

**Sessions (Vertex AI)**:
5. **Agent Engine Not Found**: Application will fail to start (fail fast)
6. **API Quota Exceeded**: Monitor usage, set up alerts
7. **Session Data Loss**: Ensure proper error handling, verify persistence
8. **Performance Degradation**: Monitor API latency, consider caching

**Memory (Vertex AI)**:
9. **Memory Search Failures**: Monitor and alert on failures
10. **Cross-Session Issues**: Test thoroughly, monitor memory retrieval
11. **Cost Overruns**: Monitor memory storage costs
12. **Privacy Concerns**: Ensure proper data handling, review memory content

### Mitigation Strategies
- Comprehensive error logging for all service initializations
- Monitoring and alerting for all services
- Cost monitoring and alerts (GCS storage, Vertex AI API calls)
- Quota monitoring and alerts
- Thorough testing before production deployment
- Fail fast on initialization errors (services are required)

## Future Enhancements (Post-Migration)

1. **Migrate Image Storage**: Store uploaded images as artifacts instead of session state
2. **Artifact Cleanup**: Implement cleanup strategy for old artifacts
3. **Artifact Sharing**: Use user namespacing for cross-session artifact access
4. **CDN Integration**: Serve artifacts via CDN for better performance
5. **Artifact Compression**: Compress large artifacts before storage

## Additional Considerations

### Cost Estimation

**GCS Artifacts**:
- Storage: ~$0.020 per GB/month (Standard storage)
- Operations: ~$0.05 per 10,000 operations
- Estimate: Low cost for typical usage (< 100GB storage, < 1M operations/month)

**Vertex AI Sessions**:
- API calls: Pricing varies by region and usage
- Storage: Managed by Vertex AI (included in API pricing)
- Estimate: Pay-per-use, typically low cost for moderate usage

**Vertex AI Memory**:
- API calls: Similar to sessions
- Storage: Managed by Vertex AI
- Estimate: Pay-per-use, cost increases with number of memories stored

### Migration Timeline Estimate

- **Infrastructure Setup**: 1-2 days (GCS bucket, Vertex AI Agent Engine, IAM)
- **Code Implementation**: 1-2 days
- **Testing**: 3-5 days (unit tests, integration tests, local testing)
- **Staging Deployment & Monitoring**: 1-2 weeks
- **Production Deployment**: 1 day
- **Total**: 3-4 weeks for complete migration

## References

- [ADK Artifacts Documentation](https://google.github.io/adk-docs/artifacts/)
- [ADK Sessions Documentation](https://google.github.io/adk-docs/sessions/session/)
- [ADK Memory Documentation](https://google.github.io/adk-docs/sessions/memory/)
- [GCS ArtifactService API](https://google.github.io/adk-docs/artifacts/#gcsartifactservice)
- [VertexAiSessionService](https://google.github.io/adk-docs/sessions/session/#vertexaisessionservice)
- [VertexAiMemoryBankService](https://google.github.io/adk-docs/sessions/memory/)
- [Google Cloud Storage Documentation](https://cloud.google.com/storage/docs)
- [Vertex AI Agent Engine Documentation](https://cloud.google.com/vertex-ai/docs/agent-builder/create-agent-engine)

