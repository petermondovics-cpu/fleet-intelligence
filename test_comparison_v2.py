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
    print("FLEETIQ COMPARISON ENGINE 2.0")
    print("================================")

    print(
        f"\nComparison results: "
        f"{len(results)}"
    )

    for result in results:

        print("\n" + "-" * 70)

        # ------------------------------------------------
        # VEHICLE
        # ------------------------------------------------

        print(
            f"🚗 "
            f"{result.brand} "
            f"{result.model}"
        )

        # ------------------------------------------------
        # VEHICLE MATCH
        # ------------------------------------------------

        print(
            f"Vehicle confidence: "
            f"{result.vehicle_confidence}%"
        )

        print(
            f"Vehicle match: "
            f"{result.vehicle_match_type}"
        )

        if (
            result.vehicle_match_type
            == "MODEL_MATCH_POWERTRAIN_MISMATCH"
        ):

            print(
                "⚠️ Vehicle: "
                "POTENTIAL MATCH"
            )

            print(
                "Reason: powertrain mismatch"
            )

        # ------------------------------------------------
        # CONTRACT SIMILARITY
        # ------------------------------------------------

        print(
            f"Duration similarity: "
            f"{result.duration_similarity}%"
        )

        print(
            f"Mileage similarity: "
            f"{result.mileage_similarity}%"
        )

        print(
            f"Contract similarity: "
            f"{result.contract_similarity}%"
        )

        # ------------------------------------------------
        # OFFERS
        # ------------------------------------------------

        for index, offer in enumerate(
            result.offers
        ):

            if index == 0:

                fuel_type = (
                    result.fuel_type_a
                )

            else:

                fuel_type = (
                    result.fuel_type_b
                )

            print(
                f"  {offer.provider}: "
                f"{fuel_type} | "
                f"{offer.monthly_fee:,} Ft "
                f"("
                f"{offer.duration} hó / "
                f"{offer.mileage:,} km"
                f")"
            )

        # ------------------------------------------------
        # CONTRACT COMPARISON
        # ------------------------------------------------

        if result.contract_comparable:

            print(
                "✅ Contract: "
                "DIRECTLY COMPARABLE"
            )

            # --------------------------------------------
            # PRICE WINNER
            # --------------------------------------------

            if result.price_winner_is_valid:

                print(
                    f"🏆 Price winner: "
                    f"{result.price_winner}"
                )

                print(
                    f"💰 Monthly price difference: "
                    f"{result.price_difference:,} Ft"
                )

                print(
                    f"💰 Annual saving: "
                    f"{result.annual_saving:,} Ft"
                )

                print(
                    f"📊 Price difference: "
                    f"{result.price_difference_percent:.2f}%"
                )

            else:

                print(
                    "⚠️ Price winner: "
                    "NOT_COMPARABLE"
                )

        else:

            print(
                "⚠️ Contract: "
                "NOT DIRECTLY COMPARABLE"
            )

            print(
                f"Reason: "
                f"{result.contract_difference}"
            )

            print(
                f"💰 Monthly price difference: "
                f"{result.price_difference:,} Ft"
            )

            print(
                f"💰 Annual price difference: "
                f"{result.annual_saving:,} Ft"
            )

            print(
                f"📊 Price difference: "
                f"{result.price_difference_percent:.2f}%"
            )

            if result.price_winner_is_valid:

                print(
                    f"🏆 Price winner: "
                    f"{result.price_winner}"
                )

            else:

                print(
                    "⚠️ Price winner: "
                    "NOT_COMPARABLE"
                )

    print("\n================================")


if __name__ == "__main__":
    main()