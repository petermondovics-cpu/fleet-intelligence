from models.financial_conditions import (
    EVIDENCE_OBSERVED,
    FinancialEvidence,
    ServiceItem,
    ServicePackage,
)

from comparison.service_semantic_equivalence import (
    SEMANTIC_DIFFERENCE,
    SEMANTIC_MATCH,
    SEMANTIC_PARTIAL_EQUIVALENCE,
    ServiceSemanticEquivalenceAssessor,
)


def observed(text):
    return FinancialEvidence(
        status=EVIDENCE_OBSERVED,
        source_url="https://example.test",
        source_text=text,
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
        evidence=observed(
            name
        ),
    )


def arval():
    return ServicePackage(
        items=[
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
                "ROADSIDE_ASSISTANCE",
            ),
            service(
                "My Arval",
                "FLEET_PORTAL",
            ),
        ]
    )


def ayvens():
    return ServicePackage(
        items=[
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
                "ROADSIDE_ASSISTANCE",
            ),
            service(
                "MyAyvens online ügyintézési rendszer",
                "FLEET_PORTAL",
            ),
            service(
                "Vonatkozó adók",
                "TAXES",
            ),
            service(
                "Biztosítási csomag",
                "INSURANCE",
            ),
        ]
    )


def main():

    print("=" * 100)
    print("SERVICE SEMANTIC EQUIVALENCE V1")
    print("=" * 100)

    engine = (
        ServiceSemanticEquivalenceAssessor()
    )

    result = engine.assess(
        arval(),
        ayvens(),
    )

    print()
    print(
        "Status:",
        result.status,
    )
    print(
        "Core equivalent:",
        result.core_equivalent,
    )
    print(
        "Shared core:",
        result.shared_core_codes,
    )
    print(
        "Left only:",
        result.left_only_codes,
    )
    print(
        "Right only:",
        result.right_only_codes,
    )
    print(
        "Domains:",
        result.functional_domains,
    )
    print(
        "Diagnostic:",
        result.diagnostic,
    )

    assert (
        result.status
        == SEMANTIC_PARTIAL_EQUIVALENCE
    )

    assert (
        result.core_equivalent
        is True
    )

    assert set(
        result.shared_core_codes
    ) == {
        "MAINTENANCE",
        "TYRES",
        "ROADSIDE_ASSISTANCE",
        "FLEET_PORTAL",
        "INSURANCE",
    }

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

    print()
    print(
        "TEST 1 PASSED - CURRENT ARVAL / AYVENS "
        "PACKAGES HAVE AN EXPLICITLY MATCHING CORE "
        "BUT UNRESOLVED ADDITIONAL SEMANTICS."
    )

    # --------------------------------------------------------
    # Exact full semantic equality
    # --------------------------------------------------------

    same = engine.assess(
        ayvens(),
        ayvens(),
    )

    assert (
        same.status
        == SEMANTIC_MATCH
    )

    assert (
        same.price_comparison_safe
        is True
    )

    print(
        "TEST 2 PASSED - IDENTICAL CANONICAL "
        "SERVICE COVERAGE IS A FULL SEMANTIC MATCH."
    )

    # --------------------------------------------------------
    # Explicit contradiction remains hard difference
    # --------------------------------------------------------

    bad_right = ayvens()

    bad_right.items.append(
        service(
            "Finanszírozás",
            "FINANCING",
            included=False,
        )
    )

    left_with_financing = arval()

    contradiction = (
        engine.assess(
            left_with_financing,
            bad_right,
        )
    )

    assert (
        contradiction.status
        == SEMANTIC_DIFFERENCE
    )

    assert any(
        item.code == "FINANCING"
        for item
        in contradiction.contradictions
    )

    print(
        "TEST 3 PASSED - EXPLICIT TRUE/FALSE "
        "CONTRADICTION REMAINS A HARD SEMANTIC DIFFERENCE."
    )

    print()
    print(
        "ALL SERVICE SEMANTIC EQUIVALENCE "
        "V1 TESTS PASSED"
    )


if __name__ == "__main__":
    main()
