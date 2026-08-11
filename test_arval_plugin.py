from core import FleetIQ
from scrapers.arval.scraper import ArvalScraper


def main():

    fleet = FleetIQ()

    arval = ArvalScraper()

    fleet.register(arval)

    print("Registered plugins:")
    print(fleet.plugins())


if __name__ == "__main__":
    main()