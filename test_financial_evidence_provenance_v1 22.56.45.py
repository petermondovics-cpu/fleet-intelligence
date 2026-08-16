from types import SimpleNamespace

from comparison.financial_evidence_provenance import (
    FINANCIAL_OBSERVED,
    FINANCIAL_REVIEWED_NOT_PUBLISHED,
    FINANCIAL_UNRESOLVED,
    FinancialEvidenceProvenanceResolverV1,
)
from models.financial_conditions import EVIDENCE_OBSERVED, EVIDENCE_UNKNOWN


def financial(status, percent=None, amount=None):
    return SimpleNamespace(
        down_payment=SimpleNamespace(
            status=status,
            percent=percent,
            amount=amount,
            evidence=SimpleNamespace(
                source_url="https://example.test"
            ),
        )
    )


def main():
    print("=" * 100)
    print("FINANCIAL EVIDENCE PROVENANCE RESOLVER V1")
    print("=" * 100)

    resolver = FinancialEvidenceProvenanceResolverV1(browser=None)

    observed = resolver.resolve(
        "Ayvens",
        "https://example.test/ayvens",
        financial(EVIDENCE_OBSERVED, percent=20),
    )
    assert observed.status == FINANCIAL_OBSERVED
    assert observed.down_payment_percent == 20
    print("TEST 1 PASSED - OBSERVED PROVIDER EVIDENCE IS PRESERVED.")

    unresolved = resolver.resolve(
        "Other",
        "https://example.test/other",
        financial(EVIDENCE_UNKNOWN),
    )
    assert unresolved.status == FINANCIAL_UNRESOLVED
    print("TEST 2 PASSED - UNKNOWN NON-ARVAL EVIDENCE IS NOT UPGRADED.")

    assert resolver._parse("Kezdő befizetés 0% önerő") == (0.0, None)
    print("TEST 3 PASSED - EXPLICIT ZERO-DOWN TEXT IS PARSED.")

    assert resolver._parse("Nincs itt pénzügyi feltétel.") is None
    print("TEST 4 PASSED - ABSENCE NEVER BECOMES 0%.")

    assert FINANCIAL_REVIEWED_NOT_PUBLISHED != FINANCIAL_OBSERVED
    print("TEST 5 PASSED - REVIEWED_NOT_PUBLISHED IS DISTINCT FROM OBSERVED.")

    print()
    print("ALL FINANCIAL EVIDENCE PROVENANCE V1 TESTS PASSED")


if __name__ == "__main__":
    main()
