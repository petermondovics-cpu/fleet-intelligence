from models.financial_conditions import (
    EVIDENCE_OBSERVED,
    EVIDENCE_UNKNOWN,
    FinancialEvidence,
    ServiceItem,
    ServicePackage,
)
from comparison.service_package_normalizer import (
    ServicePackageNormalizer,
)
from comparison.service_package_comparison import (
    SERVICE_DIFFERENCE,
    SERVICE_INSUFFICIENT_EVIDENCE,
    SERVICE_MATCH,
    ServicePackageComparisonEngine,
)


def observed(text):
    return FinancialEvidence(
        status=EVIDENCE_OBSERVED,
        source_url="https://example.com",
        source_text=text,
    )


def unknown():
    return FinancialEvidence(
        status=EVIDENCE_UNKNOWN
    )


def service(
    name,
    category,
    included=True,
):
    return ServiceItem(
        name=name,
        category=category,
        included=included,
        evidence=(
            observed(name)
            if included is not None
            else unknown()
        ),
    )


def pkg(items):
    return ServicePackage(
        items=items
    )


def main():

    normalizer = (
        ServicePackageNormalizer()
    )

    engine = (
        ServicePackageComparisonEngine()
    )

    # ========================================================
    # TEST 1 - AYVENS NORMALIZATION
    # ========================================================

    ayvens = pkg(
        [
            service(
                "Teljes körű karbantartás",
                "MAINTENANCE",
            ),
            service(
                "Téli-, nyári gumiabroncs",
                "TYRES",
            ),
            service(
                "Assistance szolgáltatás",
                "MOBILITY",
            ),
            service(
                "MyAyvens online ügyintézési rendszer",
                "ADMINISTRATION",
            ),
            service(
                "Vonatkozó adók",
                "TAX",
            ),
            service(
                "Biztosítási csomag",
                "INSURANCE",
            ),
        ]
    )

    result = normalizer.normalize(
        ayvens
    )

    assert set(
        result.by_code()
    ) == {
        "MAINTENANCE",
        "TYRES",
        "ROADSIDE_ASSISTANCE",
        "FLEET_PORTAL",
        "TAXES",
        "INSURANCE",
    }

    print(
        "TEST 1 PASSED - "
        "AYVENS SERVICES NORMALIZED"
    )

    # ========================================================
    # TEST 2 - ARVAL NORMALIZATION
    # ========================================================

    arval = pkg(
        [
            service(
                "Biztosítás és káresemény-kezelés",
                "INSURANCE",
            ),
            service(
                "Finanszírozás",
                "FINANCING",
            ),
            service(
                "Gumiabroncs kezelés",
                "TYRES",
            ),
            service(
                "Karbantartás és javítás",
                "MAINTENANCE",
            ),
            service(
                "Közúti segítségnyújtás",
                "MOBILITY",
            ),
            service(
                "My Arval",
                "ADMINISTRATION",
            ),
        ]
    )

    result = normalizer.normalize(
        arval
    )

    assert set(
        result.by_code()
    ) == {
        "INSURANCE",
        "CLAIMS_MANAGEMENT",
        "FINANCING",
        "TYRES",
        "MAINTENANCE",
        "ROADSIDE_ASSISTANCE",
        "FLEET_PORTAL",
    }

    print(
        "TEST 2 PASSED - "
        "ARVAL SERVICES NORMALIZED"
    )

    # ========================================================
    # TEST 3 - SHARED CORE + DIFFERENT PUBLISHED COVERAGE
    # ========================================================

    result = engine.compare(
        arval,
        ayvens,
    )

    assert (
        result.status
        == SERVICE_INSUFFICIENT_EVIDENCE
    )

    assert set(
        result.left_only_codes
    ) == {
        "CLAIMS_MANAGEMENT",
        "FINANCING",
    }

    assert set(
        result.right_only_codes
    ) == {
        "TAXES",
    }

    print(
        "TEST 3 PASSED - "
        "PROVIDER COVERAGE DIFFERENCE IS "
        "INSUFFICIENT_EVIDENCE"
    )

    # ========================================================
    # TEST 4 - EXPLICIT CONTRADICTION
    # ========================================================

    left = pkg(
        [
            service(
                "Casco",
                "INSURANCE",
                True,
            )
        ]
    )

    right = pkg(
        [
            service(
                "Casco",
                "INSURANCE",
                False,
            )
        ]
    )

    result = engine.compare(
        left,
        right,
    )

    assert (
        result.status
        == SERVICE_DIFFERENCE
    )

    assert (
        result.differences[0].code
        == "INSURANCE"
    )

    print(
        "TEST 4 PASSED - "
        "EXPLICIT SERVICE CONTRADICTION DETECTED"
    )

    # ========================================================
    # TEST 5 - UNKNOWN DOES NOT BECOME FALSE
    # ========================================================

    left = pkg(
        [
            service(
                "Üzemanyagkártya",
                "FUEL",
                None,
            )
        ]
    )

    right = pkg(
        [
            service(
                "Üzemanyagkártya",
                "FUEL",
                True,
            )
        ]
    )

    result = engine.compare(
        left,
        right,
    )

    assert (
        result.status
        == SERVICE_INSUFFICIENT_EVIDENCE
    )

    print(
        "TEST 5 PASSED - "
        "UNKNOWN SERVICE NOT TREATED AS EXCLUDED"
    )

    # ========================================================
    # TEST 6 - UNKNOWN WORDING PRESERVED
    # ========================================================

    result = normalizer.normalize(
        pkg(
            [
                service(
                    "Prémium mobilitási plusz",
                    "OTHER",
                    True,
                )
            ]
        )
    )

    assert (
        result.unknown_items
        == (
            "Prémium mobilitási plusz",
        )
    )

    print(
        "TEST 6 PASSED - "
        "UNKNOWN SERVICE WORDING PRESERVED"
    )

    # ========================================================
    # TEST 7 - IDENTICAL CANONICAL SERVICES MATCH
    # ========================================================

    left = pkg(
        [
            service(
                "Assistance szolgáltatás",
                "MOBILITY",
                True,
            )
        ]
    )

    right = pkg(
        [
            service(
                "Közúti segítségnyújtás",
                "MOBILITY",
                True,
            )
        ]
    )

    result = engine.compare(
        left,
        right,
    )

    assert (
        result.status
        == SERVICE_MATCH
    )

    print(
        "TEST 7 PASSED - "
        "PROVIDER ALIASES MATCH CANONICALLY"
    )

    print(
        "\nALL SERVICE PACKAGE "
        "NORMALIZATION V1 TESTS PASSED"
    )


if __name__ == "__main__":
    main()
