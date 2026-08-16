from market_intelligence.market_match_engine import (
    MarketMatchEngine,
)
from market_intelligence.market_pair_full_comparison_bridge import (
    PAIR_EVALUATED,
    MarketPairFullComparisonBridge,
)


TARGET_GROUP = "BYD::ATTO 2::PHEV"


def service_codes(enriched_side):
    return tuple(
        sorted(
            enriched_side.acquired_codes
        )
    )


def service_blockers(payload):
    return tuple(
        item["code"]
        for item in payload["blockers"]
        if item["code"].startswith("SERVICE_")
    )


def main():
    print("=" * 100)
    print("LIVE ARVAL SERVICE ACQUISITION -> ENRICH -> FULL REASSESS V1")
    print("=" * 100)

    pair = next(
        (
            p
            for p in MarketMatchEngine().build()
            if p.group_key == TARGET_GROUP
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

    assert result.status == PAIR_EVALUATED
    assert result.enrichment is not None
    assert result.response is not None

    left = result.enrichment.left_services
    right = result.enrichment.right_services

    print()
    print("--- ENRICHED SERVICES ---")
    print(
        "Left:",
        left.provider,
        "|",
        left.usable_status,
        "|",
        service_codes(left),
    )
    print(
        "Right:",
        right.provider,
        "|",
        right.usable_status,
        "|",
        service_codes(right),
    )

    arval = (
        left
        if left.provider == "Arval"
        else right
    )

    expected_arval = {
        "INSURANCE",
        "CLAIMS_MANAGEMENT",
        "FINANCING",
        "TYRES",
        "MAINTENANCE",
        "ROADSIDE_ASSISTANCE",
        "FLEET_PORTAL",
    }

    assert arval.acquisition_used is True
    assert set(arval.acquired_codes) == expected_arval

    payload = result.response.to_dict()

    print()
    print("--- FULL SERVICE REASSESSMENT ---")
    print(
        "Service status:",
        payload["dimensions"]["services"],
    )
    print(
        "Service blockers:",
        service_blockers(payload),
    )

    print()
    print("--- ALL BLOCKERS ---")
    for blocker in payload["blockers"]:
        print(
            "-",
            blocker["code"],
            "|",
            blocker["message"],
        )

    # Safety remains authoritative even after stronger service evidence.
    if not payload["price_comparison_allowed"]:
        assert payload["price_winner"] is None

    print()
    print(
        "TEST PASSED - STRUCTURED ARVAL EXACT-OFFER "
        "SERVICES FLOW THROUGH ACQUISITION, ENRICHMENT "
        "AND FULL SERVICE REASSESSMENT WITHOUT "
        "FABRICATING A PRICE WINNER."
    )


if __name__ == "__main__":
    main()
