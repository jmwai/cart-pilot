# Shopping Agent Architecture Diagram

## ADK Runtime Architecture (Google Cloud)

```mermaid
graph TB
    %% User
    User[👤 User]
    
    %% Cloud Run Services
    subgraph CloudRun["Google Cloud Run (europe-west1)"]
        direction TB
        
        %% Frontend Service
        subgraph FrontendService["Frontend Service: cart-pilot-frontend"]
            FrontendApp[Frontend Application<br/>Next.js UI<br/>A2A Client SDK]
        end
        
        %% Backend Service
        subgraph BackendService["Backend Service: cart-pilot-backend"]
            direction TB
            
            %% ADK Runtime (dashed box)
            subgraph ADKRuntime["Agent Development Kit Runtime"]
                direction TB
                
                Runner[Runner<br/>Event Processor<br/>ShoppingAgentExecutor]
                EventLoop[2. Event Loop<br/>Ask ↔ Yield]
                ExecutionLogic[Execution Logic<br/>Shopping Agent<br/>Sub-Agents<br/>LLM Innovation<br/>Callbacks<br/>Tools]
            end
            
            Services[Services<br/>Session Service<br/>Artifact Service<br/>Memory Service]
        end
    end
    
    %% External Services
    subgraph ExternalServices["External Services"]
        Storage[(Storage<br/>Cloud SQL<br/>PostgreSQL + pgvector)]
        VertexAI[Vertex AI<br/>Gemini 2.5 Flash<br/>Multimodal Embeddings]
    end
    
    %% Flow 1: User Request
    User -->|1. User: Help me to do...?<br/>session_id: 's_123'| FrontendApp
    
    %% Flow: Frontend to Backend
    FrontendApp -->|A2A Protocol Request| Runner
    
    %% Flow 2: Event Loop
    Runner -->|Ask| EventLoop
    EventLoop -->|Yield| Runner
    
    %% Flow 3: Stream Events
    Runner -->|3. Stream&lt;Event&gt;| FrontendApp
    FrontendApp -->|Stream&lt;Event&gt;| User
    
    %% Execution Logic to Vertex AI
    ExecutionLogic -->|LLM API Calls| VertexAI
    VertexAI -->|LLM Responses| ExecutionLogic
    
    %% Services interactions (dashed)
    Runner -.->|Uses| Services
    Services -.->|Persists/Retrieves| Storage
    
    %% Execution Logic uses Services
    ExecutionLogic -.->|Accesses| Services
    
    %% Styling
    classDef user fill:#e3f2fd,stroke:#1976d2,stroke-width:3px
    classDef frontend fill:#e1f5ff,stroke:#01579b,stroke-width:2px
    classDef backend fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef adk fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef services fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px
    classDef storage fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    classDef vertex fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    
    class User user
    class FrontendApp,FrontendService frontend
    class Runner,EventLoop,ExecutionLogic,BackendService backend
    class ADKRuntime adk
    class Services services
    class Storage storage
    class VertexAI vertex
    
    %% Make ADK Runtime box dashed
    style ADKRuntime stroke-dasharray: 8 4
    style FrontendService stroke-dasharray: 4 2
    style BackendService stroke-dasharray: 4 2
```

