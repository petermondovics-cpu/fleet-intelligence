from market_intelligence.market_match_engine import (
    PAIR_NORMALIZABLE,
    MarketMatchEngine,
)


def main():

    print("=" * 100)
    print("MARKET MATCH ENGINE V1")
    print("=" * 100)

    pairs = (
        MarketMatchEngine()
        .build()
    )

    assert pairs, (
        "No market offer pairs were created."
    )

    print()
    print(
        f"Cross-provider offer pairs: {len(pairs)}"
    )
    print()

    for pair in pairs:

        print("-" * 100)

        print(
            f"{pair.brand} "
            f"{pair.model} "
            f"[{pair.fuel_type}]"
        )

        print(
            f"{pair.left_provider:8} "
            f"{pair.left_duration} hó / "
            f"{pair.left_mileage} km / "
            f"{pair.left_monthly_fee} Ft"
        )

        print(
            f"{pair.right_provider:8} "
            f"{pair.right_duration} hó / "
            f"{pair.right_mileage} km / "
            f"{pair.right_monthly_fee} Ft"
        )

        print(
            "Status:",
            pair.pair_status,
        )

        print(
            "Contract exact:",
            pair.contract_exact,
        )

        print(
            "Full comparison candidate:",
            pair.full_comparison_candidate,
        )

        print(
            "Price comparison allowed:",
            pair.price_comparison_allowed,
        )

        print(
            "Diagnostic:",
            pair.diagnostic,
        )

    # ========================================================
    # LIVE-MARKET ASSERTIONS
    # ========================================================

    atto2 = [
        pair
        for pair in pairs
        if (
            pair.group_key
            == "BYD::ATTO 2::PHEV"
        )
    ]

    assert len(atto2) == 1

    assert (
        atto2[0].pair_status
        == PAIR_NORMALIZABLE
    )

    assert (
        atto2[0].left_duration
        != atto2[0].right_duration
    )

    assert (
        atto2[0].left_mileage
        == atto2[0].right_mileage
        == 20000
    )

    assert (
        atto2[0].full_comparison_candidate
        is True
    )

    assert (
        atto2[0].price_comparison_allowed
        is False
    )

    # Opel Combo contains two Arval offers and one Ayvens offer.
    # Therefore exactly two cross-provider pairs are expected.
    combo = [
        pair
        for pair in pairs
        if (
            pair.group_key
            == "OPEL::COMBO::DIESEL"
        )
    ]

    assert len(combo) == 2

    assert all(
        pair.pair_status
        == PAIR_NORMALIZABLE
        for pair in combo
    )

    # Every pair must be cross-provider and directional duplicates
    # must never exist.
    seen = set()

    for pair in pairs:

        assert (
            pair.left_provider
            != pair.right_provider
        )

        assert (
            pair.price_comparison_allowed
            is False
        )

        reverse = (
            pair.group_key,
            pair.right_offer_id,
            pair.left_offer_id,
        )

        assert reverse not in seen

        seen.add(
            (
                pair.group_key,
                pair.left_offer_id,
                pair.right_offer_id,
            )
        )

    print()
    print("=" * 100)

    print(
        "TEST PASSED - MARKET MATCH ENGINE CREATES "
        "DETERMINISTIC CROSS-PROVIDER OFFER PAIRS, "
        "PROMOTES NORMALIZABLE CONTRACT MISMATCHES TO "
        "FULL-COMPARISON CANDIDATES, AND NEVER FABRICATES "
        "PRICE COMPARABILITY."
    )


if __name__ == "__main__":
    main()
