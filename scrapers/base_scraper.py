from abc import ABC, abstractmethod
from typing import List

from models.offer import Offer


class BaseScraper(ABC):
    """
    Base class for all leasing provider scrapers.
    """

    provider_name: str = ""

    def collect(self) -> List[Offer]:
        """
        Collect all offers from the provider.
        """

        return self._collect()

    @abstractmethod
    def _collect(self) -> List[Offer]:
        """
        Provider-specific implementation.
        """
        pass

    @abstractmethod
    def collect_offer_urls(self, page):
        """
        Return all offer URLs.
        """
        pass

    @abstractmethod
    def collect_offer(self, page, url):
        """
        Parse a single offer.
        """
        pass