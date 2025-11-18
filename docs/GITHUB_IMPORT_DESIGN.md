# 🔄 GitHub Import Service - Design Document

## 📋 Overview

Sistema de importación automática que detecta cambios en repositorios GitHub y dispara workflows de desarrollo automáticamente.

## 🎯 Objetivos

1. **Webhook Integration**: Recibir eventos de GitHub (push, PR)
2. **Repository Management**: Clonar y actualizar repositorios automáticamente
3. **Dependency Resolution**: Parsear y resolver dependencias ESP-IDF
4. **Workflow Trigger**: Disparar builds/tests automáticos
5. **Project Dashboard**: Gestionar múltiples proyectos desde la UI

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                         GitHub                                   │
│  ┌──────────────┐                                               │
│  │ Repository   │ ──push/PR──> Webhook                          │
│  └──────────────┘                                               │
└─────────────────────────────────────────────────────────────────┘
                        │
                        │ POST /api/github/webhook
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Webhook Receiver Service                        │
│  ┌──────────────────────────────────────────────────────┐       │
│  │ 1. Validate HMAC signature                           │       │
│  │ 2. Parse event payload                               │       │
│  │ 3. Queue event for processing                        │       │
│  └──────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
                        │
                        │ event_queue
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Event Processor                                │
│  ┌──────────────────────────────────────────────────────┐       │
│  │ Process events async (background task)               │       │
│  └──────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Repository   │ │ Dependency   │ │ Workflow     │
│ Manager      │ │ Resolver     │ │ Dispatcher   │
│              │ │              │ │              │
│ - Clone      │ │ - Parse yml  │ │ - Trigger    │
│ - Update     │ │ - Install    │ │   builds     │
│ - Checkout   │ │   deps       │ │ - Monitor    │
└──────────────┘ └──────────────┘ └──────────────┘
        │               │               │
        └───────────────┼───────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Agent Orchestrator                              │
│  ┌──────────────────────────────────────────────────────┐       │
│  │ Run workflow: validate → build → test → QA          │       │
│  └──────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Dashboard UI                                │
│  ┌──────────────────────────────────────────────────────┐       │
│  │ Display: projects, builds, logs, metrics             │       │
│  └──────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

## 💾 Data Models

### Project
Representa un proyecto ESP32 importado desde GitHub.

```python
class Project(Base):
    """Project imported from GitHub"""
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True)  # UUID
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    
    # GitHub info
    repo_url = Column(String, nullable=False)
    repo_full_name = Column(String, nullable=False)  # owner/repo
    branch = Column(String, default="main")
    
    # Local info
    clone_path = Column(String, nullable=False)
    last_commit_sha = Column(String, nullable=True)
    last_synced_at = Column(DateTime, nullable=True)
    
    # ESP32 config
    target = Column(String, default="esp32")  # esp32, esp32s2, esp32s3, esp32c3
    build_system = Column(String, default="cmake")  # cmake, make
    
    # Status
    status = Column(String, default="pending")  # pending, active, error, archived
    webhook_secret = Column(String, nullable=True)  # For validating webhooks
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String, nullable=True)  # User ID (future auth)
```

### Dependency
Dependencias ESP-IDF del proyecto.

```python
class Dependency(Base):
    """ESP-IDF component dependency"""
    __tablename__ = "dependencies"
    
    id = Column(Integer, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    
    # Component info
    component_name = Column(String, nullable=False)
    version = Column(String, nullable=False)
    source = Column(String, nullable=False)  # registry, git, local
    
    # Git source (if applicable)
    git_url = Column(String, nullable=True)
    git_ref = Column(String, nullable=True)  # commit, tag, branch
    
    # Installation
    installed = Column(Boolean, default=False)
    installed_at = Column(DateTime, nullable=True)
    install_error = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
```

### Build
Historial de builds de cada proyecto.

```python
class Build(Base):
    """Build history for projects"""
    __tablename__ = "builds"
    
    id = Column(Integer, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    
    # Build info
    commit_sha = Column(String, nullable=False)
    commit_message = Column(Text, nullable=True)
    commit_author = Column(String, nullable=True)
    branch = Column(String, nullable=False)
    
    # Execution
    status = Column(String, default="pending")  # pending, running, success, failed
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration = Column(Float, nullable=True)
    
    # Results
    build_output = Column(Text, nullable=True)
    test_results = Column(Text, nullable=True)  # JSON
    artifacts_path = Column(String, nullable=True)
    
    # Trigger
    triggered_by = Column(String, nullable=False)  # webhook, manual, scheduled
    github_event_type = Column(String, nullable=True)  # push, pull_request
    
    created_at = Column(DateTime, default=datetime.utcnow)
```

