"""
Agent Studio endpoints — Discover agents across all platforms.

These endpoints introspect the PlatformRegistry and BaseAgent instances
to provide rich metadata for the Agent Studio UI.

Phase 2 adds live configuration (session-only), prompt editing, agent
execution ("Try It"), and LLM provider discovery.
"""
import asyncio
import importlib
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException, status

from app.common.base.agent import BaseAgent
from app.common.providers.llm import LLMProviderType, get_llm_provider
from app.platforms.registry import PlatformInfo, get_platform_registry
from app.schemas.studio import (
    StudioAgentDetail,
    StudioAgentSummary,
    StudioAgentsListResponse,
    StudioConfigUpdateRequest,
    StudioLLMConfig,
    StudioPlatformSummary,
    StudioPlatformsListResponse,
    StudioPromptUpdateRequest,
    StudioProviderInfo,
    StudioProvidersListResponse,
    StudioToolInfo,
    StudioTryRequest,
    StudioTryResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Agent Factory Registry
#
# Maps (platform_id, agent_name) -> import path for agents that are NOT
# registered via orchestrator.register_agent(). The Newsletter orchestrator
# uses LangGraph nodes and never calls register_agent(), so we need this
# fallback to instantiate those agents for introspection.
# ---------------------------------------------------------------------------

_AGENT_FACTORIES: Dict[Tuple[str, str], str] = {
    ("newsletter", "research"): "app.platforms.newsletter.agents:ResearchAgent",
    ("newsletter", "writing"): "app.platforms.newsletter.agents:WritingAgent",
    ("newsletter", "preference"): "app.platforms.newsletter.agents:PreferenceAgent",
    ("newsletter", "custom_prompt"): "app.platforms.newsletter.agents:CustomPromptAgent",
}


# ---------------------------------------------------------------------------
# Session-only override store (resets on server restart)
# ---------------------------------------------------------------------------

_session_overrides: Dict[str, Dict[str, Any]] = {}


def _apply_overrides(agent: BaseAgent, agent_id: str) -> BaseAgent:
    """Apply stored session overrides to an agent instance."""
    overrides = _session_overrides.get(agent_id)
    if not overrides:
        return agent

    if "temperature" in overrides:
        agent.temperature = overrides["temperature"]
    if "max_tokens" in overrides:
        agent.max_tokens = overrides["max_tokens"]
    if "model" in overrides:
        agent.model = overrides["model"]
    if "system_prompt" in overrides:
        agent.system_prompt = overrides["system_prompt"]
    if "provider" in overrides:
        try:
            provider_type = LLMProviderType(overrides["provider"])
            agent._llm = get_llm_provider(provider_type)
        except (ValueError, Exception) as e:
            logger.warning(f"Could not apply provider override '{overrides['provider']}': {e}")

    return agent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _import_agent_class(import_path: str):
    """Dynamically import an agent class from a 'module.path:ClassName' string."""
    module_path, class_name = import_path.rsplit(":", 1)
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


def _get_display_name(agent_name: str) -> str:
    """Convert agent_name to display name: 'custom_prompt' -> 'Custom Prompt Agent'."""
    return agent_name.replace("_", " ").title() + " Agent"


def _extract_llm_config(agent: BaseAgent) -> StudioLLMConfig:
    """
    Extract LLM config from a BaseAgent without triggering lazy LLM init.

    Reads from BaseAgent constructor attributes and the optional _llm_config
    dict that platform agents store (e.g. GreeterAgent, ResearchAgent).
    Does NOT access agent.llm (the property), which would trigger lazy init.
    """
    config = StudioLLMConfig(
        model=agent.model,
        temperature=agent.temperature,
        max_tokens=agent.max_tokens,
    )

    # Try _llm_config dict (pattern used by GreeterAgent, ResearchAgent, WritingAgent)
    if hasattr(agent, "_llm_config") and isinstance(agent._llm_config, dict):
        llm_config = agent._llm_config
        config.provider = llm_config.get("provider")
        if not config.model:
            config.model = llm_config.get("model")

    # Try to read provider from already-initialized _llm (without triggering lazy init)
    elif agent._llm is not None:
        config.provider = getattr(agent._llm, "provider_name", None) or type(agent._llm).__name__

    return config


def _build_agent_summary(
    agent: BaseAgent,
    platform_info: PlatformInfo,
) -> StudioAgentSummary:
    """Build a lightweight summary DTO from a BaseAgent instance."""
    llm_config = _extract_llm_config(agent)
    return StudioAgentSummary(
        agent_id=f"{platform_info.id}/{agent.name}",
        name=agent.name,
        display_name=_get_display_name(agent.name),
        platform_id=platform_info.id,
        platform_name=platform_info.name,
        description=agent.description or "",
        llm_config=llm_config,
        tool_count=len(agent.tools),
        has_system_prompt=bool(agent.system_prompt),
        agent_class=type(agent).__name__,
        status="discovered",
    )


def _build_agent_detail(
    agent: BaseAgent,
    platform_info: PlatformInfo,
) -> StudioAgentDetail:
    """Build a full detail DTO from a BaseAgent instance."""
    llm_config = _extract_llm_config(agent)
    tools = [
        StudioToolInfo(
            name=t.name,
            description=t.description,
            parameters=t.parameters or {},
        )
        for t in agent.tools
    ]
    return StudioAgentDetail(
        agent_id=f"{platform_info.id}/{agent.name}",
        name=agent.name,
        display_name=_get_display_name(agent.name),
        platform_id=platform_info.id,
        platform_name=platform_info.name,
        description=agent.description or "",
        llm_config=llm_config,
        tool_count=len(agent.tools),
        has_system_prompt=bool(agent.system_prompt),
        agent_class=type(agent).__name__,
        status="discovered",
        system_prompt=agent.system_prompt,
        tools=tools,
        parameters={
            "temperature": agent.temperature,
            "max_tokens": agent.max_tokens,
            "model": agent.model,
        },
    )


def _discover_agent(
    platform_info: PlatformInfo,
    agent_name: str,
    orchestrator=None,
) -> Optional[BaseAgent]:
    """
    Discover a single agent by name.

    Two-pass strategy:
    1. Try orchestrator.get_agent() (works for HelloWorld which calls register_agent)
    2. Fall back to the agent factory (needed for Newsletter's LangGraph agents)
    """
    # Strategy 1: orchestrator-registered agents
    if orchestrator:
        agent = orchestrator.get_agent(agent_name)
        if agent:
            return agent

    # Strategy 2: factory-based instantiation
    factory_key = (platform_info.id, agent_name)
    if factory_key in _AGENT_FACTORIES:
        try:
            agent_class = _import_agent_class(_AGENT_FACTORIES[factory_key])
            return agent_class()
        except Exception as e:
            logger.warning(
                f"Failed to instantiate agent '{agent_name}' via factory: {e}"
            )

    return None


def _discover_and_apply(platform_id: str, agent_name: str) -> Tuple[BaseAgent, PlatformInfo]:
    """Discover an agent and apply session overrides. Returns (agent, platform_info)."""
    registry = get_platform_registry()
    platform_info = registry.get(platform_id)

    if not platform_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Platform '{platform_id}' not found",
        )

    if agent_name not in platform_info.agents:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_name}' not found in platform '{platform_id}'",
        )

    orchestrator = None
    try:
        orchestrator = registry.create_orchestrator(platform_id)
    except Exception as e:
        logger.warning(f"Could not create orchestrator for {platform_id}: {e}")

    agent = _discover_agent(platform_info, agent_name, orchestrator)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_name}' could not be instantiated",
        )

    agent_id = f"{platform_id}/{agent_name}"
    _apply_overrides(agent, agent_id)
    return agent, platform_info


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/agents", response_model=StudioAgentsListResponse)
async def list_studio_agents(platform_id: Optional[str] = None):
    """
    Discover all agents across all platforms.

    Iterates the PlatformRegistry, creates orchestrators, and introspects
    each agent for rich metadata.

    Query params:
        platform_id: Optional filter to a single platform.
    """
    registry = get_platform_registry()
    platforms = registry.list_all()

    if platform_id:
        platforms = [p for p in platforms if p.id == platform_id]
        if not platforms:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Platform '{platform_id}' not found",
            )

    all_agents: List[StudioAgentSummary] = []
    platform_summaries: List[StudioPlatformSummary] = []

    for platform_info in platforms:
        orchestrator = None
        try:
            orchestrator = registry.create_orchestrator(platform_info.id)
        except Exception as e:
            logger.warning(
                f"Could not create orchestrator for {platform_info.id}: {e}"
            )

        discovered_names: List[str] = []
        for agent_name in platform_info.agents:
            agent = _discover_agent(platform_info, agent_name, orchestrator)
            if agent:
                agent_id = f"{platform_info.id}/{agent_name}"
                _apply_overrides(agent, agent_id)
                summary = _build_agent_summary(agent, platform_info)
                all_agents.append(summary)
                discovered_names.append(agent_name)
            else:
                logger.warning(
                    f"Could not discover agent '{agent_name}' "
                    f"in platform '{platform_info.id}'"
                )

        platform_summaries.append(
            StudioPlatformSummary(
                id=platform_info.id,
                name=platform_info.name,
                description=platform_info.description,
                version=platform_info.version,
                agent_count=len(discovered_names),
                agents=discovered_names,
                enabled=platform_info.enabled,
            )
        )

    return StudioAgentsListResponse(
        agents=all_agents,
        total=len(all_agents),
        platforms=platform_summaries,
    )


