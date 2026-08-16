from dataclasses import dataclass

from comparison.equipment_value_normalizer import (
    EquipmentValueNormalizer,
)


ACTIVE = (
    "Premium Active Black Cloth interior",
    "Reversing Camera with Rear Parking Sensors",
    "Automatic LED headlights & Rain-Sensing Front Wipers",
    "12.8” Infotainment Touchscreen & 8.8” Driver’s Display",
    "Google Automotive Services (GAS) built-in",
    "Android Auto & Apple Carplay as Standard",
)


BOOST = (
    *ACTIVE,
    "High-quality vegan leather interior",
    "Panoramic roof with electric sunshade",
    "360◦ Camera with Front & Rear Parking Sensors",
    "Heated Front Seats & Heated Steering Wheel",
    "Smartphone Wireless Charging",
    "Aluminium Roof Rail & Rear Privacy Glass",
)


@dataclass
class Item:
    name: str
    included: bool


def main():

    engine = EquipmentValueNormalizer()

    print("=" * 92)
    print("EQUIPMENT VALUE NORMALIZER V3")
    print("=" * 92)

    # --------------------------------------------------------
    # 1. Existing typed evidence still works
    # --------------------------------------------------------

    typed = engine.score_items(
        (
            Item(
                "tolatókamera",
                True,
            ),
            Item(
                "metálfényezés",
                False,
            ),
        )
    )

    assert (
        "REAR_CAMERA"
        in typed.matched_items
    )

    assert (
        "METALLIC_PAINT"
        not in typed.matched_items
    )

    print(
        "TEST 1 PASSED - EXISTING TYPED INPUT "
        "BEHAVIOR IS PRESERVED."
    )

    # --------------------------------------------------------
    # 2. Compound source item expands to multiple features
    # --------------------------------------------------------

    compound = engine.score_items(
        (
            "Heated Front Seats & Heated Steering Wheel",
        )
    )

    assert compound.fully_scored is True
    assert set(
        compound.matched_items
    ) == {
        "HEATED_FRONT_SEATS",
        "HEATED_STEERING_WHEEL",
    }

    print(
        "TEST 2 PASSED - ONE MANUFACTURER SOURCE ITEM "
        "CAN MAP TO MULTIPLE CANONICAL FEATURES."
    )

    # --------------------------------------------------------
    # 3. Unknown wording stays unknown
    # --------------------------------------------------------

    unknown = engine.score_items(
        (
            "Completely New Future Equipment Wording",
        )
    )

    assert unknown.fully_scored is False
    assert unknown.known_score == 0
    assert unknown.unknown_items == (
        "Completely New Future Equipment Wording",
    )

    print(
        "TEST 3 PASSED - UNKNOWN WORDING IS NEVER "
        "SILENTLY VALUED AS ZERO."
    )

    # --------------------------------------------------------
    # 4. BYD ACTIVE fully scores
    # --------------------------------------------------------

    active = engine.score_items(
        ACTIVE
    )

    print()
    print("ACTIVE SCORE:", active.known_score)
    print("ACTIVE FEATURES:")
    for item in active.matched_items:
        print("-", item)

    assert active.fully_scored is True
    assert active.unknown_items == ()

    print(
        "TEST 4 PASSED - BYD ACTIVE IS FULLY CANONICALIZED."
    )

    # --------------------------------------------------------
    # 5. BYD BOOST fully scores and is higher
    # --------------------------------------------------------

    boost = engine.score_items(
        BOOST
    )

    print()
    print("BOOST SCORE:", boost.known_score)
    print("BOOST FEATURES:")
    for item in boost.matched_items:
        print("-", item)

    assert boost.fully_scored is True
    assert boost.unknown_items == ()
    assert (
        boost.known_score
        > active.known_score
    )

    print(
        "TEST 5 PASSED - BYD BOOST IS FULLY "
        "CANONICALIZED AND SCORES ABOVE ACTIVE."
    )

    # --------------------------------------------------------
    # 6. Direction of comparison is explicit
    # --------------------------------------------------------

    comparison = engine.compare(
        BOOST,
        ACTIVE,
    )

    print()
    print(
        "ACTIVE - BOOST score delta:",
        comparison.score_delta,
    )

    assert comparison.fully_scored is True
    assert comparison.score_delta < 0

    print(
        "TEST 6 PASSED - BOOST VS ACTIVE PRODUCES "
        "A FULLY-SCORED VALUE DIFFERENCE."
    )

    print()
    print(
        "ALL EQUIPMENT VALUE NORMALIZER V3 TESTS PASSED"
    )


if __name__ == "__main__":
    main()
