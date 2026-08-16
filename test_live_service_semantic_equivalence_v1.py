from market_intelligence.market_match_engine import (
    MarketMatchEngine,
)
from market_intelligence.market_pair_full_comparison_bridge import (
    MarketPairFullComparisonBridge,
)

from comparison.service_semantic_equivalence import (
    SEMANTIC_PARTIAL_EQUIVALENCE,
    ServiceSemanticEquivalenceAssessor,
)


TARGET_GROUP = (
    "BYD::ATTO 2::PHEV"
)


def main():

    print("=" * 100)
    print("LIVE ARVAL / AYVENS SERVICE SEMANTIC EQUIVALENCE V1")
    print("=" * 100)

    pair = next(
        (
            item
            for item
            in MarketMatchEngine().build()
            if item.group_key
            == TARGET_GROUP
        ),
        None,
    )

    assert pair is not None

    result = (
        MarketPairFullComparisonBridge()
        .evaluate(
            pair,
            headless=False,
        )
    )

    left = (
        result.enrichment
        .left_services
    )

    right = (
        result.enrichment
        .right_services
    )

    print()
    print("--- ENRICHED SERVICE EVIDENCE ---")

    print(
        left.provider,
        "|",
        left.usable_status,
        "|",
        left.acquired_codes,
    )

    print(
        right.provider,
        "|",
        right.usable_status,
        "|",
        right.acquired_codes,
    )

    semantic = (
        ServiceSemanticEquivalenceAssessor()
        .assess(
            left.package,
            right.package,
        )
    )

    print()
    print("--- SEMANTIC ASSESSMENT ---")

    print(
        "Status:",
        semantic.status,
    )

    print(
        "Core equivalent:",
        semantic.core_equivalent,
    )

    print(
        "Shared:",
        semantic.shared_codes,
    )

    print(
        "Shared core:",
        semantic.shared_core_codes,
    )

    print(
        "Left-only semantics:",
        semantic.left_only_codes,
    )

    print(
        "Right-only semantics:",
        semantic.right_only_codes,
    )

    print(
        "Unresolved common:",
        semantic.unresolved_common_codes,
    )

    print(
        "Functional domains:",
        semantic.functional_domains,
    )

    print(
        "Diagnostic:",
        semantic.diagnostic,
    )

    assert (
        semantic.status
        == SEMANTIC_PARTIAL_EQUIVALENCE
    )

    assert (
        semantic.core_equivalent
        is True
    )

    assert set(
        semantic.left_only_codes
    ) == {
        "CLAIMS_MANAGEMENT",
        "FINANCING",
    }

    assert set(
        semantic.right_only_codes
    ) == {
        "TAXES",
    }

    assert (
        semantic.price_comparison_safe
        is False
    )

    print()
    print(
        "TEST PASSED - LIVE PROVIDER EVIDENCE "
        "ESTABLISHES THE SAME OPERATIONAL/CORE "
        "SERVICE BASELINE, WHILE CLAIMS MANAGEMENT, "
        "FINANCING AND TAXES REMAIN DISTINCT "
        "ONE-SIDED SEMANTICS. NO FALSE FULL "
        "EQUIVALENCE WAS CREATED."
    )


if __name__ == "__main__":
    main()
