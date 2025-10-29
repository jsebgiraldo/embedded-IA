"""
ESP32 Multi-Agent Development System
Specialized agents with parallel execution and QA feedback loops
"""

from .orchestrator import (
    AgentOrchestrator,
    AgentRole,
    Task,
    TaskStatus,
    WorkflowState
)

__version__ = "1.0.0"
__author__ = "Sebastian Giraldo"

__all__ = [
    "AgentOrchestrator",
    "AgentRole",
    "Task", 
    "TaskStatus",
    "WorkflowState"
]
