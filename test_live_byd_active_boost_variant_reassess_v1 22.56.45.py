from market_intelligence.market_match_engine import (
    MarketMatchEngine,
)
from market_intelligence.market_pair_full_comparison_bridge import (
    MarketPairFullComparisonBridge,
)


TARGET_GROUP = "BYD::ATTO 2::PHEV"


def main():

    print("=" * 100)
    print("LIVE BYD ACTIVE / BOOST MULTI-FEATURE VARIANT REASSESS V1")
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

    assert result.final_comparison is not None
    assert result.response is not None

    payload = result.response.to_dict()

    print()
    print("--- EQUIPMENT ---")

    for side in (
        result.enrichment.left_equipment,
        result.enrichment.right_equipment,
    ):
        print(
            side.provider,
            "|",
            side.usable_status,
            "|",
            side.source_owner,
            "|",
            len(side.items),
            "items",
        )

    print()
    print("--- FINAL DIMENSIONS ---")
    print(
        "Variant:",
        payload["dimensions"]["variant"],
    )
    print(
        "Equipment:",
        payload["dimensions"]["equipment"],
    )

    print()
    print("--- RELEVANT BLOCKERS ---")

    relevant = []

    for blocker in payload["blockers"]:
        if (
            "VARIANT" in blocker["code"]
            or "EQUIPMENT" in blocker["code"]
        ):
            relevant.append(
                blocker["code"]
            )
            print(
                "-",
                blocker["code"],
                "|",
                blocker["message"],
            )

    # After V3 canonicalization, the old "no canonical valuation rule"
    # reason must no longer survive for this exact BYD pair.
    for blocker in payload["blockers"]:
        assert (
            "no canonical valuation rule"
            not in blocker["message"].casefold()
        )

    # Different fully-scored trims must not become a false equivalence
    # merely because both evidence sides are now usable.
    assert (
        payload["dimensions"]["variant"]
        in {
            "VALUE_DIFFERENCE",
            "NOT_COMPARABLE",
        }
    )

    if not payload["price_comparison_allowed"]:
        assert payload["price_winner"] is None

    print()
    print(
        "TEST PASSED - BYD ACTIVE / BOOST EQUIPMENT "
        "IS FULLY CANONICALIZED INTO MULTI-FEATURE "
        "COMPARISON WITHOUT FABRICATING VARIANT "
        "EQUIVALENCE OR A PRICE WINNER."
    )


if __name__ == "__main__":
    main()
