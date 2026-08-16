from market_intelligence.comparable_offer_groups import (
    ComparableOfferGroupService,
)


def main():

    print("=" * 100)
    print("COMPARABLE OFFER GROUPS V1")
    print("=" * 100)

    groups = (
        ComparableOfferGroupService()
        .build()
    )

    assert groups, (
        "No cross-provider comparable groups found."
    )

    print()
    print(
        f"Cross-provider groups: {len(groups)}"
    )
    print()

    for group in groups:

        print("-" * 100)

        print(
            f"{group.brand} "
            f"{group.model} "
            f"[{group.fuel_type}]"
        )

        print(
            "Status:",
            group.match_status,
        )

        print(
            "Providers:",
            ", ".join(group.providers),
        )

        print(
            "Contract exact:",
            group.contract_exact,
        )

        print(
            "Durations:",
            group.duration_values,
        )

        print(
            "Mileages:",
            group.mileage_values,
        )

        print(
            "Diagnostic:",
            group.diagnostic,
        )

        print()

        for member in group.members:

            print(
                f"  {member.provider:8} | "
                f"{member.brand} "
                f"{member.model} | "
                f"{member.trim or '-':35} | "
                f"{member.duration} hó | "
                f"{member.mileage} km | "
                f"{member.monthly_fee} Ft"
            )

    # ========================================================
    # KNOWN LIVE-MARKET ASSERTIONS
    # ========================================================

    by_key = {
        group.group_key: group
        for group in groups
    }

    # --------------------------------------------------------
    # BYD ATTO 2 PHEV
    # --------------------------------------------------------

    atto2 = by_key.get(
        "BYD::ATTO 2::PHEV"
    )

    assert atto2 is not None, (
        "BYD ATTO 2 PHEV cross-provider group missing."
    )

    assert set(
        atto2.providers
    ) == {
        "Arval",
        "Ayvens",
    }

    assert 60 in atto2.duration_values
    assert 48 in atto2.duration_values

    assert (
        atto2.contract_exact
        is False
    )

    # --------------------------------------------------------
    # BYD ATTO 3
    #
    # Arval currently exposes PHEV while Ayvens exposes EV.
    # Fuel type is part of the canonical key, therefore they
    # must NOT be promoted into one cross-provider group.
    # --------------------------------------------------------

    assert (
        "BYD::ATTO 3::PHEV"
        not in by_key
    ), (
        "Arval ATTO 3 PHEV was incorrectly promoted to a "
        "cross-provider group."
    )

    assert (
        "BYD::ATTO 3::EV"
        not in by_key
    ), (
        "Ayvens ATTO 3 EV was incorrectly promoted to a "
        "cross-provider group."
    )

    # --------------------------------------------------------
    # BYD SEAL U PHEV
    # --------------------------------------------------------

    seal_u = by_key.get(
        "BYD::SEAL U::PHEV"
    )

    assert seal_u is not None, (
        "BYD SEAL U PHEV cross-provider group missing."
    )

    assert set(
        seal_u.providers
    ) == {
        "Arval",
        "Ayvens",
    }

    # --------------------------------------------------------
    # BYD SEALION 7 EV
    # --------------------------------------------------------

    sealion7 = by_key.get(
        "BYD::SEALION 7::EV"
    )

    assert sealion7 is not None, (
        "BYD SEALION 7 EV cross-provider group missing."
    )

    assert set(
        sealion7.providers
    ) == {
        "Arval",
        "Ayvens",
    }

    # --------------------------------------------------------
    # OPEL COMBO DIESEL
    # --------------------------------------------------------

    combo = by_key.get(
        "OPEL::COMBO::DIESEL"
    )

    assert combo is not None, (
        "OPEL COMBO DIESEL cross-provider group missing."
    )

    assert set(
        combo.providers
    ) == {
        "Arval",
        "Ayvens",
    }

    # Multiple Arval offers are valid members of the same
    # canonical market family.
    arval_combo = [
        member
        for member in combo.members
        if member.provider == "Arval"
    ]

    assert len(arval_combo) >= 2, (
        "Expected multiple Arval Opel Combo offers."
    )

    # --------------------------------------------------------
    # VOLVO XC40
    #
    # Arval: PETROL
    # Ayvens: MHEV
    #
    # They must remain separate.
    # --------------------------------------------------------

    assert (
        "VOLVO::XC40::PETROL"
        not in by_key
    ), (
        "Volvo XC40 PETROL incorrectly became a "
        "cross-provider group."
    )

    assert (
        "VOLVO::XC40::MHEV"
        not in by_key
    ), (
        "Volvo XC40 MHEV incorrectly became a "
        "cross-provider group."
    )

    print()
    print("=" * 100)

    print(
        "TEST PASSED - MARKET OFFERS ARE GROUPED "
        "CONSERVATIVELY BY CANONICAL BRAND + MODEL + "
        "FUEL WITHOUT FUZZY MATCHING OR FALSE PRICE "
        "COMPARABILITY."
    )


if __name__ == "__main__":
    main()
