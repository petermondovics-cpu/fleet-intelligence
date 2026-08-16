from market_intelligence.market_match_engine import (
    MarketMatchEngine,
)
from market_intelligence.market_pair_full_comparison_bridge import (
    MarketPairFullComparisonBridge,
)


TARGET_GROUP = "BYD::ATTO 2::PHEV"


def main():
    print("=" * 100)
    print("LIVE FULL EQUIPMENT COMPARISON VIEW V5")
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

    payload = result.response.to_dict()

    print()
    print("--- ENRICHMENT ---")

    for side in (
        result.enrichment.left_equipment,
        result.enrichment.right_equipment,
    ):
        print(
            side.provider,
            "|",
            side.usable_status,
            "| owner:",
            side.source_owner,
            "| items:",
            len(side.items),
        )

    print()
    print("--- DIMENSIONS ---")
    print(
        "Variant:",
        payload["dimensions"]["variant"],
    )
    print(
        "Equipment:",
        payload["dimensions"]["equipment"],
    )
    print(
        "Equipment score left:",
        payload["equipment_score_left"],
    )
    print(
        "Equipment score right:",
        payload["equipment_score_right"],
    )

    print()
    print("--- RELEVANT BLOCKERS ---")

    relevant = []

    for blocker in payload["blockers"]:
        if (
            "VARIANT" in blocker["code"]
            or
            "EQUIPMENT" in blocker["code"]
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

    assert (
        payload["dimensions"]["variant"]
        == "VALUE_DIFFERENCE"
    )

    assert (
        payload["dimensions"]["equipment"]
        == "VALUE_DIFFERENCE"
    )

    assert (
        "EQUIPMENT_EVIDENCE_INCOMPLETE"
        not in relevant
    )

    assert (
        "EQUIPMENT_VALUE_DIFFERENCE"
        in relevant
    )

    assert (
        payload["equipment_score_left"]
        is not None
    )

    assert (
        payload["equipment_score_right"]
        is not None
    )

    assert (
        payload["equipment_score_left"]
        != payload["equipment_score_right"]
    )

    assert (
        payload["price_comparison_allowed"]
        is False
    )

    assert payload["price_winner"] is None

    print()
    print(
        "TEST PASSED - FULL EQUIPMENT DIMENSION NOW "
        "USES VALIDATED ENRICHED MANUFACTURER EVIDENCE "
        "AND REPORTS VALUE_DIFFERENCE WITHOUT "
        "FABRICATING A PRICE WINNER."
    )


if __name__ == "__main__":
    main()
