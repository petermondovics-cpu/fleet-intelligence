from models.vehicle_specification import (
    EVIDENCE_OBSERVED,
    EVIDENCE_UNKNOWN,
    EquipmentItem,
    VehicleEvidence,
    VehicleSpecification,
)


def observed(
    url="https://example.com/vehicle",
    text="Observed source text",
):
    return VehicleEvidence(
        status=EVIDENCE_OBSERVED,
        source_url=url,
        source_text=text,
    )


def unknown():
    return VehicleEvidence(
        status=EVIDENCE_UNKNOWN,
    )


def main():

    # ========================================================
    # TEST 1
    # OBSERVED VEHICLE IDENTITY
    # ========================================================

    specification = VehicleSpecification(
        brand="BYD",
        model="ATTO 2",
        trim="Boost",
        fuel_type="PHEV",
        brand_evidence=observed(
            text="BYD"
        ),
        model_evidence=observed(
            text="BYD ATTO 2"
        ),
        trim_evidence=observed(
            text="Boost"
        ),
        fuel_evidence=observed(
            text="Plug-in hibrid"
        ),
    )

    assert specification.brand == "BYD"
    assert specification.model == "ATTO 2"
    assert specification.trim == "Boost"
    assert specification.fuel_type == "PHEV"

    print(
        "TEST 1 PASSED - "
        "OBSERVED VEHICLE IDENTITY"
    )

    # ========================================================
    # TEST 2
    # STANDARD EQUIPMENT
    # ========================================================

    standard = EquipmentItem(
        name="LED fényszóró",
        category="LIGHTING",
        included=True,
        standard=True,
        evidence=observed(
            text="LED fényszóró – alapfelszereltség"
        ),
    )

    specification = VehicleSpecification(
        brand="BYD",
        model="ATTO 2",
        trim="Boost",
        fuel_type="PHEV",
        brand_evidence=observed(),
        model_evidence=observed(),
        trim_evidence=observed(),
        fuel_evidence=observed(),
        standard_equipment=[
            standard
        ],
    )

    assert (
        specification.standard_equipment_count
        == 1
    )

    assert (
        specification.all_equipment[0].name
        == "LED fényszóró"
    )

    print(
        "TEST 2 PASSED - "
        "STANDARD EQUIPMENT"
    )

    # ========================================================
    # TEST 3
    # OPTIONAL EQUIPMENT
    # ========================================================

    optional = EquipmentItem(
        name="Panorámatető",
        category="COMFORT",
        included=True,
        standard=False,
        evidence=observed(
            text="Panorámatető – opcionális"
        ),
    )

    specification = VehicleSpecification(
        brand="BYD",
        model="ATTO 2",
        trim="Boost",
        fuel_type="PHEV",
        brand_evidence=observed(),
        model_evidence=observed(),
        trim_evidence=observed(),
        fuel_evidence=observed(),
        optional_equipment=[
            optional
        ],
    )

    assert (
        specification.optional_equipment_count
        == 1
    )

    assert (
        specification.optional_equipment[0].standard
        is False
    )

    print(
        "TEST 3 PASSED - "
        "OPTIONAL EQUIPMENT"
    )

    # ========================================================
    # TEST 4
    # UNKNOWN IS NOT NOT-INCLUDED
    # ========================================================

    unknown_equipment = EquipmentItem(
        name="Ülésfűtés",
        category="COMFORT",
        included=None,
        standard=None,
        evidence=unknown(),
    )

    assert (
        unknown_equipment.included
        is None
    )

    assert (
        unknown_equipment.standard
        is None
    )

    print(
        "TEST 4 PASSED - "
        "UNKNOWN EQUIPMENT PRESERVED"
    )

    # ========================================================
    # TEST 5
    # UNKNOWN VEHICLE FIELD
    # ========================================================

    specification = VehicleSpecification(
        brand="BYD",
        model="ATTO 2",
        trim=None,
        fuel_type="PHEV",
        brand_evidence=observed(),
        model_evidence=observed(),
        trim_evidence=unknown(),
        fuel_evidence=observed(),
    )

    assert specification.trim is None
    assert (
        specification.trim_evidence.status
        == EVIDENCE_UNKNOWN
    )

    print(
        "TEST 5 PASSED - "
        "UNKNOWN VEHICLE FIELD"
    )

    # ========================================================
    # TEST 6
    # UNKNOWN CANNOT ASSERT INCLUSION
    # ========================================================

    try:

        EquipmentItem(
            name="Ismeretlen extra",
            category="OTHER",
            included=True,
            standard=None,
            evidence=unknown(),
        )

    except ValueError:
        pass

    else:
        raise AssertionError(
            "UNKNOWN evidence incorrectly allowed "
            "an inclusion assertion."
        )

    print(
        "TEST 6 PASSED - "
        "UNKNOWN ASSERTION REJECTED"
    )

    # ========================================================
    # TEST 7
    # STANDARD / OPTIONAL CLASSIFICATION IS STRICT
    # ========================================================

    try:

        VehicleSpecification(
            brand="BYD",
            model="ATTO 2",
            trim="Boost",
            fuel_type="PHEV",
            brand_evidence=observed(),
            model_evidence=observed(),
            trim_evidence=observed(),
            fuel_evidence=observed(),
            standard_equipment=[
                optional
            ],
        )

    except ValueError:
        pass

    else:
        raise AssertionError(
            "Optional equipment incorrectly "
            "accepted in standard_equipment."
        )

    print(
        "TEST 7 PASSED - "
        "EQUIPMENT CLASSIFICATION VALIDATED"
    )

    print(
        "\nALL VEHICLE SPECIFICATION V1 "
        "TESTS PASSED"
    )


if __name__ == "__main__":
    main()