### WebhookEvent
Log de todos los webhooks recibidos.

```python
class WebhookEvent(Base):
    """GitHub webhook event log"""
    __tablename__ = "webhook_events"
    
    id = Column(Integer, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=True)
    
    # Event info
    event_type = Column(String, nullable=False)  # push, pull_request, ping
    event_id = Column(String, unique=True, nullable=False)  # GitHub delivery ID
    payload = Column(Text, nullable=False)  # Full JSON payload
    
    # Processing
    status = Column(String, default="pending")  # pending, processing, success, failed
    processed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Validation
    signature_valid = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
```

## 🔌 API Endpoints

### Webhook Receiver

**POST** `/api/github/webhook`
Recibe webhooks de GitHub.

```python
Headers:
  X-GitHub-Event: push | pull_request | ping
  X-GitHub-Delivery: <UUID>
  X-Hub-Signature-256: sha256=<HMAC>

Body: GitHub webhook payload (JSON)

Response 200:
{
  "status": "received",
  "event_id": "abc123",
  "event_type": "push",
  "queued": true
}

Response 401:
{
  "error": "Invalid signature"
}
```

### Project Management

**POST** `/api/projects`
Crear nuevo proyecto desde GitHub.

```python
Request:
{
  "name": "my-esp32-project",
  "repo_url": "https://github.com/user/repo",
  "branch": "main",
  "target": "esp32s3",
  "webhook_secret": "optional-secret"
}

Response 201:
{
  "id": "uuid",
  "name": "my-esp32-project",
  "repo_url": "...",
  "status": "pending",
  "clone_path": "/app/projects/my-esp32-project",
  "webhook_url": "http://your-domain/api/github/webhook?project=uuid",
  "created_at": "2025-11-17T..."
}
```

**GET** `/api/projects`
Listar todos los proyectos.

```python
Response 200:
{
  "projects": [
    {
      "id": "uuid",
      "name": "project1",
      "repo_url": "...",
      "branch": "main",
      "status": "active",
      "last_synced_at": "2025-11-17T...",
      "last_commit_sha": "abc123",
      "builds_count": 42,
      "last_build_status": "success"
    }
  ]
}
```

**GET** `/api/projects/{project_id}`
Obtener detalles de un proyecto.

```python
Response 200:
{
  "id": "uuid",
  "name": "project1",
  "repo_url": "...",
  "branch": "main",
  "target": "esp32s3",
  "clone_path": "/app/projects/project1",
  "status": "active",
  "dependencies": [
    {
      "component_name": "esp_wifi",
      "version": "1.2.3",
      "installed": true
    }
  ],
  "recent_builds": [...],
  "metrics": {
    "total_builds": 42,
    "success_rate": 0.95,
    "avg_build_time": 125.5
  }
}
```

**PUT** `/api/projects/{project_id}/sync`
Sincronizar proyecto (pull latest changes).

```python
Response 200:
{
  "status": "synced",
  "previous_commit": "abc123",
  "current_commit": "def456",
  "changes": {
    "files_changed": 3,
    "insertions": 45,
    "deletions": 12
  }
}
```

**POST** `/api/projects/{project_id}/build`
Disparar build manual.

```python
Request:
{
  "trigger": "manual",
  "commit_sha": "optional-specific-commit"
}

Response 201:
{
  "build_id": 123,
  "status": "pending",
  "project_id": "uuid",
  "commit_sha": "def456"
}
```

**DELETE** `/api/projects/{project_id}`
Eliminar proyecto (solo metadata, no el repo clonado).

```python
Response 200:
{
  "deleted": true,
  "id": "uuid"
}
```

### Build History

**GET** `/api/projects/{project_id}/builds`
Obtener historial de builds.

```python
Query params:
  ?limit=20
  ?status=success|failed
  ?branch=main

Response 200:
{
  "builds": [
    {
      "id": 123,
      "commit_sha": "abc123",
      "commit_message": "Fix GPIO bug",
      "branch": "main",
      "status": "success",
      "duration": 125.5,
      "started_at": "...",
      "completed_at": "..."
    }
  ],
  "total": 156
}
```

**GET** `/api/builds/{build_id}`
Obtener detalles de un build.

