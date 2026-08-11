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
        f"\nTotal FleetIQ offers: "
        f"{len(offers)}"
    )

    print("\nOffers by provider:")

    providers = {}

    for offer in offers:

        providers.setdefault(
            offer.provider,
            0
        )

        providers[offer.provider] += 1

    for provider, count in providers.items():

        print(
            f"{provider}: {count}"
        )


if __name__ == "__main__":
    main()