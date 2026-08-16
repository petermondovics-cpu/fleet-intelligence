from models.vehicle_specification import (
    EVIDENCE_OBSERVED,
    EquipmentItem,
    VehicleEvidence,
)
from comparison.equipment_value_normalizer import (
    EquipmentValueNormalizer,
)


def ve(text):
    return VehicleEvidence(
        status=EVIDENCE_OBSERVED,
        source_url="https://example.com",
        source_text=text,
    )


def eq(name):
    return EquipmentItem(
        name=name,
        category="OTHER",
        included=True,
        standard=False,
        evidence=ve(name),
    )


def main():

    normalizer = (
        EquipmentValueNormalizer()
    )

    # ========================================================
    # TEST 1 - KNOWN EQUIPMENT SCORED
    # ========================================================

    result = normalizer.score_items(
        [
            eq("Fűthető kormánykerék"),
            eq("180 fokos tolatókamera"),
        ]
    )

    assert result.known_score == 5
    assert result.fully_scored is True

    print(
        "TEST 1 PASSED - "
        "KNOWN EQUIPMENT SCORED"
    )

    # ========================================================
    # TEST 2 - ALIASES COLLAPSE
    # ========================================================

    result = normalizer.score_items(
        [
            eq("Adaptív tempomat"),
            eq(
                "Adaptív sebességtartó "
                "Stop&Go rendszerrel"
            ),
        ]
    )

    assert result.known_score == 5

    print(
        "TEST 2 PASSED - "
        "ALIASES COLLAPSE TO ONE CANONICAL ITEM"
    )

    # ========================================================
    # TEST 3 - UNKNOWN IS NOT ZERO
    # ========================================================

    result = normalizer.score_items(
        [
            eq("Panoráma hangulatfény csomag"),
        ]
    )

    assert result.known_score == 0
    assert result.fully_scored is False
    assert (
        result.unknown_items
        == (
            "Panoráma hangulatfény csomag",
        )
    )

    print(
        "TEST 3 PASSED - "
        "UNKNOWN EQUIPMENT PRESERVED"
    )

    # ========================================================
    # TEST 4 - RELATIVE COMPARISON
    # ========================================================

    result = normalizer.compare(
        [
            eq("Fűthető kormánykerék"),
        ],
        [
            eq("Fűthető kormánykerék"),
            eq("180 fokos tolatókamera"),
        ],
    )

    assert result.score_delta == 3

    print(
        "TEST 4 PASSED - "
        "RELATIVE EQUIPMENT SCORE DELTA"
    )

    # ========================================================
    # TEST 5 - SCORE IS NOT MONEY
    # ========================================================

    assert not hasattr(
        result,
        "monthly_fee_adjustment"
    )

    assert not hasattr(
        result,
        "huf_value"
    )

    print(
        "TEST 5 PASSED - "
        "EQUIPMENT SCORE KEPT SEPARATE FROM PRICE"
    )

    print(
        "\nALL EQUIPMENT VALUE "
        "NORMALIZATION V1 TESTS PASSED"
    )


if __name__ == "__main__":
    main()