```python
Response 200:
{
  "id": 123,
  "project_id": "uuid",
  "commit_sha": "abc123",
  "status": "success",
  "build_output": "...",
  "test_results": {...},
  "artifacts_path": "/app/artifacts/123"
}
```

## 🔧 Services

### 1. WebhookService

```python
class WebhookService:
    """Handle GitHub webhook events"""
    
    async def receive_webhook(
        self,
        event_type: str,
        delivery_id: str,
        signature: str,
        payload: dict
    ) -> WebhookEvent:
        """
        Receive and validate webhook.
        
        1. Validate HMAC signature
        2. Parse payload
        3. Store event in DB
        4. Queue for processing
        """
        
    async def validate_signature(
        self,
        payload: bytes,
        signature: str,
        secret: str
    ) -> bool:
        """Validate HMAC-SHA256 signature"""
        
    async def parse_push_event(self, payload: dict) -> dict:
        """Extract relevant info from push event"""
        
    async def parse_pr_event(self, payload: dict) -> dict:
        """Extract relevant info from PR event"""
```

### 2. RepositoryManager

```python
class RepositoryManager:
    """Manage git repositories"""
    
    async def clone_repository(
        self,
        repo_url: str,
        clone_path: str,
        branch: str = "main"
    ) -> bool:
        """Clone repository from GitHub"""
        
    async def update_repository(
        self,
        clone_path: str,
        branch: str = "main"
    ) -> dict:
        """Pull latest changes"""
        
    async def checkout_commit(
        self,
        clone_path: str,
        commit_sha: str
    ) -> bool:
        """Checkout specific commit"""
        
    async def get_latest_commit(
        self,
        clone_path: str
    ) -> dict:
        """Get latest commit info"""
        
    async def get_diff(
        self,
        clone_path: str,
        from_commit: str,
        to_commit: str
    ) -> dict:
        """Get diff between commits"""
```

### 3. DependencyResolver

```python
class DependencyResolver:
    """Resolve ESP-IDF component dependencies"""
    
    async def parse_idf_component_yml(
        self,
        project_path: str
    ) -> List[Dependency]:
        """Parse idf_component.yml or main/idf_component.yml"""
        
    async def resolve_dependencies(
        self,
        dependencies: List[Dependency]
    ) -> List[Dependency]:
        """Resolve dependency versions"""
        
    async def install_dependencies(
        self,
        project_path: str,
        dependencies: List[Dependency]
    ) -> dict:
        """Install dependencies using idf.py"""
        
    async def validate_dependencies(
        self,
        project_path: str
    ) -> dict:
        """Check if all dependencies are installed"""
```

### 4. WorkflowDispatcher

```python
class WorkflowDispatcher:
    """Dispatch workflows to orchestrator"""
    
    async def trigger_build(
        self,
        project: Project,
        commit_sha: str,
        trigger: str = "webhook"
    ) -> Build:
        """
        Trigger build workflow:
        1. Create Build record
        2. Prepare workspace
        3. Call AgentOrchestrator
        4. Update Build with results
        """
        
    async def monitor_workflow(
        self,
        build_id: int
    ) -> dict:
        """Monitor workflow progress"""
```

## 🔐 Security

### Webhook Validation

```python
import hmac
import hashlib

def validate_github_signature(payload: bytes, signature: str, secret: str) -> bool:
    """
    Validate GitHub webhook signature.
    
    GitHub sends: X-Hub-Signature-256: sha256=<hash>
    We compute: HMAC-SHA256(secret, payload)
    """
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    # Remove 'sha256=' prefix if present
    if signature.startswith('sha256='):
        signature = signature[7:]
    
    return hmac.compare_digest(expected, signature)
```

### Environment Variables

```bash
# .env
GITHUB_WEBHOOK_SECRET=your-secret-here
PROJECTS_BASE_DIR=/app/projects
MAX_REPO_SIZE_MB=500
CLONE_TIMEOUT_SECONDS=300
```

## 📊 Workflow Integration

### Event Processing Flow

```
1. Webhook arrives
   ↓
2. Validate signature
   ↓
3. Parse event (push/PR)
   ↓
4. Find/create Project
   ↓
5. Clone/update repository
   ↓
6. Resolve dependencies
   ↓
7. Create Build record
   ↓
8. Dispatch to AgentOrchestrator
   ├─ Project Manager: validate
   ├─ Developer: check code (if needed)
   ├─ Builder: compile firmware
   ├─ Tester: flash + QEMU
   ├─ Doctor: diagnostics
   └─ QA: validate results
   ↓
9. Update Build with results
   ↓
10. Send notifications (future)
```

