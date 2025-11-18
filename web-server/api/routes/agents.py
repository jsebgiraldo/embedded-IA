"""Agent management endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from database.db import get_db, Agent as DBAgent
from models.agent import AgentResponse, AgentCreate, AgentStatus

router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.get("", response_model=List[AgentResponse])
async def list_agents(db: Session = Depends(get_db)):
    """List all agents."""
    agents = db.query(DBAgent).all()
    return agents


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str, db: Session = Depends(get_db)):
    """Get agent by ID."""
    agent = db.query(DBAgent).filter(DBAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.post("", response_model=AgentResponse)
async def create_agent(agent: AgentCreate, db: Session = Depends(get_db)):
    """Create a new agent."""
    # Check if agent already exists
    existing = db.query(DBAgent).filter(DBAgent.id == agent.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Agent already exists")
    
    db_agent = DBAgent(
        id=agent.id,
        name=agent.name,
        type=agent.type,
        status=agent.status.value
    )
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    return db_agent


@router.put("/{agent_id}/status")
async def update_agent_status(
    agent_id: str, 
    status_update: dict,
    db: Session = Depends(get_db)
):
    """Update agent status."""
    agent = db.query(DBAgent).filter(DBAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    new_status = status_update.get("status")
    if not new_status:
        raise HTTPException(status_code=400, detail="Status is required")
    
    agent.status = new_status
    agent.updated_at = datetime.utcnow()
    if new_status in ["active", "running"]:
        agent.last_active = datetime.utcnow()
    
    db.commit()
    db.refresh(agent)
    
    return agent


@router.post("/{agent_id}/start")
async def start_agent(agent_id: str, db: Session = Depends(get_db)):
    """Start an agent."""
    agent = db.query(DBAgent).filter(DBAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent.status = AgentStatus.ACTIVE.value
    agent.last_active = datetime.utcnow()
    agent.updated_at = datetime.utcnow()
    db.commit()
    
    return {"status": "success", "message": f"Agent {agent_id} started"}


@router.post("/{agent_id}/stop")
async def stop_agent(agent_id: str, db: Session = Depends(get_db)):
    """Stop an agent."""
    agent = db.query(DBAgent).filter(DBAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent.status = AgentStatus.IDLE.value
    agent.updated_at = datetime.utcnow()
    db.commit()
    
    return {"status": "success", "message": f"Agent {agent_id} stopped"}


@router.delete("/{agent_id}")
async def delete_agent(agent_id: str, db: Session = Depends(get_db)):
    """Delete an agent."""
    agent = db.query(DBAgent).filter(DBAgent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    db.delete(agent)
    db.commit()
    
    return {"status": "success", "message": f"Agent {agent_id} deleted"}