@router.get(
    "/agents/{platform_id}/{agent_name}",
    response_model=StudioAgentDetail,
)
async def get_studio_agent(platform_id: str, agent_name: str):
    """
    Get detailed agent metadata by platform and name.

    Returns full introspection data including system prompt, tools,
    and parameters.  Session overrides are applied before returning.
    """
    agent, platform_info = _discover_and_apply(platform_id, agent_name)
    return _build_agent_detail(agent, platform_info)


@router.patch(
    "/agents/{platform_id}/{agent_name}/config",
    response_model=StudioAgentDetail,
)
async def update_agent_config(
    platform_id: str,
    agent_name: str,
    request: StudioConfigUpdateRequest,
):
    """
    Update agent LLM config (session-only, resets on server restart).

    Merges the provided fields into the session override store and
    returns the updated agent detail.
    """
    agent_id = f"{platform_id}/{agent_name}"

    # Merge new values into existing overrides
    overrides = _session_overrides.setdefault(agent_id, {})
    update = request.model_dump(exclude_none=True)
    overrides.update(update)

    agent, platform_info = _discover_and_apply(platform_id, agent_name)
    return _build_agent_detail(agent, platform_info)


@router.put(
    "/agents/{platform_id}/{agent_name}/prompt",
    response_model=StudioAgentDetail,
)
async def update_agent_prompt(
    platform_id: str,
    agent_name: str,
    request: StudioPromptUpdateRequest,
):
    """
    Update agent system prompt (session-only, resets on server restart).
    """
    agent_id = f"{platform_id}/{agent_name}"

    overrides = _session_overrides.setdefault(agent_id, {})
    overrides["system_prompt"] = request.system_prompt

    agent, platform_info = _discover_and_apply(platform_id, agent_name)
    return _build_agent_detail(agent, platform_info)


