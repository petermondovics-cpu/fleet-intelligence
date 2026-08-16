"""
LIVE MANUFACTURER EQUIPMENT ACQUISITION V1

This test intentionally does NOT scrape arbitrary third-party equipment.
Wire `discover_exact_byd_equipment` only to an official BYD Hungary /
BYD manufacturer model page, specification page, brochure or PDF.

The first live objective is:
Arval BYD ATTO 2 / 1.5 PHEV BOOST AT
provider equipment status = NOT_PUBLISHED
+
exact manufacturer derivative evidence
=
manufacturer equipment status = VALIDATED

Until an exact official source is configured, the correct result is
UNRESOLVED.
"""

from comparison.manufacturer_equipment_acquisition import (
    ManufacturerEquipmentAcquisition,
)


class Offer:
    brand = "BYD"
    model = "ATTO 2"
    trim = "1.5 PHEV BOOST AT"
    fuel_type = "PHEV"


def canonical_identity(brand, model, trim, fuel):
    # Replace this helper with the project's existing
    # VehicleIdentityNormalizer adapter when wiring live discovery.
    normalized_model = (
        model.upper()
        .replace(" DM-I", "")
        .replace(" DM-i", "")
    )
    return {
        "brand": brand.upper().strip(),
        "model": normalized_model.strip(),
        "trim": trim.upper().strip(),
        "fuel_type": fuel.upper().strip(),
    }


def discover_exact_byd_equipment(task, offer):
    # V1 safety default:
    # no manufacturer URL is guessed or fabricated.
    #
    # The next connector will populate this callback from an official
    # manufacturer page/PDF and must return variant_match_status EXACT
    # or EXPLICITLY_COMPATIBLE.
    return None


def main():
    print("=" * 80)
    print("LIVE MANUFACTURER EQUIPMENT ACQUISITION V1")
    print("=" * 80)

    engine = ManufacturerEquipmentAcquisition(
        canonical_identity_builder=canonical_identity,
        manufacturer_discovery=discover_exact_byd_equipment,
    )

    result = engine.acquire(
        task=None,
        offer=Offer(),
        provider_equipment_status="NOT_PUBLISHED",
    )

    print(
        "\nProvider equipment:",
        result.provider_equipment_status,
    )
    print(
        "Manufacturer equipment:",
        result.manufacturer_equipment_status,
    )
    print("Status:", result.status)
    print("Diagnostic:", result.diagnostic)

    assert result.provider_equipment_status == "NOT_PUBLISHED"
    assert result.status == "UNRESOLVED"

    print(
        "\nTEST PASSED - MANUFACTURER FALLBACK DOES NOT "
        "FABRICATE EQUIPMENT EVIDENCE BEFORE AN EXACT OFFICIAL "
        "DERIVATIVE SOURCE IS CONFIGURED"
    )


if __name__ == "__main__":
    main()
