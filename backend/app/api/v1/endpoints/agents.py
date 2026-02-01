"""
Agent management endpoints.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException

from app.schemas.agent import AgentCreate, AgentUpdate, AgentResponse
from app.core.security import get_current_user

router = APIRouter()


@router.get("", response_model=List[AgentResponse])
async def list_agents():
    """List all agents."""
    # TODO: Implement agent listing
    return []


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str):
    """Get agent by ID."""
    # TODO: Implement agent retrieval
    pass


@router.post("", response_model=AgentResponse)
async def create_agent(agent: AgentCreate):
    """Create a new agent."""
    # TODO: Implement agent creation
    pass


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(agent_id: str, agent: AgentUpdate):
    """Update an agent."""
    # TODO: Implement agent update
    pass


@router.delete("/{agent_id}")
async def delete_agent(agent_id: str):
    """Delete an agent."""
    # TODO: Implement agent deletion
    return {"message": "Agent deleted"}


@router.post("/{agent_id}/execute")
async def execute_agent(agent_id: str, request: dict):
    """Execute an agent."""
    # TODO: Implement agent execution
    pass