## 🎨 UI Components

### Projects Tab

```
┌──────────────────────────────────────────────────────────────┐
│ 📦 Projects                                        [+ New]    │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  🟢 my-esp32-wifi                                            │
│     github.com/user/repo • main                              │
│     Last build: ✅ success (2m ago)                          │
│     [Sync] [Build] [Settings]                                │
│                                                               │
│  🟢 sensor-gateway                                           │
│     github.com/user/sensor • develop                         │
│     Last build: ❌ failed (1h ago)                           │
│     [Sync] [Build] [Settings]                                │
│                                                               │
│  🔴 legacy-project                                           │
│     github.com/old/legacy • master                           │
│     Status: error - clone failed                             │
│     [Retry] [Remove]                                         │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### Project Detail View

```
┌──────────────────────────────────────────────────────────────┐
│ 📦 my-esp32-wifi                                             │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ℹ️ Info                                                      │
│     Repository: github.com/user/repo                         │
│     Branch: main                                             │
│     Target: esp32s3                                          │
│     Last sync: 5 minutes ago                                 │
│     Commit: abc1234 - "Fix WiFi bug"                         │
│                                                               │
│  📦 Dependencies                                              │
│     ✅ esp_wifi (1.2.3)                                       │
│     ✅ esp_http_server (2.0.1)                                │
│     ⏳ custom_sensor (0.5.0) - installing...                  │
│                                                               │
│  🔨 Recent Builds                                             │
│     #123 ✅ success (2m ago) - "Fix WiFi bug"                 │
│     #122 ✅ success (1h ago) - "Add LED control"              │
│     #121 ❌ failed (2h ago) - "Refactor code"                 │
│                                                               │
│  📊 Metrics                                                   │
│     Total builds: 156                                        │
│     Success rate: 92%                                        │
│     Avg build time: 2m 15s                                   │
│                                                               │
│  ⚙️ Webhook                                                   │
│     URL: https://your-domain/api/github/webhook?project=uuid │
│     Events: push, pull_request                               │
│     [Copy URL] [Test]                                        │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

## 🧪 Testing

### Manual Testing

```bash
# Test webhook endpoint
curl -X POST http://localhost:8000/api/github/webhook \
  -H "X-GitHub-Event: push" \
  -H "X-GitHub-Delivery: test-123" \
  -H "X-Hub-Signature-256: sha256=$(echo -n 'test' | openssl dgst -sha256 -hmac 'secret')" \
  -d @test_payload.json

# Create project
curl -X POST http://localhost:8000/api/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test-project",
    "repo_url": "https://github.com/espressif/esp-idf-template",
    "branch": "main",
    "target": "esp32"
  }'

# List projects
curl http://localhost:8000/api/projects

# Trigger build
curl -X POST http://localhost:8000/api/projects/{id}/build
```

## 🚀 Implementation Plan

### Phase 1: Foundation (Week 1)
- [x] Design document
- [ ] Database models (Project, Build, Dependency, WebhookEvent)
- [ ] Basic API endpoints (CRUD projects)
- [ ] RepositoryManager (clone, update)

### Phase 2: Webhook Integration (Week 2)
- [ ] WebhookService (receive, validate, parse)
- [ ] Event queue system
- [ ] Background task processor
- [ ] Webhook endpoint + validation

### Phase 3: Dependencies & Workflow (Week 3)
- [ ] DependencyResolver (parse, install)
- [ ] WorkflowDispatcher (trigger builds)
- [ ] Integration with AgentOrchestrator
- [ ] Build monitoring

### Phase 4: UI & Polish (Week 4)
- [ ] Projects tab in dashboard
- [ ] Project detail view
- [ ] Build history UI
- [ ] Real-time updates (WebSocket)
- [ ] Documentation

## 📚 Resources

- [GitHub Webhooks Documentation](https://docs.github.com/en/webhooks)
- [ESP-IDF Component Manager](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/tools/idf-component-manager.html)
- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- [GitPython Library](https://gitpython.readthedocs.io/)

## 🔮 Future Enhancements

- [ ] Support for GitLab webhooks
- [ ] PR previews (build on PR branches)
- [ ] Automatic rollback on failed builds
- [ ] Scheduled builds (cron)
- [ ] Build notifications (Slack, email, Discord)
- [ ] Multi-repo projects (monorepo support)
- [ ] Branch protection (require successful build)
- [ ] Build badges for README
- [ ] Docker image generation for projects
- [ ] OTA update generation
