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
        "FLEETIQ MARKET INTELLIGENCE V3"
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

    # ------------------------------------------------
    # MARKET OVERVIEW
    # ------------------------------------------------

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

    print(
        f"Contract normalization: "
        f"{len(result.normalization_results)}"
    )

    # ------------------------------------------------
    # CONTRACT NORMALIZATION V3 SUMMARY
    # ------------------------------------------------

    print(
        "\n--------------------------------"
    )

    print(
        "CONTRACT NORMALIZATION V3 SUMMARY"
    )

    print(
        "--------------------------------"
    )

    print(
        f"Normalized comparisons: "
        f"{result.normalized_comparisons}"
    )

    print(
        f"Estimated normalizations: "
        f"{result.estimated_normalizations}"
    )

    print(
        f"Term normalization required: "
        f"{result.term_normalizations_required}"
    )

    print(
        f"Mileage normalization required: "
        f"{result.mileage_normalizations_required}"
    )

    print(
        f"Term + mileage normalization required: "
        f"{result.term_and_mileage_normalizations_required}"
    )

    print(
        f"Unsupported normalizations: "
        f"{result.unsupported_normalizations}"
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

    if not result.positioning_results:

        print(
            "\n⚠️ No multi-provider "
            "vehicle groups available."
        )

    else:

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

    # ------------------------------------------------
    # CONTRACT NORMALIZATION V3
    # ------------------------------------------------

    print(
        "\n================================"
    )

    print(
        "CONTRACT NORMALIZATION V3"
    )

    print(
        "================================"
    )

    if not result.normalization_results:

        print(
            "\n⚠️ No comparison results "
            "available for normalization."
        )

    else:

        for normalization in (
            result.normalization_results
        ):

            print(
                "\n" + "-" * 70
            )

            print(
                f"🚗 "
                f"{normalization.brand} "
                f"{normalization.model}"
            )

            print(
                f"Providers: "
                f"{normalization.provider_a}, "
                f"{normalization.provider_b}"
            )

            print(
                f"Contract A: "
                f"{normalization.duration_a} hó / "
                f"{normalization.mileage_a:,} km"
            )

            print(
                f"Contract B: "
                f"{normalization.duration_b} hó / "
                f"{normalization.mileage_b:,} km"
            )

            print(
                f"Duration difference: "
                f"{normalization.duration_difference} hó"
            )

            print(
                f"Mileage difference: "
                f"{normalization.mileage_difference:,} km/year"
            )

            print(
                f"Duration similarity: "
                f"{normalization.duration_similarity}%"
            )

            print(
                f"Mileage similarity: "
                f"{normalization.mileage_similarity}%"
            )

            print(
                f"Contract similarity: "
                f"{normalization.contract_similarity}%"
            )

            print(
                f"Normalization status: "
                f"{normalization.normalization_status}"
            )

            print(
                f"Normalization method: "
                f"{normalization.normalization_method}"
            )

            print(
                f"Normalization confidence: "
                f"{normalization.normalization_confidence}%"
            )

            if (
                normalization.normalization_factor_a
                is not None
            ):

                print(
                    f"Normalization factor A: "
                    f"{normalization.normalization_factor_a:.6f}"
                )

            else:

                print(
                    "Normalization factor A: "
                    "NOT_AVAILABLE"
                )

            if (
                normalization.normalization_factor_b
                is not None
            ):

                print(
                    f"Normalization factor B: "
                    f"{normalization.normalization_factor_b:.6f}"
                )

            else:

                print(
                    "Normalization factor B: "
                    "NOT_AVAILABLE"
                )

            if (
                normalization.normalized_price_available
            ):

                if (
                    normalization.normalized_monthly_fee_a
                    is not None
                ):

                    print(
                        f"Normalized "
                        f"{normalization.provider_a}: "
                        f"{normalization.normalized_monthly_fee_a:,} Ft"
                    )

                else:

                    print(
                        f"Normalized "
                        f"{normalization.provider_a}: "
                        "NOT_AVAILABLE"
                    )

                if (
                    normalization.normalized_monthly_fee_b
                    is not None
                ):

                    print(
                        f"Normalized "
                        f"{normalization.provider_b}: "
                        f"{normalization.normalized_monthly_fee_b:,} Ft"
                    )

                else:

                    print(
                        f"Normalized "
                        f"{normalization.provider_b}: "
                        "NOT_AVAILABLE"
                    )

            else:

                print(
                    "Normalized price: "
                    "NOT_AVAILABLE"
                )

            if normalization.normalization_reason:

                print(
                    f"Reason: "
                    f"{normalization.normalization_reason}"
                )

            if normalization.normalization_evidence:

                print(
                    f"Evidence: "
                    f"{normalization.normalization_evidence}"
                )

    # ------------------------------------------------
    # END
    # ------------------------------------------------

    print(
        "\n================================"
    )

    print(
        "END OF MARKET INTELLIGENCE V3"
    )

    print(
        "================================"
    )


if __name__ == "__main__":
    main()