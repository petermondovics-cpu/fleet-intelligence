from types import SimpleNamespace

from comparison.financial_evidence_provenance import (
    FINANCIAL_OBSERVED,
    FINANCIAL_REVIEWED_NOT_PUBLISHED,
    FinancialEvidenceProvenanceResolverV1_1,
)
from models.financial_conditions import (
    EVIDENCE_OBSERVED,
)


def financial(
    status,
    percent=None,
    amount=None,
):
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
    print("FINANCIAL EVIDENCE PROVENANCE V1.1 UNIT TESTS")
    print("=" * 100)

    resolver = (
        FinancialEvidenceProvenanceResolverV1_1(
            browser=None
        )
    )

    observed = resolver.resolve(
        "Ayvens",
        "https://example.test/ayvens",
        financial(
            EVIDENCE_OBSERVED,
            percent=0,
        ),
    )

    assert (
        observed.status
        == FINANCIAL_OBSERVED
    )

    assert (
        observed.down_payment_percent
        == 0
    )

    print(
        "TEST 1 PASSED - EXISTING EXPLICIT 0% "
        "AYVENS EVIDENCE IS PRESERVED."
    )

    target = resolver._quote_target_from_parts_for_test(
        base_url=(
            "https://www.arval.hu/"
            "kis-es-kozepvallalkozasok/"
            "tartos-berleti-ajantlat/x/x"
        ),
        href=(
            "/node/524577/switch?"
            "mileage=21800&duration=19610"
        ),
        text="AJÁNLAT KIVÁLASZTÁSA",
    )

    assert target is not None
    assert (
        target["url"]
        == "https://www.arval.hu/node/524577/switch?"
        "mileage=21800&duration=19610"
    )

    print(
        "TEST 2 PASSED - PROVIDER-OWNED RELATIVE "
        "QUOTE URL IS RESOLVED SAFELY."
    )

    external = resolver._quote_target_from_parts_for_test(
        base_url=(
            "https://www.arval.hu/x"
        ),
        href=(
            "https://evil.example/quote"
        ),
        text="AJÁNLAT KIVÁLASZTÁSA",
    )

    assert external is None

    print(
        "TEST 3 PASSED - NON-ARVAL QUOTE TARGET "
        "IS REJECTED."
    )

    assert (
        resolver._parse(
            "nincs önerő adat"
        )
        is None
    )

    print(
        "TEST 4 PASSED - REVIEWED ABSENCE STILL "
        "DOES NOT BECOME ZERO-DOWN."
    )

    assert (
        FINANCIAL_REVIEWED_NOT_PUBLISHED
        != FINANCIAL_OBSERVED
    )

    print(
        "TEST 5 PASSED - REVIEWED_NOT_PUBLISHED "
        "REMAINS DISTINCT FROM OBSERVED."
    )

    print()
    print(
        "ALL FINANCIAL EVIDENCE PROVENANCE "
        "V1.1 UNIT TESTS PASSED"
    )


if __name__ == "__main__":
    main()
