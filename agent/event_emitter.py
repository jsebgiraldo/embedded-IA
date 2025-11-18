"""Event emitter system for real-time updates.

This module provides a centralized event system that allows different
components (orchestrator, agents, etc.) to emit events that are captured
by the web server and broadcast to connected clients.
"""
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Callable, Optional
from enum import Enum
import json


class EventType(str, Enum):
    """Event types for the system."""
    # Agent events
    AGENT_STATUS_CHANGED = "agent_status_changed"
    AGENT_STARTED = "agent_started"
    AGENT_STOPPED = "agent_stopped"
    
    # Job events
    JOB_CREATED = "job_created"
    JOB_STARTED = "job_started"
    JOB_PROGRESS = "job_progress"
    JOB_COMPLETED = "job_completed"
    JOB_FAILED = "job_failed"
    JOB_CANCELLED = "job_cancelled"
    
    # Workflow events
    WORKFLOW_PHASE_STARTED = "workflow_phase_started"
    WORKFLOW_PHASE_COMPLETED = "workflow_phase_completed"
    
    # Log events
    LOG_ENTRY = "log_entry"
    
    # Metric events
    METRIC_UPDATE = "metric_update"
    
    # System events
    SYSTEM_STATUS = "system_status"


class Event:
    """Event data structure."""
    
    def __init__(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        agent_id: Optional[str] = None,
        job_id: Optional[int] = None
    ):
        self.event_type = event_type
        self.data = data
        self.agent_id = agent_id
        self.job_id = job_id
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "event_type": self.event_type.value,
            "data": self.data,
            "agent_id": self.agent_id,
            "job_id": self.job_id,
            "timestamp": self.timestamp.isoformat()
        }
    
    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.to_dict())


class EventEmitter:
    """Centralized event emitter for the system."""
    
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        """Singleton pattern to ensure only one event emitter exists."""
        if cls._instance is None:
            cls._instance = super(EventEmitter, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize event emitter."""
        if self._initialized:
            return
        
        self._listeners: Dict[EventType, List[Callable]] = {}
        self._event_queue = asyncio.Queue()
        self._running = False
        self._initialized = True
    
    def on(self, event_type: EventType, callback: Callable):
        """Register an event listener."""
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(callback)
    
    def off(self, event_type: EventType, callback: Callable):
        """Unregister an event listener."""
        if event_type in self._listeners:
            self._listeners[event_type].remove(callback)
    
    async def emit(self, event: Event):
        """Emit an event to all registered listeners."""
        await self._event_queue.put(event)
    
    async def emit_sync(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        agent_id: Optional[str] = None,
        job_id: Optional[int] = None
    ):
        """Emit an event synchronously (helper method)."""
        event = Event(event_type, data, agent_id, job_id)
        await self.emit(event)
    
    def emit_blocking(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        agent_id: Optional[str] = None,
        job_id: Optional[int] = None
    ):
        """Emit an event from synchronous code."""
        event = Event(event_type, data, agent_id, job_id)
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.emit(event))
            else:
                loop.run_until_complete(self.emit(event))
        except RuntimeError:
            # No event loop, create a new one
            asyncio.run(self.emit(event))
    
    async def _process_events(self):
        """Process events from the queue."""
        while self._running:
            try:
                event = await asyncio.wait_for(
                    self._event_queue.get(),
                    timeout=1.0
                )
                
                # Call all registered listeners for this event type
                if event.event_type in self._listeners:
                    for callback in self._listeners[event.event_type]:
                        try:
                            if asyncio.iscoroutinefunction(callback):
                                await callback(event)
                            else:
                                callback(event)
                        except Exception as e:
                            print(f"Error in event listener: {e}")
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Error processing event: {e}")
    
    async def start(self):
        """Start the event processing loop."""
        self._running = True
        asyncio.create_task(self._process_events())
    
    async def stop(self):
        """Stop the event processing loop."""
        self._running = False


# Global event emitter instance
event_emitter = EventEmitter()


# Helper functions for common events
async def emit_log(
    level: str,
    message: str,
    agent_id: Optional[str] = None,
    job_id: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """Emit a log event."""
    await event_emitter.emit_sync(
        EventType.LOG_ENTRY,
        {
            "level": level,
            "message": message,
            "metadata": metadata
        },
        agent_id=agent_id,
        job_id=job_id
    )


async def emit_job_progress(
    job_id: int,
    phase: str,
    progress: float,
    message: str,
    agent_id: Optional[str] = None
):
    """Emit a job progress event."""
    await event_emitter.emit_sync(
        EventType.JOB_PROGRESS,
        {
            "phase": phase,
            "progress": progress,
            "message": message
        },
        agent_id=agent_id,
        job_id=job_id
    )


async def emit_agent_status(agent_id: str, status: str, metadata: Optional[Dict[str, Any]] = None):
    """Emit an agent status change event."""
    await event_emitter.emit_sync(
        EventType.AGENT_STATUS_CHANGED,
        {
            "status": status,
            "metadata": metadata
        },
        agent_id=agent_id
    )