```mermaid
graph TB
    %% External Users
    subgraph External["External"]
        Users[Users/Browsers]
        GitHub[GitHub Repository]
    end

    %% CI/CD Pipeline
    subgraph CICD["CI/CD Pipeline (GitHub Actions)"]
        GitHubActions[GitHub Actions Workflow]
        BuildBackend[Build Backend Image]
        BuildFrontend[Build Frontend Image]
        PushImages[Push to Artifact Registry]
    end

    %% Google Cloud Project
    subgraph GCP["Google Cloud Project: gemini-adk-vertex-2025"]
        
        %% Artifact Registry
        subgraph ArtifactRegistry["Artifact Registry (europe-west1)"]
            ARRepo[cart-pilot Repository]
            BackendImage[cart-pilot-backend<br/>Docker Image]
            FrontendImage[cart-pilot-frontend<br/>Docker Image]
        end

        %% Secret Manager
        subgraph SecretManager["Secret Manager"]
            APIKeySecret[google-api-key]
            DBPasswordSecret[db-password]
            DBNameSecret[db-name]
            DBUserSecret[db-user]
            CloudSQLSecret[cloud-sql-connection-name]
        end

        %% Cloud Run Services
        subgraph CloudRun["Cloud Run (europe-west1)"]
            subgraph BackendService["Backend Service: cart-pilot-backend"]
                BackendContainer[Backend Container<br/>FastAPI + ADK<br/>Port: 8080<br/>Memory: 512Mi<br/>CPU: 1<br/>Min: 1, Max: 3]
                BackendEnv[Environment Variables<br/>PROJECT_ID<br/>REGION]
                BackendSecrets[Secrets<br/>GOOGLE_API_KEY<br/>DB_PASSWORD<br/>DB_NAME<br/>DB_USER<br/>CLOUD_SQL_CONNECTION_NAME]
            end
            
            subgraph FrontendService["Frontend Service: cart-pilot-frontend"]
                FrontendContainer[Frontend Container<br/>Next.js Standalone<br/>Port: 8080<br/>Memory: 512Mi<br/>CPU: 1<br/>Min: 1, Max: 3]
                FrontendEnv[Environment Variables<br/>NEXT_PUBLIC_AGENT_CARD_URL<br/>NEXT_PUBLIC_API_BASE_URL<br/>NEXT_PUBLIC_DEFAULT_USER_ID]
            end
        end

        %% Cloud SQL
        subgraph CloudSQL["Cloud SQL for PostgreSQL"]
            SQLInstance[(Cloud SQL Instance<br/>PostgreSQL with pgvector)]
            SQLDatabase[(Database<br/>Catalog Items<br/>Cart Items<br/>Orders<br/>Payments<br/>Inquiries)]
        end

        %% Vertex AI Services
        subgraph VertexAI["Vertex AI (europe-west1)"]
            GeminiModel[Gemini 2.5 Flash<br/>LLM Inference]
            EmbeddingModel[Multimodal Embedding<br/>Text & Image Embeddings]
        end

        %% IAM & Security
        subgraph IAM["IAM & Security"]
            ServiceAccount[GitHub Actions<br/>Service Account]
            CloudRunSA[Cloud Run<br/>Service Account]
            IAMPolicies[IAM Policies<br/>roles/run.admin<br/>roles/artifactregistry.writer<br/>roles/iam.serviceAccountUser]
        end

        %% VPC & Networking
        subgraph Networking["Networking"]
            CloudSQLProxy[Cloud SQL Proxy<br/>Unix Socket Connection]
            LoadBalancer[Cloud Load Balancer<br/>HTTPS]
            CloudRunURLs[Cloud Run URLs<br/>*.run.app]
        end
    end

    %% Application Components (inside containers)
    subgraph BackendApp["Backend Application Components"]
        A2AProtocol[A2A Protocol Handler]
        AgentExecutor[ShoppingAgentExecutor]
        ADKRunner[ADK Runner]
        ShoppingAgent[Shopping Agent]
        SubAgents[Sub-Agents<br/>Product Discovery<br/>Cart<br/>Checkout<br/>Payment<br/>Customer Service]
        Tools[Agent Tools]
        SessionService[DatabaseSessionService]
    end

    subgraph FrontendApp["Frontend Application Components"]
        NextJSApp[Next.js Application]
        A2AClient[A2A Client SDK]
        Chatbox[Chatbox UI]
        ArtifactDisplay[Artifact Display]
    end

    %% Flow connections
    Users -->|HTTPS| LoadBalancer
    LoadBalancer -->|Routes| CloudRunURLs
    CloudRunURLs -->|HTTPS| FrontendService
    CloudRunURLs -->|HTTPS| BackendService

    GitHub -->|Push Events| GitHubActions
    GitHubActions -->|Triggers| BuildBackend
    GitHubActions -->|Triggers| BuildFrontend
    BuildBackend -->|Builds| BackendImage
    BuildFrontend -->|Builds| FrontendImage
    PushImages -->|Pushes| ARRepo
    ARRepo -->|Stores| BackendImage
    ARRepo -->|Stores| FrontendImage

    BackendImage -->|Deploys| BackendContainer
    FrontendImage -->|Deploys| FrontendContainer

    SecretManager -->|Provides Secrets| BackendSecrets
    ServiceAccount -->|Authenticates| GitHubActions
    CloudRunSA -->|Runs| BackendContainer
    CloudRunSA -->|Runs| FrontendContainer
    IAMPolicies -->|Grants Permissions| ServiceAccount

    BackendContainer -->|Contains| A2AProtocol
    A2AProtocol -->|Uses| AgentExecutor
    AgentExecutor -->|Uses| ADKRunner
    ADKRunner -->|Executes| ShoppingAgent
    ShoppingAgent -->|Delegates| SubAgents
    SubAgents -->|Calls| Tools
    ADKRunner -->|Uses| SessionService

    FrontendContainer -->|Contains| NextJSApp
    NextJSApp -->|Uses| A2AClient
    A2AClient -->|Displays| Chatbox
    A2AClient -->|Displays| ArtifactDisplay

    FrontendApp -->|A2A Protocol| BackendApp
    A2AClient -->|HTTP Requests| A2AProtocol

    BackendContainer -->|Connects via| CloudSQLProxy
    CloudSQLProxy -->|Unix Socket| SQLInstance
    SQLInstance -->|Stores Data| SQLDatabase
    SessionService -->|Persists Sessions| SQLDatabase
    Tools -->|Queries| SQLDatabase

    BackendContainer -->|API Calls| GeminiModel
    BackendContainer -->|API Calls| EmbeddingModel
    Tools -->|Generates Embeddings| EmbeddingModel
    ShoppingAgent -->|LLM Inference| GeminiModel
    SubAgents -->|LLM Inference| GeminiModel

    %% Styling
    classDef external fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef cicd fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef gcp fill:#f1f8e9,stroke:#558b2f,stroke-width:2px
    classDef cloudrun fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    classDef database fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px
    classDef vertex fill:#fff9c4,stroke:#f9a825,stroke-width:2px
    classDef security fill:#ffebee,stroke:#d32f2f,stroke-width:2px
    classDef app fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    
    class Users,GitHub external
    class GitHubActions,BuildBackend,BuildFrontend,PushImages cicd
    class ARRepo,BackendImage,FrontendImage,SecretManager,APIKeySecret,DBPasswordSecret,DBNameSecret,DBUserSecret,CloudSQLSecret,LoadBalancer,CloudRunURLs,CloudSQLProxy gcp
    class BackendService,FrontendService,BackendContainer,FrontendContainer,BackendEnv,FrontendEnv,BackendSecrets cloudrun
    class SQLInstance,SQLDatabase database
    class GeminiModel,EmbeddingModel vertex
    class ServiceAccount,CloudRunSA,IAMPolicies security
    class A2AProtocol,AgentExecutor,ADKRunner,ShoppingAgent,SubAgents,Tools,SessionService,NextJSApp,A2AClient,Chatbox,ArtifactDisplay app
```

