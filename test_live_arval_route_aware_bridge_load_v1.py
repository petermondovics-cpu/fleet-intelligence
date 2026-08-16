from market_intelligence.market_match_engine import (
    MarketMatchEngine,
)
from market_intelligence.market_pair_full_comparison_bridge import (
    MarketPairFullComparisonBridge,
)

TARGET_GROUP = "BYD::ATTO 2::PHEV"


def main():
    print("=" * 100)
    print("LIVE ARVAL ROUTE-AWARE BRIDGE LOAD V1")
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

    print("Arval/Ayvens pair:")
    print("left:", pair.left_provider, pair.left_url)
    print("right:", pair.right_provider, pair.right_url)

    result = (
        MarketPairFullComparisonBridge()
        .evaluate(
            pair,
            headless=True,
        )
    )

    print()
    print("bridge status:", result.status)
    print("diagnostic:", result.diagnostic)

    assert result.status == "EVALUATED"
    assert result.response is not None
    assert result.response.to_dict()["api_version"] == "comparison.v2"

    print()
    print(
        "TEST PASSED - BRIDGE RESOLVES ARVAL EXACT-OFFER "
        "ROUTE BEFORE THE EVIDENCE-AWARE BUILDER RUNS."
    )


if __name__ == "__main__":
    main()
