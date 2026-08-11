from core import FleetIQ

from matching.vehicle_matcher import VehicleMatcher

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

    matcher = VehicleMatcher()

    arval_offers = [
        offer
        for offer in offers
        if offer.provider.lower() == "arval"
    ]

    ayvens_offers = [
        offer
        for offer in offers
        if offer.provider.lower() == "ayvens"
    ]

    print("\n================================")
    print("FLEETIQ LIVE VEHICLE MATCHING")
    print("================================")

    print(
        f"\nArval offers: "
        f"{len(arval_offers)}"
    )

    print(
        f"Ayvens offers: "
        f"{len(ayvens_offers)}"
    )

    matches = []

    for arval in arval_offers:

        for ayvens in ayvens_offers:

            result = matcher.match(
                arval.brand,
                arval.model,
                arval.fuel_type,

                ayvens.brand,
                ayvens.model,
                ayvens.fuel_type,
            )

            if result.confidence >= 80:

                matches.append(
                    (
                        result.confidence,
                        arval,
                        ayvens,
                        result,
                    )
                )

    matches.sort(
        key=lambda item: (
            -item[0],
            item[1].brand,
            item[1].model,
        )
    )

    print(
        f"\nPotential matches: "
        f"{len(matches)}"
    )

    for (
        confidence,
        arval,
        ayvens,
        result,
    ) in matches:

        print("\n" + "-" * 70)

        print(
            f"Match confidence: "
            f"{confidence}%"
        )

        print(
            f"Match type: "
            f"{result.match_type}"
        )

        print(
            f"\nARVAL"
        )

        print(
            f"  {arval.brand} "
            f"{arval.model}"
        )

        print(
            f"  Fuel: "
            f"{arval.fuel_type}"
        )

        print(
            f"  Price: "
            f"{arval.monthly_fee:,} Ft"
        )

        print(
            f"  Contract: "
            f"{arval.duration} hó / "
            f"{arval.mileage:,} km"
        )

        print(
            f"\nAYVENS"
        )

        print(
            f"  {ayvens.brand} "
            f"{ayvens.model}"
        )

        print(
            f"  Fuel: "
            f"{ayvens.fuel_type}"
        )

        print(
            f"  Price: "
            f"{ayvens.monthly_fee:,} Ft"
        )

        print(
            f"  Contract: "
            f"{ayvens.duration} hó / "
            f"{ayvens.mileage:,} km"
        )


if __name__ == "__main__":
    main()