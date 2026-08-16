from market_intelligence.market_match_engine import MarketMatchEngine
from market_intelligence.market_pair_full_comparison_bridge import (
    MarketPairFullComparisonBridge,
)

TARGET_GROUP = "BYD::ATTO 2::PHEV"

OLD_CODES = {
    "SERVICE_LEFT_ONLY_PUBLISHED",
    "SERVICE_RIGHT_ONLY_PUBLISHED",
    "SERVICE_EVIDENCE_INCOMPLETE",
}

def main():
    print("=" * 100)
    print("LIVE FULL COMPARISON - SERVICE SEMANTIC ORCHESTRATOR INTEGRATION V1")
    print("=" * 100)

    pair = next(
        (
            item
            for item in MarketMatchEngine().build()
            if item.group_key == TARGET_GROUP
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

    final = result.final_comparison
    assert final is not None

    print()
    print("--- FINAL DIMENSIONS ---")
    print("Status:", final.status)
    print("Service:", final.service_status)
    print("Price comparison allowed:", final.price_comparison_allowed)
    print("Price winner:", final.price_winner)

    print()
    print("--- FINAL BLOCKERS ---")
    for blocker in final.barriers:
        print("-", blocker.code, "|", blocker.message)

    codes = set(final.blocker_codes)

    assert "SERVICE_SEMANTIC_EQUIVALENCE_INCOMPLETE" in codes
    assert not (OLD_CODES & codes)
    assert final.service_status == "PARTIAL_EQUIVALENCE"

    # Critical safety invariant: partial equivalence still blocks price.
    assert final.price_comparison_allowed is False
    assert final.price_winner is None

    print()
    print(
        "TEST PASSED - FULL COMPARISON NOW REPORTS ONE CONSOLIDATED "
        "SEMANTIC SERVICE BLOCKER, PRESERVES PARTIAL_EQUIVALENCE, "
        "AND STILL REFUSES TO FABRICATE A PRICE WINNER."
    )

if __name__ == "__main__":
    main()