## Deployment Architecture Details

### Cloud Run Services

#### Backend Service (`cart-pilot-backend`)
- **Runtime**: Python 3.11 (Docker)
- **Framework**: FastAPI + Starlette (A2A Protocol)
- **Port**: 8080
- **Resources**:
  - Memory: 512Mi
  - CPU: 1
  - Min Instances: 1 (always warm)
  - Max Instances: 3
  - Timeout: 300s
- **Authentication**: Unauthenticated (public)
- **Environment Variables**:
  - `PROJECT_ID`: GCP Project ID
  - `REGION`: europe-west1
- **Secrets** (from Secret Manager):
  - `GOOGLE_API_KEY`: Vertex AI API key
  - `DB_PASSWORD`: Cloud SQL password
  - `DB_NAME`: Database name
  - `DB_USER`: Database user
  - `CLOUD_SQL_CONNECTION_NAME`: Cloud SQL connection string

#### Frontend Service (`cart-pilot-frontend`)
- **Runtime**: Node.js 20 (Docker)
- **Framework**: Next.js (Standalone build)
- **Port**: 8080
- **Resources**:
  - Memory: 512Mi
  - CPU: 1
  - Min Instances: 1
  - Max Instances: 3
  - Timeout: 300s
- **Authentication**: Unauthenticated (public)
- **Environment Variables**:
  - `NEXT_PUBLIC_AGENT_CARD_URL`: Backend agent card endpoint
  - `NEXT_PUBLIC_API_BASE_URL`: Backend service URL
  - `NEXT_PUBLIC_DEFAULT_USER_ID`: Default user ID

