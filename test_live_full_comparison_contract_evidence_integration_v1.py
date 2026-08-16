from market_intelligence.market_match_engine import (
    MarketMatchEngine,
)
from market_intelligence.market_pair_full_comparison_bridge import (
    MarketPairFullComparisonBridge,
)

TARGET_GROUP = "BYD::ATTO 2::PHEV"

def main():
    print("=" * 100)
    print("LIVE FULL COMPARISON CONTRACT EVIDENCE INTEGRATION V1")
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
    print("Contract:", final.contract_status)
    print(
        "Contract method:",
        final.contract_normalization_method,
    )
    print(
        "Contract confidence:",
        final.contract_normalization_confidence,
    )
    print(
        "Normalized left:",
        final.normalized_monthly_fee_left,
    )
    print(
        "Normalized right:",
        final.normalized_monthly_fee_right,
    )
    print(
        "Price comparison allowed:",
        final.price_comparison_allowed,
    )
    print(
        "Price winner:",
        final.price_winner,
    )

    print()
    print("--- CONTRACT BLOCKERS ---")

    contract_blockers = [
        item
        for item in final.barriers
        if "CONTRACT" in item.code
    ]

    for item in contract_blockers:
        print("-", item.code, "|", item.message)

    assert final.contract_status in {
        "EVIDENCE_UNRESOLVED",
        "EXACT_COMMON_CONTRACT_OBSERVED",
    }

    if final.contract_status == "EVIDENCE_UNRESOLVED":
        assert "CONTRACT_NORMALIZATION_INCOMPLETE" in final.blocker_codes
        assert final.normalized_monthly_fee_left is None
        assert final.normalized_monthly_fee_right is None
        assert (
            final.contract_normalization_method
            == "EXPLICIT_COMMON_CONTRACT_STATE"
        )

        blocker = next(
            item
            for item in contract_blockers
            if item.code == "CONTRACT_NORMALIZATION_INCOMPLETE"
        )

        assert (
            "No exact priced common contract coordinate"
            in blocker.message
        )
        assert (
            "No interpolation, extrapolation or provider term factor"
            in blocker.message
        )

    else:
        assert "CONTRACT_NORMALIZATION_INCOMPLETE" not in final.blocker_codes
        assert final.normalized_monthly_fee_left is not None
        assert final.normalized_monthly_fee_right is not None
        assert final.contract_normalization_confidence == 100

    if final.price_comparison_allowed is False:
        assert final.price_winner is None

    print()
    print(
        "TEST PASSED - FINAL CONTRACT DIMENSION USES "
        "EXPLICIT COMMON-COORDINATE EVIDENCE AND NEVER "
        "FALLS BACK TO AN ESTIMATED TERM FACTOR."
    )

if __name__ == "__main__":
    main()
