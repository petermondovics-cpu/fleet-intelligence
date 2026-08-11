from typing import List

from core.plugin import FleetIQPlugin
from core.registry import PluginRegistry
from core.scraper_plugin import ScraperPlugin

from models.offer import Offer

from normalizers.vehicle_normalizer import (
    VehicleNormalizer,
)

from quality.data_quality import (
    DataQualityChecker,
)


class FleetIQ:
    """
    Main orchestration engine of the FleetIQ platform.

    FleetIQ coordinates registered plugins and
    normalizes collected vehicle data.
    """

    def __init__(self) -> None:

        self.registry = PluginRegistry()

        self.vehicle_normalizer = (
            VehicleNormalizer()
        )

        self.data_quality_checker = (
            DataQualityChecker()
        )

    def register(
        self,
        plugin: FleetIQPlugin,
    ) -> None:

        self.registry.register(plugin)

    def plugins(self) -> List[str]:

        return self.registry.names()

    def collect(self) -> List[Offer]:

        offers: List[Offer] = []

        for plugin in self.registry.all():

            if not isinstance(
                plugin,
                ScraperPlugin,
            ):
                continue

            print(
                f"\n🚗 Running scraper: "
                f"{plugin.name}"
            )

            try:

                plugin_offers = (
                    plugin.collect()
                )

                normalized_offers = (
                    self.normalize_offers(
                        plugin_offers
                    )
                )

                for offer in normalized_offers:

                    quality = (
                        self.data_quality_checker.check_offer(
                            offer
                        )
                    )

                    # DEBUG: inspect BYD ATTO 3
                    # before changing the quality logic
                    if (
                        offer.brand == "BYD"
                        and "ATTO 3" in offer.model
                    ):

                        print(
                            "🔍 QUALITY DEBUG:"
                        )

                        print(
                            f"brand={offer.brand}"
                        )

                        print(
                            f"model={offer.model}"
                        )

                        print(
                            f"trim={offer.trim}"
                        )

                        print(
                            f"fuel={offer.fuel_type}"
                        )

                        print(
                            f"raw_title={offer.raw_title}"
                        )

                    if quality.issues:

                        print(
                            f"⚠️ Data quality: "
                            f"{offer.provider} | "
                            f"{offer.brand} "
                            f"{offer.model} | "
                            f"{quality.confidence}%"
                        )

                        for issue in quality.issues:

                            print(
                                f"   {issue.severity}: "
                                f"{issue.message}"
                            )

                offers.extend(
                    normalized_offers
                )

                print(
                    f"✅ {plugin.name}: "
                    f"{len(normalized_offers)} offers"
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

    def normalize_offers(
        self,
        offers: List[Offer],
    ) -> List[Offer]:

        for offer in offers:

            raw_title = (
                offer.model
                or offer.trim
            )

            offer.raw_title = raw_title

            normalized = (
                self.vehicle_normalizer.normalize(
                    raw_title,
                    offer.fuel_type,
                )
            )

            offer.brand = (
                normalized["brand"]
            )

            offer.model = (
                normalized["model"]
            )

            offer.fuel_type = (
                normalized["fuel_type"]
            )

        return offers