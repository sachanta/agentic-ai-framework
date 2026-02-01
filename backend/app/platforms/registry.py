"""
Platform registry for discovering and managing multi-agent platforms.
"""
from typing import Dict, List, Optional, Type
from dataclasses import dataclass, field

from app.common.base.orchestrator import BaseOrchestrator


@dataclass
class PlatformInfo:
    """Information about a registered platform."""

    id: str
    name: str
    description: str
    version: str
    orchestrator_class: Type[BaseOrchestrator]
    agents: List[str] = field(default_factory=list)
    enabled: bool = True
    config: Dict = field(default_factory=dict)


class PlatformRegistry:
    """
    Registry for multi-agent platforms.

    Provides platform discovery, registration, and lifecycle management.
    """

    _instance: Optional["PlatformRegistry"] = None
    _platforms: Dict[str, PlatformInfo] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._platforms = {}
        return cls._instance

    def register(
        self,
        platform_id: str,
        name: str,
        description: str,
        orchestrator_class: Type[BaseOrchestrator],
        version: str = "1.0.0",
        agents: List[str] = None,
        config: Dict = None,
    ) -> None:
        """Register a platform with the registry."""
        self._platforms[platform_id] = PlatformInfo(
            id=platform_id,
            name=name,
            description=description,
            version=version,
            orchestrator_class=orchestrator_class,
            agents=agents or [],
            config=config or {},
        )

    def unregister(self, platform_id: str) -> bool:
        """Unregister a platform from the registry."""
        if platform_id in self._platforms:
            del self._platforms[platform_id]
            return True
        return False

    def get(self, platform_id: str) -> Optional[PlatformInfo]:
        """Get platform info by ID."""
        return self._platforms.get(platform_id)

    def list_all(self) -> List[PlatformInfo]:
        """List all registered platforms."""
        return list(self._platforms.values())

    def list_enabled(self) -> List[PlatformInfo]:
        """List only enabled platforms."""
        return [p for p in self._platforms.values() if p.enabled]

    def create_orchestrator(self, platform_id: str) -> Optional[BaseOrchestrator]:
        """Create an orchestrator instance for a platform."""
        platform = self.get(platform_id)
        if platform:
            return platform.orchestrator_class(
                name=platform.name,
                description=platform.description,
            )
        return None

    def enable(self, platform_id: str) -> bool:
        """Enable a platform."""
        if platform_id in self._platforms:
            self._platforms[platform_id].enabled = True
            return True
        return False

    def disable(self, platform_id: str) -> bool:
        """Disable a platform."""
        if platform_id in self._platforms:
            self._platforms[platform_id].enabled = False
            return True
        return False


# Global registry instance
_registry: Optional[PlatformRegistry] = None


def get_platform_registry() -> PlatformRegistry:
    """Get the global platform registry instance."""
    global _registry
    if _registry is None:
        _registry = PlatformRegistry()
    return _registry