### Cloud SQL Database

- **Type**: Cloud SQL for PostgreSQL
- **Extension**: pgvector (for vector similarity search)
- **Connection**: Unix socket via Cloud SQL Proxy
- **Connection Name**: Stored in Secret Manager
- **Tables**:
  - `catalog_items`: Products with embeddings
  - `cart_items`: Shopping cart items
  - `orders`: Customer orders
  - `order_items`: Order line items
  - `mandates`: AP2 payment mandates
  - `payments`: Payment records
  - `customer_inquiries`: Support tickets

### Artifact Registry

- **Repository**: `cart-pilot`
- **Region**: `europe-west1`
- **Format**: Docker
- **Images**:
  - `cart-pilot-backend`: Backend service image
  - `cart-pilot-frontend`: Frontend service image
- **Tags**: `latest` and `{GITHUB_SHA}`

### Secret Manager

Stores sensitive configuration:
- `google-api-key`: Vertex AI API key
- `db-password`: Cloud SQL database password
- `db-name`: Database name
- `db-user`: Database username
- `cloud-sql-connection-name`: Cloud SQL connection string

### Vertex AI Services

- **Gemini 2.5 Flash**: LLM for agent inference
- **Multimodal Embedding Model**: Text and image embeddings for product search
- **Region**: europe-west1
- **Authentication**: Via GOOGLE_API_KEY

### CI/CD Pipeline

**GitHub Actions Workflow**:
1. **Trigger**: Push to `main` branch (changes in `frontend/**` or `backend/**`)
2. **Check Changes**: Determines which services need deployment
3. **Build**: Creates Docker images
4. **Push**: Uploads to Artifact Registry
5. **Deploy**: Updates Cloud Run services

**Service Account Permissions**:
- `roles/run.admin`: Deploy to Cloud Run
- `roles/artifactregistry.writer`: Push images
- `roles/iam.serviceAccountUser`: Use service accounts

## Network Flow

1. **User Request** → Cloud Load Balancer → Cloud Run URL
2. **Frontend** → Serves static assets and Next.js app
3. **Frontend A2A Client** → HTTP requests to Backend service
4. **Backend** → Processes A2A protocol requests
5. **Backend** → Connects to Cloud SQL via Unix socket
6. **Backend** → Calls Vertex AI APIs for LLM inference
7. **Backend** → Streams responses back to Frontend
8. **Frontend** → Updates UI with artifacts and responses

## Security Architecture

- **Secrets**: Stored in Secret Manager, injected at runtime
- **IAM**: Service accounts with least-privilege access
- **Network**: Cloud SQL uses private Unix socket connections
- **Authentication**: Public endpoints (can be secured with Cloud IAP)
- **HTTPS**: All traffic encrypted via Cloud Load Balancer

## Scalability

- **Auto-scaling**: Cloud Run scales 1-3 instances based on traffic
- **Connection Pooling**: Database connections pooled (max 10)
- **Stateless**: Both services are stateless (state in database)
- **Session Persistence**: DatabaseSessionService stores sessions in Cloud SQL

## Monitoring & Logging

- **Cloud Logging**: Automatic logging from Cloud Run
- **Cloud Monitoring**: Metrics and health checks
- **Error Reporting**: Automatic error tracking
- **Trace**: Request tracing across services

