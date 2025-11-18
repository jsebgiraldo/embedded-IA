"""FastAPI main application for ESP32 Developer Agent Dashboard."""
import sys
import os
from contextlib import asynccontextmanager

# Add parent and agent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
agent_dir = os.path.join(parent_dir, 'agent')
sys.path.insert(0, current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, agent_dir)

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from database.db import init_db, SessionLocal, Agent as DBAgent
from api.routes import agents_router, jobs_router, logs_router, metrics_router
from api.routes.llm import router as llm_router
from api.routes.projects import router as projects_router
from api.routes.github import router as github_router
from api.websocket import router as websocket_router, manager

# Import event_emitter directly to avoid loading all agent dependencies
from event_emitter import event_emitter, Event, EventType


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print("🚀 Starting ESP32 Developer Agent Dashboard...")
    
    # Initialize database
    init_db()
    
    # Create default agents if they don't exist
    db = SessionLocal()
    try:
        agents_data = [
            {"id": "developer", "name": "Developer Agent", "type": "developer", "status": "idle"},
            {"id": "test", "name": "Test Agent", "type": "test", "status": "idle"},
            {"id": "build", "name": "Build Agent", "type": "build", "status": "idle"}
        ]
        
        for agent_data in agents_data:
            existing = db.query(DBAgent).filter(DBAgent.id == agent_data["id"]).first()
            if not existing:
                agent = DBAgent(**agent_data)
                db.add(agent)
        
        db.commit()
        print("✅ Default agents initialized")
    finally:
        db.close()
    
    # Start event emitter
    await event_emitter.start()
    print("✅ Event emitter started")
    
    # Register event listener to broadcast events via WebSocket
    async def broadcast_event_to_clients(event: Event):
        """Broadcast events to all connected WebSocket clients."""
        await manager.broadcast_json(event.to_dict())
    
    # Register listeners for all event types
    for event_type in EventType:
        event_emitter.on(event_type, broadcast_event_to_clients)
    
    print("✅ WebSocket event broadcasting configured")
    print("=" * 80)
    print("🌐 Dashboard ready at: http://localhost:8000")
    print("📡 WebSocket endpoint: ws://localhost:8000/ws")
    print("📚 API docs: http://localhost:8000/docs")
    print("=" * 80)
    
    yield
    
    # Shutdown
    print("🛑 Shutting down...")
    await event_emitter.stop()


# Create FastAPI app
app = FastAPI(
    title="ESP32 Developer Agent Dashboard",
    description="Real-time monitoring and management for ESP32 development agents",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(agents_router)
app.include_router(jobs_router)
app.include_router(logs_router)
app.include_router(metrics_router)
app.include_router(llm_router)
app.include_router(projects_router)
app.include_router(github_router)
app.include_router(websocket_router)

# Serve static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def read_index():
    """Serve the main dashboard."""
    return FileResponse(os.path.join(static_dir, "index.html"))


@app.get("/api/status")
async def get_status():
    """Get system status."""
    return {
        "status": "ok",
        "service": "ESP32 Developer Agent Dashboard",
        "version": "1.0.0",
        "websocket_connections": len(manager.active_connections)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
