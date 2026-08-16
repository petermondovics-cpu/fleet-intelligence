from dataclasses import dataclass

from comparison.equipment_value_normalizer import (
    EquipmentValueNormalizer,
)


@dataclass
class Item:
    name: str
    included: bool


def main():

    engine = EquipmentValueNormalizer()

    # Existing typed EquipmentItem-like behavior remains intact.
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
        "TEST 1 PASSED - TYPED EQUIPMENT INPUT "
        "BEHAVIOR IS PRESERVED."
    )

    # Validated acquisition strings no longer crash the normalizer.
    strings = engine.score_items(
        (
            "tolatókamera",
            "unmapped manufacturer equipment",
        )
    )

    assert (
        "REAR_CAMERA"
        in strings.matched_items
    )

    assert (
        "unmapped manufacturer equipment"
        in strings.unknown_items
    )

    print(
        "TEST 2 PASSED - VALIDATED STRING EQUIPMENT "
        "IS ACCEPTED WITHOUT VALUING UNKNOWN ITEMS AS ZERO."
    )

    comparison = engine.compare(
        (
            "tolatókamera",
        ),
        (
            "tolatókamera",
            "unknown extra",
        ),
    )

    assert comparison.fully_scored is False

    print(
        "TEST 3 PASSED - UNKNOWN ACQUISITION STRINGS "
        "STILL BLOCK FULL VARIANT SCORING."
    )

    print(
        "\nALL EQUIPMENT VALUE NORMALIZER V2 TESTS PASSED"
    )


if __name__ == "__main__":
    main()
