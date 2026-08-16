from comparison.arval_exact_offer_service_evidence_resolver import (
    ArvalExactOfferServiceEvidenceResolver,
)


def main():
    mapping = (
        ArvalExactOfferServiceEvidenceResolver
        .TITLE_TO_CODES
    )

    assert mapping[
        "biztosítás és káresemény-kezelés"
    ] == (
        "INSURANCE",
        "CLAIMS_MANAGEMENT",
    )

    assert mapping["finanszírozás"] == (
        "FINANCING",
    )
    assert mapping["gumiabroncs kezelés"] == (
        "TYRES",
    )
    assert mapping["karbantartás és javítás"] == (
        "MAINTENANCE",
    )
    assert mapping["közúti segítségnyújtás"] == (
        "ROADSIDE_ASSISTANCE",
    )
    assert mapping["my arval"] == (
        "FLEET_PORTAL",
    )

    all_codes = {
        code
        for codes in mapping.values()
        for code in codes
    }

    assert all_codes == {
        "INSURANCE",
        "CLAIMS_MANAGEMENT",
        "FINANCING",
        "TYRES",
        "MAINTENANCE",
        "ROADSIDE_ASSISTANCE",
        "FLEET_PORTAL",
    }

    print(
        "TEST PASSED - ARVAL V2 MAPS ONLY EXPLICIT "
        "STRUCTURED SERVICE TITLES TO CANONICAL CODES."
    )


if __name__ == "__main__":
    main()
