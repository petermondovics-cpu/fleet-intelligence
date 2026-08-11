from core import FleetIQ

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

    print("\nRegistered plugins:")
    print(fleet.plugins())

    offers = fleet.collect()

    print(
        f"\nTotal offers: "
        f"{len(offers)}"
    )

    print(
        "\nNormalized offers:"
    )

    for offer in offers:

        print(
            f"{offer.provider:10} | "
            f"{offer.brand:12} | "
            f"{offer.model:20} | "
            f"{offer.fuel_type:8} | "
            f"{offer.monthly_fee:,} Ft"
        )


if __name__ == "__main__":
    main()