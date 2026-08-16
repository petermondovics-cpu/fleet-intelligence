from market_intelligence.market_match_engine import (
    MarketMatchEngine,
)
from market_intelligence.market_pair_full_comparison_bridge import (
    MarketPairFullComparisonBridge,
)


TARGET_GROUP = "BYD::ATTO 2::PHEV"


def main():
    print("=" * 100)
    print("LIVE AYVENS ACTIVE EQUIPMENT -> FULL VARIANT REASSESS V1")
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

    assert result.enrichment is not None
    assert result.response is not None

    print()
    print("--- EQUIPMENT ENRICHMENT ---")

    for side in (
        result.enrichment.left_equipment,
        result.enrichment.right_equipment,
    ):
        print()
        print(
            side.provider,
            "|",
            side.usable_status,
            "| owner:",
            side.source_owner,
            "| acquired:",
            side.acquisition_used,
            "| items:",
            len(side.items),
        )

        for item in side.items:
            print("  -", item)

    payload = result.response.to_dict()

    print()
    print("--- VARIANT / EQUIPMENT STATUS ---")
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

    for blocker in payload["blockers"]:
        if (
            "VARIANT" in blocker["code"]
            or "EQUIPMENT" in blocker["code"]
        ):
            print(
                "-",
                blocker["code"],
                "|",
                blocker["message"],
            )

    ayvens = (
        result.enrichment.left_equipment
        if (
            result.enrichment
            .left_equipment
            .provider
            == "Ayvens"
        )
        else result.enrichment.right_equipment
    )

    assert (
        ayvens.usable_status
        == "MANUFACTURER_VALIDATED"
    )
    assert ayvens.acquisition_used is True
    assert len(ayvens.items) > 0

    if not payload["price_comparison_allowed"]:
        assert payload["price_winner"] is None

    print()
    print(
        "TEST PASSED - AYVENS ACTIVE MANUFACTURER "
        "EQUIPMENT FLOWS THROUGH ACQUISITION AND "
        "ENRICHMENT INTO VARIANT REASSESSMENT WITHOUT "
        "FABRICATING PRICE COMPARABILITY."
    )


if __name__ == "__main__":
    main()
