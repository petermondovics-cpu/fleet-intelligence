from market_intelligence.market_match_engine import (
    MarketMatchEngine,
)
from market_intelligence.market_pair_full_comparison_bridge import (
    MarketPairFullComparisonBridge,
)

TARGET_GROUP = "BYD::ATTO 2::PHEV"


def main():
    print("=" * 100)
    print("LIVE FULL COMPARISON FINANCIAL PROVENANCE V1.1")
    print("=" * 100)

    pair = next(
        (
            item
            for item in MarketMatchEngine().build()
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

    final = (
        result.final_comparison
    )

    assert (
        final is not None
    )

    print()
    print("--- FINANCIAL DIMENSION ---")
    print(
        "Financial status:",
        final.financial_status,
    )
    print(
        "Price comparison allowed:",
        final.price_comparison_allowed,
    )
    print(
        "Price winner:",
        final.price_winner,
    )

    blockers = [
        item
        for item in final.barriers
        if (
            "DOWN_PAYMENT"
            in item.code
        )
    ]

    print()
    print("--- FINANCIAL BLOCKERS ---")

    for item in blockers:
        print(
            "-",
            item.code,
            "|",
            item.message,
        )

    assert (
        "DOWN_PAYMENT_EVIDENCE_INCOMPLETE"
        in final.blocker_codes
    )

    blocker = next(
        item
        for item in blockers
        if item.code
        == "DOWN_PAYMENT_EVIDENCE_INCOMPLETE"
    )

    assert (
        "REVIEWED_NOT_PUBLISHED"
        in blocker.message
    )

    assert (
        "EXACT_OFFER, QUOTE_FLOW"
        in blocker.message
    )

    assert (
        "OBSERVED (0.0%)"
        in blocker.message
        or "OBSERVED (0%)"
        in blocker.message
    )

    assert (
        "does not mean 0% down payment"
        in blocker.message
    )

    assert (
        final.price_comparison_allowed
        is False
    )

    assert (
        final.price_winner
        is None
    )

    print()
    print(
        "TEST PASSED - ARVAL EXACT OFFER + "
        "PROVIDER-OWNED QUOTE FLOW ARE BOTH REVIEWED; "
        "ABSENCE REMAINS UNKNOWN, WHILE AYVENS "
        "EXPLICIT 0% EVIDENCE REMAINS OBSERVED."
    )


if __name__ == "__main__":
    main()
