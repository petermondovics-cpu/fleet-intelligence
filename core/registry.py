from typing import Dict, List

from core.plugin import FleetIQPlugin


class PluginRegistry:
    """
    Central registry for FleetIQ plugins.
    """

    def __init__(self) -> None:
        self._plugins: Dict[str, FleetIQPlugin] = {}

    def register(self, plugin: FleetIQPlugin) -> None:
        """
        Register a plugin.

        Raises:
            ValueError: if a plugin with the same name
            is already registered.
        """

        if not plugin.name:
            raise ValueError(
                "Plugin must define a name."
            )

        if plugin.name in self._plugins:
            raise ValueError(
                f"Plugin already registered: {plugin.name}"
            )

        self._plugins[plugin.name] = plugin

    def get(self, name: str) -> FleetIQPlugin:
        """
        Get a registered plugin by name.
        """

        try:
            return self._plugins[name]

        except KeyError:
            raise KeyError(
                f"Plugin not found: {name}"
            )

    def all(self) -> List[FleetIQPlugin]:
        """
        Return all registered plugins.
        """

        return list(self._plugins.values())

    def names(self) -> List[str]:
        """
        Return the names of all registered plugins.
        """

        return list(self._plugins.keys())