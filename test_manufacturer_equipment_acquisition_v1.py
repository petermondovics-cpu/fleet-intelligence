from dataclasses import dataclass

from comparison.manufacturer_equipment_acquisition import (
    ManufacturerEquipmentAcquisition,
)


@dataclass
class Offer:
    brand: str
    model: str
    trim: str
    fuel_type: str


def identity(brand, model, trim, fuel):
    model = (
        model.upper()
        .replace(" DM-I", "")
        .replace(" DM-i", "")
    )
    return {
        "brand": brand.upper(),
        "model": model,
        "fuel_type": fuel.upper(),
        "trim": trim.upper(),
    }


def exact_discovery(task, offer):
    return {
        "source_type": "MANUFACTURER_BROCHURE_OR_PDF",
        "source_url": "https://manufacturer.example/spec.pdf",
        "source_text": "ATTO 2 DM-i Boost specification",
        "brand": "BYD",
        "model": "ATTO 2",
        "trim": "Boost",
        "fuel_type": "PHEV",
        "variant_match_status": "EXACT",
        "equipment": (
            "Adaptive cruise control",
            "360 degree camera",
        ),
    }


def main():
    offer = Offer(
        "BYD",
        "ATTO 2",
        "Boost",
        "PHEV",
    )

    engine = ManufacturerEquipmentAcquisition(
        canonical_identity_builder=identity,
        manufacturer_discovery=exact_discovery,
    )

    r = engine.acquire(
        None,
        offer,
        "NOT_PUBLISHED",
    )

    assert r.status == "VALIDATED"
    assert r.provider_equipment_status == "NOT_PUBLISHED"
    assert r.manufacturer_equipment_status == "VALIDATED"
    assert len(r.equipment) == 2

    print(
        "TEST 1 PASSED - MANUFACTURER EVIDENCE VALIDATED "
        "WITHOUT OVERWRITING PROVIDER STATUS"
    )

    r = engine.acquire(
        None,
        offer,
        "PUBLISHED",
    )

    assert r.status == "NOT_REQUIRED"

    print(
        "TEST 2 PASSED - PUBLISHED PROVIDER EQUIPMENT WINS"
    )

    def wrong_variant(task, offer):
        x = exact_discovery(task, offer)
        x["trim"] = "Active"
        x["variant_match_status"] = "UNPROVEN"
        return x

    engine = ManufacturerEquipmentAcquisition(
        canonical_identity_builder=identity,
        manufacturer_discovery=wrong_variant,
    )

    r = engine.acquire(
        None,
        offer,
        "NOT_PUBLISHED",
    )

    assert r.status == "UNRESOLVED"

    print(
        "TEST 3 PASSED - UNPROVEN TRIM IS REJECTED"
    )

    def wrong_year(task, offer):
        x = exact_discovery(task, offer)
        x["different_model_year"] = True
        return x

    engine = ManufacturerEquipmentAcquisition(
        canonical_identity_builder=identity,
        manufacturer_discovery=wrong_year,
    )

    r = engine.acquire(
        None,
        offer,
        "NOT_PUBLISHED",
    )

    assert r.status == "UNRESOLVED"

    print(
        "TEST 4 PASSED - DIFFERENT MODEL YEAR IS REJECTED"
    )

    print(
        "\nALL MANUFACTURER EQUIPMENT ACQUISITION V1 TESTS PASSED"
    )


if __name__ == "__main__":
    main()
