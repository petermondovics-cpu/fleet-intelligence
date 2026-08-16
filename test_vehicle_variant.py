from datetime import datetime

from models.offer import Offer

from matching.vehicle_variant import (
    VehicleVariantMatcher,
)


def create_offer(
    provider,
    model,
    trim,
    fuel_type,
):

    return Offer(

        provider=provider,

        brand="OPEL",

        model=model,

        trim=trim,

        fuel_type=fuel_type,

        monthly_fee=100000,

        duration=48,

        mileage=20000,

        url="",

        scraped_at=datetime.now(),

        raw_title=(
            f"OPEL {model} {trim}"
        ),
    )


def main():

    matcher = (
        VehicleVariantMatcher()
    )

    # ------------------------------------------------
    # TEST 1
    # COMBO 100 HP
    # ------------------------------------------------

    offer = create_offer(
        "Arval",
        "COMBO",
        "1.5 DÍZEL "
        "(75 KW/100 LE)",
        "DIESEL",
    )

    result = matcher.extract(
        offer
    )

    assert (
        result.variant_key
        == "DIESEL|100HP"
    )

    assert (
        result.power_kw
        == 75
    )

    assert (
        result.power_hp
        == 100
    )

    assert (
        result.variant_confidence
        == 100
    )

    assert (
        result.variant_match_type
        == "EXACT_VARIANT"
    )

    print(
        "TEST 1 PASSED - "
        "COMBO 100 HP"
    )

    # ------------------------------------------------
    # TEST 2
    # COMBO 130 HP
    # ------------------------------------------------

    offer = create_offer(
        "Arval",
        "COMBO",
        "1.5 DÍZEL "
        "(96 KW/130 LE)",
        "DIESEL",
    )

    result = matcher.extract(
        offer
    )

    assert (
        result.variant_key
        == "DIESEL|130HP"
    )

    assert (
        result.power_kw
        == 96
    )

    assert (
        result.power_hp
        == 130
    )

    print(
        "TEST 2 PASSED - "
        "COMBO 130 HP"
    )

    # ------------------------------------------------
    # TEST 3
    # 100 HP != 130 HP
    # ------------------------------------------------

    offer_a = create_offer(
        "Arval",
        "COMBO",
        "1.5 DÍZEL "
        "(75 KW/100 LE)",
        "DIESEL",
    )

    offer_b = create_offer(
        "Arval",
        "COMBO",
        "1.5 DÍZEL "
        "(96 KW/130 LE)",
        "DIESEL",
    )

    result = matcher.match(
        offer_a,
        offer_b,
    )

    assert (
        result.variant_match_type
        == "VARIANT_POWER_MISMATCH"
    )

    assert (
        result.variant_confidence
        == 0
    )

    print(
        "TEST 3 PASSED - "
        "100 HP != 130 HP"
    )

    # ------------------------------------------------
    # TEST 4
    # SAME VARIANT
    # ------------------------------------------------

    offer_a = create_offer(
        "Arval",
        "COMBO",
        "1.5 DÍZEL "
        "(75 KW/100 LE)",
        "DIESEL",
    )

    offer_b = create_offer(
        "Ayvens",
        "COMBO",
        "1.5 DÍZEL "
        "(75 KW/100 LE)",
        "DIESEL",
    )

    result = matcher.match(
        offer_a,
        offer_b,
    )

    assert (
        result.variant_match_type
        == "EXACT_VARIANT"
    )

    assert (
        result.variant_confidence
        == 100
    )

    assert (
        result.variant_key
        == "DIESEL|100HP"
    )

    print(
        "TEST 4 PASSED - "
        "SAME VARIANT"
    )

    # ------------------------------------------------
    # TEST 5
    # EV != PHEV
    # ------------------------------------------------

    offer_a = Offer(

        provider="Arval",

        brand="BYD",

        model="ATTO 3",

        trim="EXCELLENCE 75KWH AWD",

        fuel_type="PHEV",

        monthly_fee=100000,

        duration=48,

        mileage=20000,

        url="",

        scraped_at=datetime.now(),

        raw_title=(
            "BYD ATTO 3 "
            "EXCELLENCE 75KWH AWD"
        ),
    )

    offer_b = Offer(

        provider="Ayvens",

        brand="BYD",

        model="ATTO 3",

        trim="",

        fuel_type="EV",

        monthly_fee=100000,

        duration=48,

        mileage=20000,

        url="",

        scraped_at=datetime.now(),

        raw_title=(
            "BYD ATTO 3"
        ),
    )

    result = matcher.match(
        offer_a,
        offer_b,
    )

    assert (
        result.variant_match_type
        == "VARIANT_POWERTRAIN_MISMATCH"
    )

    assert (
        result.variant_confidence
        == 0
    )

    print(
        "TEST 5 PASSED - "
        "EV != PHEV"
    )

    # ------------------------------------------------
    # TEST 6
    # NO VARIANT INFORMATION
    # ------------------------------------------------

    offer = create_offer(
        "Ayvens",
        "COMBO",
        "",
        "",
    )

    result = matcher.extract(
        offer
    )

    assert (
        result.variant_key
        == "UNKNOWN"
    )

    assert (
        result.variant_confidence
        == 0
    )

    assert (
        result.variant_match_type
        == "NO_VARIANT_INFORMATION"
    )

    print(
        "TEST 6 PASSED - "
        "NO VARIANT INFORMATION"
    )

    # ------------------------------------------------
    # FINAL
    # ------------------------------------------------

    print(
        "\nALL VEHICLE VARIANT V1 "
        "TESTS PASSED"
    )


if __name__ == "__main__":
    main()