## CI/CD Deployment Flow

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant GitHub as GitHub Repo
    participant Actions as GitHub Actions
    participant Docker as Docker Build
    participant AR as Artifact Registry
    participant CR as Cloud Run
    participant SM as Secret Manager
    participant DB as Cloud SQL

    Dev->>GitHub: Push code to main branch
    GitHub->>Actions: Trigger workflow (on push)
    
    Actions->>Actions: Check changed paths<br/>(backend/** or frontend/**)
    
    alt Backend Changes
        Actions->>Docker: Build backend image<br/>(Python 3.11 + FastAPI)
        Docker->>Docker: Install dependencies<br/>Copy application code
        Docker->>AR: Push image<br/>(cart-pilot-backend:{SHA})
        AR->>CR: Deploy to cart-pilot-backend
        CR->>SM: Fetch secrets<br/>(GOOGLE_API_KEY, DB_*)
        CR->>DB: Connect via Cloud SQL Proxy
        CR-->>Actions: Deployment successful
    end
    
    alt Frontend Changes
        Actions->>CR: Get backend service URL
        CR-->>Actions: Backend URL
        Actions->>Docker: Build frontend image<br/>(Next.js standalone)
        Docker->>Docker: Install dependencies<br/>Build Next.js app<br/>Set env vars
        Docker->>AR: Push image<br/>(cart-pilot-frontend:{SHA})
        AR->>CR: Deploy to cart-pilot-frontend
        CR-->>Actions: Deployment successful
    end
    
    Actions-->>GitHub: Update deployment status
    GitHub-->>Dev: Deployment complete
```

## Request Flow Through Google Cloud

```mermaid
graph LR
    Frontend[Frontend Service<br/>Cloud Run<br/>Next.js]
    Backend[Backend Service<br/>Cloud Run<br/>FastAPI + ADK]
    SecretMgr[Secret Manager<br/>API Keys & DB Credentials]
    CloudSQL[Cloud SQL<br/>PostgreSQL + pgvector]
    VertexAI[Vertex AI<br/>Gemini & Embeddings]

    Frontend -->|A2A Protocol<br/>HTTP POST| Backend
    Backend -->|Fetch Secrets| SecretMgr
    SecretMgr -->|Return Credentials| Backend
    Backend -->|Unix Socket<br/>/cloudsql/connection-name| CloudSQL
    Backend -->|LLM API Calls| VertexAI
    Backend -->|Generate Embeddings| VertexAI
    VertexAI -->|Return Embeddings| Backend
    Backend -->|Vector Search| CloudSQL
    Backend -->|Query/Update<br/>Products, Cart, Orders| CloudSQL
    CloudSQL -->|Return Results| Backend
    Backend -->|Stream Response<br/>Text + Artifacts| Frontend

    %% Styling
    classDef frontend fill:#e1f5ff,stroke:#01579b,stroke-width:2px
    classDef backend fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef database fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    classDef vertex fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    classDef secret fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px
    
    class Frontend frontend
    class Backend backend
    class CloudSQL database
    class VertexAI vertex
    class SecretMgr secret
```

```mermaid
graph TB
    %% Frontend Layer
    subgraph Frontend["Frontend (Next.js)"]
        UI[User Interface]
        A2AClient[A2A Client SDK]
        Chatbox[Chatbox Component]
        ArtifactDisplay[Artifact Display Components]
    end

    %% API Gateway Layer
    subgraph Backend["Backend (Starlette/FastAPI)"]
        subgraph A2AProtocol["A2A Protocol Layer"]
            AgentCard[Agent Card Endpoint]
            RequestHandler[Default Request Handler]
            TaskStore[InMemory Task Store]
        end
        
        subgraph Executor["Agent Executor"]
            ShoppingExecutor[ShoppingAgentExecutor]
            MessageParser[Message Parser]
            ContentBuilder[Content Builder]
            SessionManager[Session Manager]
            StateTracker[State Tracker]
            ArtifactStreamer[Artifact Streamer]
            StatusHandler[Status Message Handler]
        end
        
        subgraph ADKCore["ADK Core Services"]
            Runner[ADK Runner]
            SessionService[DatabaseSessionService]
            ArtifactService[InMemoryArtifactService]
            MemoryService[InMemoryMemoryService]
        end
    end

    %% Agent Layer
    subgraph Agents["Agent Hierarchy"]
        RootAgent[Shopping Agent<br/>Root Orchestrator]
        
        subgraph SubAgents["Sub-Agents"]
            ProductAgent[Product Discovery Agent]
            CartAgent[Cart Agent]
            CheckoutAgent[Checkout Agent]
            CustomerAgent[Customer Service Agent]
            PaymentAgent[Payment Agent]
        end
    end

    %% Tools Layer
    subgraph Tools["Agent Tools"]
        subgraph ProductTools["Product Discovery Tools"]
            TextSearch[text_vector_search]
            ImageSearch[image_vector_search]
        end
        
        subgraph CartTools["Cart Tools"]
            AddToCart[add_to_cart]
            GetCart[get_cart]
            UpdateCart[update_cart_item]
            RemoveCart[remove_from_cart]
            ClearCart[clear_cart]
            CartTotal[get_cart_total]
        end
        
        subgraph CheckoutTools["Checkout Tools"]
            ValidateCart[validate_cart_for_checkout]
            CreateOrder[create_order]
            OrderStatus[get_order_status]
            CancelOrder[cancel_order]
        end
        
        subgraph PaymentTools["Payment Tools"]
            GetPaymentMethods[get_available_payment_methods]
            CreateCartMandate[create_cart_mandate]
            CreatePaymentMandate[create_payment_mandate]
            ProcessPayment[process_payment]
        end
        
        subgraph CustomerTools["Customer Service Tools"]
            CreateInquiry[create_inquiry]
            GetInquiryStatus[get_inquiry_status]
            SearchFAQ[search_faq]
            InitiateReturn[initiate_return]
        end
    end

    %% Database Layer
    subgraph Database["PostgreSQL Database"]
        subgraph Models["Data Models"]
            CatalogItems[CatalogItem<br/>with pgvector embeddings]
            CartItems[CartItem]
            Orders[Order]
            OrderItems[OrderItem]
            Mandates[Mandate]
            Payments[Payment]
            Inquiries[CustomerInquiry]
        end
        
        DBConnection[(PostgreSQL<br/>with pgvector)]
    end

    %% External Services
    subgraph External["External Services"]
        VertexAI[Vertex AI<br/>Gemini Model]
        EmbeddingService[Vertex AI<br/>Multimodal Embedding]
    end

    %% Flow connections
    UI -->|User Input| A2AClient
    A2AClient -->|A2A Protocol| AgentCard
    AgentCard --> RequestHandler
    RequestHandler --> ShoppingExecutor
    
    ShoppingExecutor --> MessageParser
    ShoppingExecutor --> ContentBuilder
    ShoppingExecutor --> SessionManager
    ShoppingExecutor --> StateTracker
    ShoppingExecutor --> ArtifactStreamer
    ShoppingExecutor --> StatusHandler
    ShoppingExecutor --> Runner
    
    Runner --> SessionService
    Runner --> ArtifactService
    Runner --> MemoryService
    Runner --> RootAgent
    
    RootAgent -->|Delegates| ProductAgent
    RootAgent -->|Delegates| CartAgent
    RootAgent -->|Delegates| CheckoutAgent
    RootAgent -->|Delegates| CustomerAgent
    RootAgent -->|Delegates| PaymentAgent
    
    ProductAgent --> TextSearch
    ProductAgent --> ImageSearch
    
    CartAgent --> AddToCart
    CartAgent --> GetCart
    CartAgent --> UpdateCart
    CartAgent --> RemoveCart
    CartAgent --> ClearCart
    CartAgent --> CartTotal
    
    CheckoutAgent --> ValidateCart
    CheckoutAgent --> CreateOrder
    CheckoutAgent --> OrderStatus
    CheckoutAgent --> CancelOrder
    
    PaymentAgent --> GetPaymentMethods
    PaymentAgent --> CreateCartMandate
    PaymentAgent --> CreatePaymentMandate
    PaymentAgent --> ProcessPayment
    
    CustomerAgent --> CreateInquiry
    CustomerAgent --> GetInquiryStatus
    CustomerAgent --> SearchFAQ
    CustomerAgent --> InitiateReturn
    
    TextSearch --> DBConnection
    ImageSearch --> DBConnection
    AddToCart --> DBConnection
    GetCart --> DBConnection
    UpdateCart --> DBConnection
    RemoveCart --> DBConnection
    ClearCart --> DBConnection
    CartTotal --> DBConnection
    ValidateCart --> DBConnection
    CreateOrder --> DBConnection
    OrderStatus --> DBConnection
    CancelOrder --> DBConnection
    CreateCartMandate --> DBConnection
    CreatePaymentMandate --> DBConnection
    ProcessPayment --> DBConnection
    CreateInquiry --> DBConnection
    GetInquiryStatus --> DBConnection
    SearchFAQ --> DBConnection
    InitiateReturn --> DBConnection
    
    DBConnection --> CatalogItems
    DBConnection --> CartItems
    DBConnection --> Orders
    DBConnection --> OrderItems
    DBConnection --> Mandates
    DBConnection --> Payments
    DBConnection --> Inquiries
    
    TextSearch --> EmbeddingService
    ImageSearch --> EmbeddingService
    
    RootAgent --> VertexAI
    ProductAgent --> VertexAI
    CartAgent --> VertexAI
    CheckoutAgent --> VertexAI
    CustomerAgent --> VertexAI
    PaymentAgent --> VertexAI
    
    SessionService -->|Persists State| DBConnection
    
    Runner -->|Streams Events| ArtifactStreamer
    ArtifactStreamer -->|A2A Events| RequestHandler
    RequestHandler -->|A2A Response| A2AClient
    A2AClient -->|Updates UI| Chatbox
    A2AClient -->|Displays Artifacts| ArtifactDisplay

    %% Styling
    classDef frontend fill:#e1f5ff,stroke:#01579b,stroke-width:2px
    classDef backend fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef agent fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef tool fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px
    classDef database fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    classDef external fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    
    class UI,A2AClient,Chatbox,ArtifactDisplay frontend
    class AgentCard,RequestHandler,TaskStore,ShoppingExecutor,MessageParser,ContentBuilder,SessionManager,StateTracker,ArtifactStreamer,StatusHandler,Runner,SessionService,ArtifactService,MemoryService backend
    class RootAgent,ProductAgent,CartAgent,CheckoutAgent,CustomerAgent,PaymentAgent agent
    class TextSearch,ImageSearch,AddToCart,GetCart,UpdateCart,RemoveCart,ClearCart,CartTotal,ValidateCart,CreateOrder,OrderStatus,CancelOrder,GetPaymentMethods,CreateCartMandate,CreatePaymentMandate,ProcessPayment,CreateInquiry,GetInquiryStatus,SearchFAQ,InitiateReturn tool
    class DBConnection,CatalogItems,CartItems,Orders,OrderItems,Mandates,Payments,Inquiries database
    class VertexAI,EmbeddingService external
```

## User Journey Flow Diagram

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant A2AProtocol
    participant Executor
    participant ShoppingAgent
    participant SubAgent
    participant Tools
    participant Database
    participant VertexAI

    User->>Frontend: "Find me running shoes"
    Frontend->>A2AProtocol: A2A Request (text)
    A2AProtocol->>Executor: Parse & Create Session
    Executor->>ShoppingAgent: Execute with message
    
    ShoppingAgent->>ShoppingAgent: Analyze Intent
    ShoppingAgent->>SubAgent: Transfer to Product Discovery Agent
    
    SubAgent->>Tools: text_vector_search("running shoes")
    Tools->>Database: Query with embeddings
    Database-->>Tools: Product results
    Tools->>Database: Store in session state["current_results"]
    Tools-->>SubAgent: Return products
    SubAgent-->>ShoppingAgent: Product list
    ShoppingAgent-->>Executor: Response with products
    Executor->>A2AProtocol: Stream artifacts (products)
    A2AProtocol-->>Frontend: Display products
    
    User->>Frontend: "Add the blue ones"
    Frontend->>A2AProtocol: A2A Request
    A2AProtocol->>Executor: Get existing session
    Executor->>ShoppingAgent: Execute
    
    ShoppingAgent->>SubAgent: Transfer to Cart Agent
    SubAgent->>Tools: add_to_cart("blue ones")
    Tools->>Tools: Match "blue ones" from state["current_results"]
    Tools->>Database: Insert CartItem
    Tools->>Database: Update state["cart"]
    Tools-->>SubAgent: Cart updated
    SubAgent-->>ShoppingAgent: Cart confirmation
    ShoppingAgent-->>Executor: Response
    Executor->>A2AProtocol: Stream cart artifact
    A2AProtocol-->>Frontend: Display cart
    
    User->>Frontend: "Checkout"
    Frontend->>A2AProtocol: A2A Request
    A2AProtocol->>Executor: Execute
    Executor->>ShoppingAgent: Execute
    
    ShoppingAgent->>SubAgent: Transfer to Checkout Agent
    SubAgent->>Tools: validate_cart_for_checkout()
    Tools->>Database: Query cart
    Tools-->>SubAgent: Cart valid
    SubAgent->>Tools: Prepare order summary
    Tools->>Database: Update state["order_summary"]
    SubAgent-->>ShoppingAgent: Order summary
    ShoppingAgent-->>Executor: Show summary
    Executor-->>Frontend: Display order summary
    
    User->>Frontend: "Yes, confirm"
    Frontend->>A2AProtocol: A2A Request
    A2AProtocol->>Executor: Execute
    Executor->>ShoppingAgent: Execute
    
    ShoppingAgent->>SubAgent: Transfer to Payment Agent
    SubAgent->>Tools: get_available_payment_methods()
    Tools-->>SubAgent: Payment methods
    SubAgent-->>ShoppingAgent: Show payment options
    ShoppingAgent-->>Frontend: Display payment methods
    
    User->>Frontend: Select payment method + "place order"
    Frontend->>A2AProtocol: A2A Request
    A2AProtocol->>Executor: Execute
    Executor->>ShoppingAgent: Execute
    
    ShoppingAgent->>SubAgent: Transfer to Payment Agent
    SubAgent->>Tools: create_cart_mandate()
    SubAgent->>Tools: create_payment_mandate()
    SubAgent->>Tools: process_payment()
    Tools->>Database: Create Mandate & Payment records
    Tools->>Database: Update state["payment_processed"]
    Tools-->>SubAgent: Payment successful
    SubAgent-->>ShoppingAgent: "Payment processed successfully"
    
    Note over ShoppingAgent: Automatic continuation<br/>No user input needed
    ShoppingAgent->>SubAgent: Transfer to Checkout Agent (immediate)
    SubAgent->>Tools: create_order()
    Tools->>Database: Create Order & OrderItems
    Tools->>Database: Clear cart
    Tools-->>SubAgent: Order created
    SubAgent-->>ShoppingAgent: Order confirmation
    ShoppingAgent-->>Executor: Complete response
    Executor-->>Frontend: Order confirmation
    Frontend-->>User: "Your order has been placed!"
```

## Architecture Flow Description

### Request Flow

1. **User Input** → Frontend UI captures user message (text/image)
2. **A2A Client** → Wraps message in A2A protocol format with contextId
3. **Agent Card** → Returns agent capabilities metadata
4. **Request Handler** → Processes A2A request, creates task
5. **Agent Executor** → Parses message, manages session, builds content
6. **ADK Runner** → Executes agent with session context
7. **Shopping Agent** → Analyzes intent, delegates to sub-agent
8. **Sub-Agent** → Uses specialized tools to fulfill request
9. **Tools** → Interact with database, update session state
10. **State Updates** → Detected by executor, artifacts streamed back
11. **Response** → Streamed to frontend via A2A protocol

### Key Components

#### Frontend Layer
- **Next.js Application**: React-based UI
- **A2A Client SDK**: Handles agent-to-agent protocol communication
- **Chatbox**: Main conversation interface
- **Artifact Display**: Shows products, cart, orders as structured data

#### Backend Layer
- **A2A Protocol**: JSON-RPC 2.0 based agent communication
- **Agent Executor**: Bridges A2A to ADK, handles session management
- **ADK Runner**: Core agent execution engine
- **Session Service**: Database-backed persistent session storage
- **State Tracker**: Monitors state changes for artifact streaming

#### Agent Hierarchy
- **Shopping Agent**: Root orchestrator, routes to sub-agents
- **Product Discovery**: Semantic and visual product search
- **Cart Agent**: Shopping cart management
- **Checkout Agent**: Order creation and management
- **Payment Agent**: Payment processing with AP2 mandates
- **Customer Service**: Support, returns, inquiries

#### Database Layer
- **PostgreSQL**: Primary data store
- **pgvector**: Vector similarity search for products
- **Models**: Catalog, Cart, Orders, Payments, Inquiries

#### External Services
- **Vertex AI**: LLM inference (Gemini models)
- **Multimodal Embedding**: Text and image embeddings for search

### State Management

- **Session State**: Stored in database via DatabaseSessionService
- **Shared State**: All agents access same session state
- **State Keys**:
  - `current_results`: Product search results
  - `cart`: Current cart items
  - `order_summary`: Prepared order summary
  - `payment_processed`: Payment completion flag
  - `current_image_bytes`: Uploaded image data

### Artifact Streaming

- **Real-time Updates**: State changes trigger artifact streaming
- **Artifact Types**: Products, Cart, Orders, Payment Methods
- **Incremental Updates**: Only changed artifacts are sent
- **Format**: Structured JSON via A2A protocol