@router.post(
    "/agents/{platform_id}/{agent_name}/try",
    response_model=StudioTryResponse,
)
async def try_agent(
    platform_id: str,
    agent_name: str,
    request: StudioTryRequest,
):
    """
    Execute an agent with ad-hoc input and return the result.

    Applies session overrides + optional per-request config_override.
    Times out after 60 seconds.
    """
    agent, platform_info = _discover_and_apply(platform_id, agent_name)
    agent_id = f"{platform_id}/{agent_name}"

    # Apply per-request config overrides (temporary, not persisted)
    if request.config_override:
        co = request.config_override
        if co.temperature is not None:
            agent.temperature = co.temperature
        if co.max_tokens is not None:
            agent.max_tokens = co.max_tokens
        if co.model is not None:
            agent.model = co.model
        if co.provider is not None:
            try:
                provider_type = LLMProviderType(co.provider)
                agent._llm = get_llm_provider(provider_type)
            except (ValueError, Exception):
                pass

    start = time.perf_counter()
    try:
        result = await asyncio.wait_for(agent.run(request.input), timeout=60)
        elapsed_ms = (time.perf_counter() - start) * 1000
        return StudioTryResponse(
            success=True,
            output=result,
            duration_ms=round(elapsed_ms, 1),
            agent_id=agent_id,
        )
    except asyncio.TimeoutError:
        elapsed_ms = (time.perf_counter() - start) * 1000
        return StudioTryResponse(
            success=False,
            error="Agent execution timed out after 60 seconds",
            duration_ms=round(elapsed_ms, 1),
            agent_id=agent_id,
        )
    except Exception as e:
        elapsed_ms = (time.perf_counter() - start) * 1000
        return StudioTryResponse(
            success=False,
            error=str(e),
            duration_ms=round(elapsed_ms, 1),
            agent_id=agent_id,
        )


@router.delete(
    "/agents/{platform_id}/{agent_name}/config",
    response_model=StudioAgentDetail,
)
async def reset_agent_config(platform_id: str, agent_name: str):
    """
    Reset all session overrides for an agent back to defaults.
    """
    agent_id = f"{platform_id}/{agent_name}"
    _session_overrides.pop(agent_id, None)

    agent, platform_info = _discover_and_apply(platform_id, agent_name)
    return _build_agent_detail(agent, platform_info)


@router.get("/providers", response_model=StudioProvidersListResponse)
async def list_providers():
    """
    List all LLM providers with their available models.

    Iterates the LLMProviderType enum and attempts to instantiate each
    provider.  Gracefully handles missing API keys / unreachable services.
    """
    providers: List[StudioProviderInfo] = []

    for pt in LLMProviderType:
        info = StudioProviderInfo(
            name=pt.name.replace("_", " ").title(),
            provider_type=pt.value,
            models=[],
            available=False,
        )
        try:
            provider = get_llm_provider(pt)
            healthy = await provider.health_check()
            if healthy:
                info.available = True
                info.models = await provider.list_models()
            else:
                # Still try to list models even if health check fails
                info.models = await provider.list_models()
        except Exception as e:
            logger.debug(f"Provider {pt.value} not available: {e}")

        providers.append(info)

    return StudioProvidersListResponse(
        providers=providers,
        total=len(providers),
    )


@router.get("/platforms", response_model=StudioPlatformsListResponse)
async def list_studio_platforms():
    """
    List all platforms with agent counts.

    Lighter-weight than /agents — does not instantiate agents.
    """
    registry = get_platform_registry()
    platforms = registry.list_all()

    summaries = [
        StudioPlatformSummary(
            id=p.id,
            name=p.name,
            description=p.description,
            version=p.version,
            agent_count=len(p.agents),
            agents=p.agents,
            enabled=p.enabled,
        )
        for p in platforms
    ]

    return StudioPlatformsListResponse(
        platforms=summaries,
        total=len(summaries),
    )
