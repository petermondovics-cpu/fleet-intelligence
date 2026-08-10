from abc import ABC, abstractmethod
from typing import Any


class FleetIQPlugin(ABC):
    """
    Base class for all FleetIQ plugins.

    A plugin can represent a scraper, exporter,
    AI module, connector, or another platform component.
    """

    name: str = ""
    version: str = "1.0.0"

    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """
        Execute the plugin.
        """
        raise NotImplementedError