from core import FleetIQ
from scrapers.ayvens.scraper import AyvensScraper


def main():

    fleet = FleetIQ()

    fleet.register(
        AyvensScraper()
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