from core import FleetIQ

from comparison.engine import ComparisonEngine

from scrapers.arval.scraper import ArvalScraper
from scrapers.ayvens.scraper import AyvensScraper


def main():

    fleet = FleetIQ()

    fleet.register(
        ArvalScraper()
    )

    fleet.register(
        AyvensScraper()
    )

    offers = fleet.collect()

    engine = ComparisonEngine()

    results = engine.compare(
        offers
    )

    print("\n================================")
    print("FLEETIQ PRICE COMPARISON")
    print("================================")

    if not results:

        print(
            "No cross-provider matches found."
        )

        return

    for result in results:

        print(
            f"\n🚗 "
            f"{result.brand} "
            f"{result.model} "
            f"({result.fuel_type})"
        )

        if result.comparable:

            print(
                f"✅ Comparable contract: "
                f"{result.duration} months / "
                f"{result.mileage:,} km/year"
            )

        else:

            print(
                f"⚠️ Not directly comparable: "
                f"{result.contract_difference}"
            )

        for offer in result.offers:

            print(
                f"  {offer.provider}: "
                f"{offer.monthly_fee:,} Ft "
                f"({offer.duration} hó / "
                f"{offer.mileage:,} km)"
            )

        if result.comparable:

            print(
                f"🏆 Best: "
                f"{result.best_provider}"
            )

            print(
                f"💰 Difference: "
                f"{result.price_difference:,} Ft/month"
            )

            print(
                f"📅 Annual saving: "
                f"{result.annual_saving:,} Ft"
            )

    print(
        f"\nVehicle comparisons: "
        f"{len(results)}"
    )


if __name__ == "__main__":
    main()