from types import SimpleNamespace

import comparison.financial_evidence_provenance as provenance_module
from comparison.financial_evidence_provenance import (
    FINANCIAL_OBSERVED,
    FINANCIAL_REVIEWED_NOT_PUBLISHED,
    FINANCIAL_UNRESOLVED,
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
    assert observed.surface_timings == ()

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

    timings = []
    result = resolver._measure_surface(
        timings,
        "EXACT_OFFER_ROUTE",
        lambda: "ok",
    )
    assert result == "ok"
    assert timings[0][0] == "EXACT_OFFER_ROUTE"
    assert timings[0][1] >= 0

    failed_timings = []
    try:
        resolver._measure_surface(
            failed_timings,
            "QUOTE_FLOW_NAVIGATION",
            lambda: (_ for _ in ()).throw(RuntimeError("expected")),
        )
    except RuntimeError:
        pass
    else:
        raise AssertionError("Expected timing action to raise.")
    assert failed_timings[0][0] == "QUOTE_FLOW_NAVIGATION"
    assert failed_timings[0][1] >= 0

    class FakePage:
        def __init__(self):
            self.closed = False

        def close(self):
            self.closed = True

    class FakeBrowser:
        def __init__(self):
            self.page = FakePage()

        def new_page(self):
            return self.page

    class UnresolvedRouteResolver:
        def resolve(self, *args, **kwargs):
            return SimpleNamespace(status="UNRESOLVED", resolved_url=None)

    original_route_resolver = provenance_module.ArvalOfferRouteResolver
    fake_browser = FakeBrowser()
    provenance_module.ArvalOfferRouteResolver = UnresolvedRouteResolver
    try:
        unresolved = FinancialEvidenceProvenanceResolverV1_1(
            fake_browser
        ).resolve(
            "Arval",
            "https://www.arval.hu/exact-offer",
            financial("UNKNOWN"),
        )
    finally:
        provenance_module.ArvalOfferRouteResolver = original_route_resolver

    assert unresolved.status == FINANCIAL_UNRESOLVED
    assert unresolved.surface_timings[0][0] == "EXACT_OFFER_ROUTE"
    assert unresolved.surface_timings[0][1] >= 0
    assert fake_browser.page.closed is True

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
