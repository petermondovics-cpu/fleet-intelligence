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

    offers = fleet.collect()

    normalizer = (
        fleet.vehicle_normalizer
    )

    grouped = {}

    for offer in offers:

        key = normalizer.vehicle_key(
            offer.brand,
            offer.model,
            offer.fuel_type,
        )

        if key not in grouped:
            grouped[key] = []

        grouped[key].append(
            offer
        )

    print("\n================================")
    print("VEHICLE MATCHING")
    print("================================")

    for key, vehicle_offers in grouped.items():

        if len(vehicle_offers) < 2:
            continue

        print("\nVehicle:", key)

        for offer in vehicle_offers:

            print(
                f"  {offer.provider}: "
                f"{offer.monthly_fee:,} Ft "
                f"({offer.duration} hó / "
                f"{offer.mileage:,} km)"
            )


if __name__ == "__main__":
    main()