from core import FleetIQ
from scrapers.arval.scraper import ArvalScraper


def main():

    fleet = FleetIQ()

    fleet.register(
        ArvalScraper()
    )

    print(
        "\nRegistered plugins:"
    )

    print(
        fleet.plugins()
    )

    offers = fleet.collect()

    print(
        f"\nCollected offers: "
        f"{len(offers)}"
    )


if __name__ == "__main__":
    main()