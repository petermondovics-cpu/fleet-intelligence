from market_intelligence.market_match_engine import (
    MarketMatchEngine,
)
from market_intelligence.market_pair_full_comparison_bridge import (
    PAIR_EVALUATED,
    MarketPairFullComparisonBridge,
)


TARGET_GROUP = (
    "BYD::ATTO 2::PHEV"
)


def main():

    print("=" * 100)
    print("LIVE MARKET PAIR -> FULL COMPARISON BRIDGE V1")
    print("=" * 100)

    pairs = (
        MarketMatchEngine()
        .build()
    )

    target = next(
        (
            pair
            for pair in pairs
            if (
                pair.group_key
                == TARGET_GROUP
            )
        ),
        None,
    )

    assert target is not None, (
        "BYD ATTO 2 PHEV market pair not found."
    )

    print()
    print("--- MARKET PAIR ---")

    print(
        target.left_provider,
        target.left_duration,
        target.left_mileage,
        target.left_monthly_fee,
    )

    print(
        target.right_provider,
        target.right_duration,
        target.right_mileage,
        target.right_monthly_fee,
    )

    print(
        "Pair status:",
        target.pair_status,
    )

    assert (
        target.price_comparison_allowed
        is False
    )

    result = (
        MarketPairFullComparisonBridge()
        .evaluate(
            target,
            headless=False,
        )
    )

    print()
    print("--- BRIDGE ---")
    print(
        "Bridge status:",
        result.status,
    )
    print(
        "Diagnostic:",
        result.diagnostic,
    )
    print(
        "Stage timings:",
        result.stage_timings,
    )

    assert (
        result.status
        == PAIR_EVALUATED
    )

    assert (
        result.response
        is not None
    )

    timing_names = tuple(
        name
        for name, seconds
        in result.stage_timings
    )
    assert timing_names[:2] == (
        "load_left",
        "load_right",
    )
    assert "acquisition" in timing_names
    assert "contract_evidence" in timing_names

    payload = (
        result.response
        .to_dict()
    )

    print()
    print("--- FULL COMPARISON ---")

    print(
        "Status:",
        payload["status"],
    )

    print(
        "Price comparison allowed:",
        payload[
            "price_comparison_allowed"
        ],
    )

    print(
        "Price winner:",
        payload[
            "price_winner"
        ],
    )

    print(
        "Left:",
        payload[
            "left_offer"
        ]["provider"],
        payload[
            "left_offer"
        ]["price"][
            "advertised_monthly_fee_huf"
        ],
    )

    print(
        "Right:",
        payload[
            "right_offer"
        ]["provider"],
        payload[
            "right_offer"
        ]["price"][
            "advertised_monthly_fee_huf"
        ],
    )

    print(
        "Right DP:",
        payload[
            "right_offer"
        ]["price"][
            "down_payment"
        ]["status"],
        payload[
            "right_offer"
        ]["price"][
            "down_payment"
        ]["percent"],
    )

    print()
    print("--- BLOCKERS ---")

    for blocker in payload[
        "blockers"
    ]:
        print(
            "-",
            blocker["code"],
            "|",
            blocker["message"],
        )

    # Market pairing itself must never become a price decision.
    assert (
        target.price_comparison_allowed
        is False
    )

    # The full evidence-aware engine remains the authority.
    assert (
        payload[
            "price_comparison_allowed"
        ]
        is False
    )

    assert (
        payload[
            "price_winner"
        ]
        is None
    )

    # Current Ayvens exact-offer financial observation must still
    # be promoted through the bridge.
    ayvens_offer = (
        payload["left_offer"]
        if (
            payload["left_offer"][
                "provider"
            ]
            == "Ayvens"
        )
        else payload["right_offer"]
    )

    assert (
        ayvens_offer[
            "price"
        ][
            "down_payment"
        ][
            "status"
        ]
        == "OBSERVED"
    )

    assert (
        ayvens_offer[
            "price"
        ][
            "down_payment"
        ][
            "percent"
        ]
        == 0.0
    )

    assert (
        ayvens_offer[
            "price"
        ][
            "pricing_basis"
        ]
        == "OBSERVED_ZERO_DOWN_PAYMENT_STATE"
    )

    print()
    print("=" * 100)

    print(
        "TEST PASSED - A PERSISTED MARKET PAIR CAN BE "
        "RE-OBSERVED LIVE, ROUTED THROUGH ACQUISITION + "
        "ENRICHMENT + FULL COMPARISON, AND STILL REFUSES "
        "A FALSE PRICE WINNER."
    )


if __name__ == "__main__":
    main()
