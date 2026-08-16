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
        "FLEETIQ MARKET INTELLIGENCE V5"
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

    # ------------------------------------------------
    # CONTRACT EVIDENCE V1
    # ------------------------------------------------

    print(
        "\n================================"
    )

    print(
        "CONTRACT EVIDENCE V1"
    )

    print(
        "================================"
    )

    print(
        f"Total observed evidence: "
        f"{result.evidence_count}"
    )

    print(
        f"Term evidence: "
        f"{result.term_evidence_count}"
    )

    print(
        f"Mileage evidence: "
        f"{result.mileage_evidence_count}"
    )

    if not result.evidence_results:

        print(
            "\n⚠️ No observed contract "
            "evidence found."
        )

    else:

        for evidence in result.evidence_results:

            print(
                "\n" + "-" * 70
            )

            print(
                f"Provider: "
                f"{evidence.provider}"
            )

            print(
                f"Vehicle: "
                f"{evidence.brand} "
                f"{evidence.model}"
            )

            print(
                f"Evidence type: "
                f"{evidence.evidence_type}"
            )

            print(
                f"Source contract: "
                f"{evidence.source_duration} hó / "
                f"{evidence.source_mileage:,} km"
            )

            print(
                f"Target contract: "
                f"{evidence.target_duration} hó / "
                f"{evidence.target_mileage:,} km"
            )

            print(
                f"Source price: "
                f"{evidence.source_monthly_fee:,} Ft"
            )

            print(
                f"Target price: "
                f"{evidence.target_monthly_fee:,} Ft"
            )

            print(
                f"Observed factor: "
                f"{evidence.factor:.6f}"
            )

            print(
                f"Sample size: "
                f"{evidence.sample_size}"
            )

    # ------------------------------------------------
    # CONTRACT NORMALIZATION V4
    # ------------------------------------------------

    print(
        "\n================================"
    )

    print(
        "CONTRACT NORMALIZATION V4"
    )

    print(
        "================================"
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
            normalization.normalized_price_available
        ):

            print(
                f"Normalized "
                f"{normalization.provider_a}: "
                f"{normalization.normalized_monthly_fee_a:,} Ft"
            )

            print(
                f"Normalized "
                f"{normalization.provider_b}: "
                f"{normalization.normalized_monthly_fee_b:,} Ft"
            )

        else:

            print(
                "Normalized price: "
                "NOT_AVAILABLE"
            )

        if (
            normalization.normalization_reason
        ):

            print(
                f"Reason: "
                f"{normalization.normalization_reason}"
            )

        if (
            normalization.normalization_evidence
        ):

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
        "END OF MARKET INTELLIGENCE V5"
    )

    print(
        "================================"
    )


if __name__ == "__main__":
    main()
