# Build Orchestration Integration

## Overview

The Build Orchestration system integrates GitHub project management with the AgentOrchestrator multi-agent workflow system. This enables complete automated build/test/QA cycles for ESP32 projects.

## Architecture

```
┌──────────────────┐
│  GitHub Webhook  │
│   or Manual UI   │
└────────┬─────────┘
         │
         v
┌──────────────────────────┐
│  trigger_build Endpoint  │
│  /api/projects/{id}/build│
└────────┬─────────────────┘
         │
         v
┌────────────────────────────┐
│ BuildOrchestrationService  │
│  - Validates project       │
│  - Creates build record    │
│  - Executes in background  │
└────────┬───────────────────┘
         │
         v
┌──────────────────────────┐
│   AgentOrchestrator      │
│  - PROJECT_MANAGER       │
│  - DEVELOPER             │
│  - BUILDER               │
│  - TESTER (parallel)     │
│  - DOCTOR (parallel)     │
│  - QA                    │
└────────┬─────────────────┘
         │
         v
┌────────────────────────┐
│  Database + WebSocket  │
│  - Update build status │
│  - Emit events to UI   │
└────────────────────────┘
```

## Workflow Execution

### Phase 1: Project Setup
- **Agent**: PROJECT_MANAGER
- **Tasks**:
  - Validate project structure
  - Check for CMakeLists.txt
  - Set target chip (esp32, esp32s3, etc.)

### Phase 2: Build
- **Agent**: BUILDER
- **Tasks**:
  - Compile firmware
  - Generate artifacts
  - Cache build output

### Phase 3: Testing (Parallel)
- **Agents**: TESTER (2 parallel executions)
- **Tasks**:
  - Flash to hardware (if enabled)
  - Run QEMU simulation (if enabled)

### Phase 4: Validation (Parallel)
- **Agents**: DOCTOR + QA
- **Tasks**:
  - Hardware diagnostics
  - QA analysis and validation

### Phase 5: Feedback Loop (if issues found)
- **Agent**: DEVELOPER
- **Tasks**:
  - Fix code issues
  - Recompile
  - Retest

## API Endpoints

### Trigger Build

```http
POST /api/projects/{project_id}/build
Content-Type: application/json

{
  "commit_sha": "abc123",  // Optional, defaults to latest
  "trigger": "manual"       // "manual", "push", or "webhook"
}
```

**Response:**
```json
{
  "build_id": 42,
  "status": "pending",
  "project_id": "uuid-here",
  "commit_sha": "abc123"
}
```

### Get Build Status

```http
GET /api/builds/{build_id}
```

**Response:**
```json
{
  "id": 42,
  "project_id": "uuid-here",
  "commit_sha": "abc123",
  "status": "running",  // pending, running, success, failed
  "started_at": "2024-01-15T10:30:00Z",
  "completed_at": null,
  "duration": null,
  "build_output": "...",
  "test_results": "...",
  "artifacts_path": "/app/projects/..."
}
```

## BuildOrchestrationService

### Methods

#### `execute_build(db, build_id, project, flash_device, run_qemu)`

Executes a complete build workflow synchronously.

**Parameters:**
- `db`: SQLAlchemy session
- `build_id`: Build record ID
- `project`: Project instance
- `flash_device`: Enable hardware flashing
- `run_qemu`: Enable QEMU simulation

**Returns:**
```python
{
    "build_id": 42,
    "status": "success",
    "duration": 125.3,
    "result": {...}  # Full orchestrator results
}
```

#### `execute_build_background(db, build_id, project_id, flash_device, run_qemu)`

Wrapper for background execution via FastAPI BackgroundTasks.

#### `validate_project_for_build(project)`

Validates that a project is ready to be built.

**Returns:** `(is_valid: bool, error_message: Optional[str])`

**Checks:**
- Project status is "active"
- Clone path exists
- CMakeLists.txt present (ESP-IDF requirement)

#### `retry_failed_build(db, build_id, flash_device, run_qemu)`

Retries a previously failed build.

#### `get_build_stats(db, project_id)`

Returns build statistics for a project.

**Returns:**
```python
{
    "project_id": "uuid",
    "total_builds": 15,
    "successful": 12,
    "failed": 2,
    "pending": 0,
    "running": 1,
    "success_rate": 80.0,
    "average_duration": 98.5
}
```

## Build Status Flow

```
pending → running → success
                 ↘ failed
```

### Status Definitions

- **pending**: Build created, waiting to start
- **running**: Orchestrator executing workflow
- **success**: All phases completed successfully
- **failed**: One or more phases failed

## Database Schema

### builds table

```sql
CREATE TABLE builds (
    id INTEGER PRIMARY KEY,
    project_id TEXT NOT NULL,
    commit_sha TEXT NOT NULL,
    commit_message TEXT,
    commit_author TEXT,
    branch TEXT,
    triggered_by TEXT,  -- 'manual', 'push', 'webhook'
    status TEXT NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration REAL,
    build_output TEXT,
    test_results TEXT,
    artifacts_path TEXT,
    created_at TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);
```

