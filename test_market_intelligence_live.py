from core import FleetIQ

from market_intelligence.engine import (
    MarketIntelligenceEngine,
)

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

    print(
        "\n================================"
    )

    print(
        "FLEETIQ MARKET INTELLIGENCE V2.1"
    )

    print(
        "================================"
    )

    offers = fleet.collect()

    engine = (
        MarketIntelligenceEngine()
    )

    result = engine.analyze(
        offers
    )

    print(
        "\n================================"
    )

    print(
        "MARKET OVERVIEW"
    )

    print(
        "================================"
    )

    print(
        f"Offers collected: "
        f"{result.offers_count}"
    )

    print(
        f"Vehicle groups: "
        f"{result.benchmark_count}"
    )

    print(
        f"Vehicle comparisons: "
        f"{result.comparison_count}"
    )

    print(
        f"Directly comparable: "
        f"{result.comparable_comparisons}"
    )

    print(
        f"Non-comparable: "
        f"{result.non_comparable_comparisons}"
    )

    print(
        f"Market positioning: "
        f"{len(result.positioning_results)}"
    )

    print(
        f"Provider rankings: "
        f"{len(result.ranking_results)}"
    )

    # ------------------------------------------------
    # PROVIDER RANKING
    # ------------------------------------------------

    print(
        "\n================================"
    )

    print(
        "PROVIDER RANKING"
    )

    print(
        "================================"
    )

    if not result.ranking_results:

        print(
            "\n⚠️ No directly comparable "
            "contracts available."
        )

    else:

        for ranking in (
            result.ranking_results
        ):

            print(
                "\n" + "-" * 60
            )

            print(
                f"#{ranking.rank} "
                f"{ranking.provider}"
            )

            print(
                f"Comparable models: "
                f"{ranking.comparable_comparisons}"
            )

            print(
                f"Wins: "
                f"{ranking.wins}"
            )

            print(
                f"Win rate: "
                f"{ranking.win_rate}%"
            )

            print(
                f"Average advantage: "
                f"{ranking.average_monthly_advantage:,.0f} Ft"
            )

            print(
                f"Average advantage %: "
                f"{ranking.average_price_advantage_percent:.2f}%"
            )

            print(
                f"Annual saving potential: "
                f"{ranking.total_annual_saving:,} Ft"
            )

            print(
                f"Competitive rate: "
                f"{ranking.competitive_rate}%"
            )

    # ------------------------------------------------
    # MARKET POSITIONING
    # ------------------------------------------------

    print(
        "\n================================"
    )

    print(
        "MARKET POSITIONING"
    )

    print(
        "================================"
    )

    for position in (
        result.positioning_results
    ):

        print(
            "\n" + "-" * 70
        )

        print(
            f"🚗 "
            f"{position.brand} "
            f"{position.model}"
        )

        print(
            f"Providers: "
            f"{', '.join(position.providers)}"
        )

        for offer in position.offers:

            print(
                f"  {offer.provider}: "
                f"{offer.monthly_fee:,} Ft "
                f"("
                f"{offer.duration} hó / "
                f"{offer.mileage:,} km / "
                f"{offer.fuel_type}"
                f")"
            )

        print(
            f"Lowest nominal price: "
            f"{position.lowest_provider} "
            f"— "
            f"{position.lowest_monthly_fee:,} Ft"
        )

        print(
            f"Highest nominal price: "
            f"{position.highest_provider} "
            f"— "
            f"{position.highest_monthly_fee:,} Ft"
        )

        print(
            f"Nominal difference: "
            f"{position.price_difference:,} Ft/month"
        )

        print(
            f"Nominal difference: "
            f"{position.price_difference_percent:.2f}%"
        )

        print(
            f"Vehicle match: "
            f"{position.vehicle_confidence}% "
            f"({position.vehicle_match_type})"
        )

        if position.contract_comparable:

            print(
                "Contract: COMPARABLE"
            )

        else:

            print(
                "Contract: NOT_COMPARABLE"
            )

            if position.contract_difference:

                print(
                    f"Reason: "
                    f"{position.contract_difference}"
                )

        print(
            f"Position type: "
            f"{position.position_type}"
        )

        print(
            f"Nominal price position: "
            f"{position.nominal_price_position}"
        )

        print(
            f"Price winner: "
            f"{position.price_winner}"
        )

        print(
            f"Price winner valid: "
            f"{position.price_winner_is_valid}"
        )

        if position.data_quality_warning:

            print(
                "⚠️ Data quality: WARNING"
            )

            print(
                f"Reason: "
                f"{position.data_quality_reason}"
            )

    print(
        "\n================================"
    )


if __name__ == "__main__":
    main()