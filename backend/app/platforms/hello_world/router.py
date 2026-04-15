"""
Hello World Platform API routes.

These routes are registered under /api/v1/platforms/hello-world/
"""
from fastapi import APIRouter, Depends, HTTPException

from app.core.security import get_current_user, require_platform
from app.platforms.hello_world.schemas import (
    GreetRequest,
    GreetResponse,
    PlatformStatusResponse,
)
from app.platforms.hello_world.services import HelloWorldService
from app.platforms.hello_world.agents.greeter.llm import get_greeter_config

router = APIRouter()


@router.get("/status", response_model=PlatformStatusResponse)
async def get_platform_status():
    """Get the status of the Hello World platform."""
    llm_config = get_greeter_config()
    return PlatformStatusResponse(
        platform_id="hello-world",
        name="Hello World",
        status="active",
        agents=["greeter"],
        version="1.0.0",
    )


@router.get("/config")
async def get_platform_config():
    """Get the current LLM configuration for the platform."""
    llm_config = get_greeter_config()
    return {
        "platform_id": "hello-world",
        "llm": llm_config,
    }


@router.get("/health")
async def check_health():
    """
    Check platform and LLM health.

    Returns the health status of the platform and its LLM provider.
    """
    service = HelloWorldService()
    llm_config = get_greeter_config()

    # Check LLM health
    llm_healthy = await service.check_llm_health()

    return {
        "platform": "healthy",
        "llm": {
            "status": "healthy" if llm_healthy else "unavailable",
            "provider": llm_config.get("provider"),
            "model": llm_config.get("model"),
        },
    }


@router.get("/agents")
async def list_agents():
    """List all agents in the Hello World platform."""
    llm_config = get_greeter_config()
    return [
        {
            "id": "greeter",
            "name": "Greeter Agent",
            "description": "Generates personalized greetings",
            "status": "active",
            "llm": {
                "provider": llm_config.get("provider"),
                "model": llm_config.get("model"),
            },
        }
    ]


@router.post("/execute", response_model=GreetResponse,
              dependencies=[Depends(require_platform("hello_world"))])
async def execute_platform(
    request: GreetRequest,
    current_user: dict = Depends(get_current_user),
):
    """Execute the Hello World platform workflow."""
    service = HelloWorldService()
    result = await service.generate_greeting(request.name, request.style)
    return GreetResponse(
        greeting=result["greeting"],
        agent="greeter",
        metadata=result.get("metadata", {}),
    )


@router.post("/agents/greeter/run",
              dependencies=[Depends(require_platform("hello_world"))])
async def run_greeter_agent(
    request: GreetRequest,
    current_user: dict = Depends(get_current_user),
):
    """Run the greeter agent directly."""
    service = HelloWorldService()
    result = await service.generate_greeting(request.name, request.style)
    return result
