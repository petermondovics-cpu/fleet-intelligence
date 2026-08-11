from typing import List

from core.plugin import FleetIQPlugin
from core.registry import PluginRegistry
from core.scraper_plugin import ScraperPlugin
from models.offer import Offer


class FleetIQ:
    """
    Main orchestration engine of the FleetIQ platform.

    FleetIQ coordinates registered plugins but does not
    contain provider-specific scraping logic.
    """

    def __init__(self) -> None:
        self.registry = PluginRegistry()

    def register(self, plugin: FleetIQPlugin) -> None:
        """
        Register a plugin.
        """

        self.registry.register(plugin)

    def plugins(self) -> List[str]:
        """
        Return registered plugin names.
        """

        return self.registry.names()

    def collect(self) -> List[Offer]:
        """
        Run all registered scraper plugins and collect
        their offers.
        """

        offers: List[Offer] = []

        for plugin in self.registry.all():

            if not isinstance(plugin, ScraperPlugin):
                continue

            print(
                f"\n🚗 Running scraper: "
                f"{plugin.name}"
            )

            try:

                plugin_offers = plugin.collect()

                offers.extend(plugin_offers)

                print(
                    f"✅ {plugin.name}: "
                    f"{len(plugin_offers)} offers"
                )

            except Exception as e:

                print(
                    f"❌ {plugin.name} failed:"
                )

                print(e)

        print(
            f"\n📊 FleetIQ collected "
            f"{len(offers)} offers total"
        )

        return offers