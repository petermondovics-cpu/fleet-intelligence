from abc import abstractmethod
from typing import List

from core.plugin import FleetIQPlugin
from models.offer import Offer


class ScraperPlugin(FleetIQPlugin):
    """
    Base plugin for FleetIQ data collectors.

    Every provider scraper must implement collect()
    and return a list of Offer objects.
    """

    category: str = "scraper"

    @abstractmethod
    def collect(self) -> List[Offer]:
        """
        Collect offers from the provider.
        """
        raise NotImplementedError

    def execute(self) -> List[Offer]:
        """
        FleetIQ plugin interface.

        For scraper plugins, execute() delegates to collect().
        """
        return self.collect()