## WebSocket Events

The orchestrator emits real-time events to the dashboard via WebSocket:

### Event Types

#### `workflow.started`
```json
{
  "type": "workflow.started",
  "job_id": 42,
  "project_path": "/app/projects/...",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### `workflow.progress`
```json
{
  "type": "workflow.progress",
  "job_id": 42,
  "phase": "build",
  "progress": 50,
  "message": "Compiling main.c..."
}
```

#### `workflow.completed`
```json
{
  "type": "workflow.completed",
  "job_id": 42,
  "success": true,
  "duration": 125.3,
  "result": {...}
}
```

#### `agent.status`
```json
{
  "type": "agent.status",
  "job_id": 42,
  "agent": "BUILDER",
  "status": "working",  // idle, working, completed, error
  "task": "Compiling firmware"
}
```

## Testing

### Manual Build Trigger

```bash
# Trigger build for project
curl -X POST http://localhost:8000/api/projects/{project_id}/build \
  -H "Content-Type: application/json" \
  -d '{
    "trigger": "manual"
  }'

# Check build status
curl http://localhost:8000/api/builds/{build_id}
```

### Background Execution

Builds execute in the background using FastAPI's `BackgroundTasks`. This ensures:
- API responds immediately
- Long-running workflows don't block
- Multiple builds can run concurrently
- Status updates happen in real-time

## Error Handling

### Project Validation Errors

```json
{
  "detail": "Project status is 'pending', must be 'active'"
}
```

### Build Execution Errors

When a build fails, the error is stored in the database:

```python
build.status = "failed"
build.build_output = f"Error: {str(exception)}"
```

### Orchestrator Errors

The orchestrator handles errors gracefully:
- Phase failures are tracked
- QA can trigger code fixes
- Failed builds can be retried

## Configuration

### Environment Variables

- `OLLAMA_HOST`: LLM provider for code fixing (default: http://ollama:11434)
- `ESP_IDF_VERSION`: Target IDF version (default: v5.1)

### Project Settings

Each project has a `target` field:
- `esp32`
- `esp32s2`
- `esp32s3`
- `esp32c3`
- `esp32c6`

## Integration Points

### With Projects API

- Projects must be "active" to build
- Builds track commit SHA, author, message
- Sync operations can trigger auto-builds

### With Dependency Resolver

- Dependencies are scanned before build
- Missing deps can cause build failures
- QA validates dependency versions

### With LLM Chat

- Code Fixer agent uses Ollama LLM
- Errors are analyzed automatically
- Fixes are suggested and applied

## Monitoring

### Build Metrics

Track these metrics per project:
- Total builds
- Success rate
- Average duration
- Failure patterns

### Real-Time Dashboard

The Projects tab shows:
- Active builds with progress
- Recent build history
- Success/failure badges
- Build logs

## Future Enhancements

### Auto-Build on Push

```python
# In webhook handler
if event_type == "push":
    await trigger_build(
        project_id=project.id,
        trigger="push"
    )
```

### Build Queuing

For high-volume scenarios:
- Implement build queue
- Limit concurrent builds
- Priority scheduling

### Artifact Storage

- Store build artifacts in S3/MinIO
- Track binary sizes
- Compare artifacts across builds

### Notifications

- Slack/Discord webhooks
- Email on build failure
- GitHub status checks

## Troubleshooting

### Build Stuck in "pending"

Check that:
1. Container has access to orchestrator
2. MCP client initializes correctly
3. BackgroundTasks are running

### Build Fails Immediately

Validate:
1. Project has CMakeLists.txt
2. Clone path exists
3. Git repository is valid

### Orchestrator Errors

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Example: Complete Build Flow

```python
# 1. User triggers build from UI
# POST /api/projects/abc-123/build

# 2. Endpoint validates and creates build record
build = Build(
    project_id="abc-123",
    status="pending",
    commit_sha="def456"
)

# 3. Background task starts
background_tasks.add_task(
    build_service.execute_build_background,
    build_id=build.id,
    ...
)

# 4. Orchestrator executes workflow
result = await orchestrator.execute_workflow(
    project_path="/app/projects/my-project",
    target="esp32",
    job_id=build.id
)

# 5. Build record updated
build.status = "success"
build.completed_at = datetime.utcnow()
build.duration = 125.3

# 6. WebSocket event sent to dashboard
emit_event({
    "type": "workflow.completed",
    "job_id": build.id,
    "success": True
})
```

## Summary

The Build Orchestration system provides:

✅ **Automated Workflows** - Complete build/test/QA cycles  
✅ **Background Execution** - Non-blocking API responses  
✅ **Real-Time Updates** - WebSocket events to dashboard  
✅ **Error Handling** - Graceful failures and retries  
✅ **Parallel Testing** - QEMU + hardware simultaneously  
✅ **QA Feedback Loop** - Automatic code fixing  
✅ **Build Tracking** - Full history and metrics  
✅ **Multi-Project Support** - Concurrent builds  

This integration completes the end-to-end flow from GitHub import to validated firmware artifacts.
