from typing import List

from core.plugin import FleetIQPlugin
from core.registry import PluginRegistry


class FleetIQ:
    """
    Main orchestration engine of the FleetIQ platform.

    The engine coordinates plugins but does not contain
    provider-specific business logic.
    """

    def __init__(self) -> None:
        self.registry = PluginRegistry()

    def register(self, plugin: FleetIQPlugin) -> None:
        """
        Register a plugin with FleetIQ.
        """

        self.registry.register(plugin)

    def plugins(self) -> List[str]:
        """
        Return the names of all registered plugins.
        """

        return self.registry.names()
