from playwright.sync_api import sync_playwright

from comparison.full_comparison_orchestrator import (
    FullComparisonOrchestrator,
)
from comparison.provider_acquisition_router import (
    ProviderAcquisitionRouter,
)
from comparison.evidence_acquisition_orchestrator import (
    EvidenceAcquisitionOrchestrator,
)

from scrapers.arval.evidence_aware_builder import (
    ArvalEvidenceAwareBuilder,
)
from scrapers.ayvens.evidence_aware_builder import (
    AyvensEvidenceAwareBuilder,
)
from scrapers.arval.acquisition_connector import (
    ArvalAcquisitionConnector,
)
from scrapers.ayvens.acquisition_connector import (
    AyvensAcquisitionConnector,
)


ARVAL_URL = (
    "https://www.arval.hu/kis-es-kozepvallalkozasok/"
    "tartos-berleti-ajantlat/byd-atto-2-15-phev-boost-at/"
    "byd-atto-2-15-phev-boost-at"
)

AYVENS_URL = (
    "https://autotartosberlet.ayvens.com/"
    "byd/atto-2-dm-i"
)


def dismiss(page):
    for selector in (
        "#onetrust-reject-all-handler",
        "#onetrust-accept-btn-handler",
        "button:has-text('Összes elfogadása')",
        "button:has-text('Elfogadom')",
        "button:has-text('Elutasítom')",
    ):
        loc = page.locator(selector)

        if not loc.count():
            continue

        try:
            loc.first.click(timeout=1800)
            page.wait_for_timeout(300)
            return
        except Exception:
            pass


def load(browser, url, builder):
    page = browser.new_page()

    try:
        page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=60000,
        )
        page.wait_for_timeout(1800)
        dismiss(page)
        return builder.build(page)

    finally:
        page.close()


def key(wrapped):
    return (
        EvidenceAcquisitionOrchestrator()
        ._vehicle_key(wrapped)
    )


def main():
    print("=" * 88)
    print("LIVE AYVENS FINANCIAL DISCOVERY V2")
    print("=" * 88)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False
        )

        arval = load(
            browser,
            ARVAL_URL,
            ArvalEvidenceAwareBuilder(),
        )

        ayvens = load(
            browser,
            AYVENS_URL,
            AyvensEvidenceAwareBuilder(),
        )

        initial = FullComparisonOrchestrator().compare(
            arval,
            ayvens,
            observed_offer_pool=[
                arval.composite.offer,
                ayvens.composite.offer,
            ],
        )

        router = ProviderAcquisitionRouter(
            arval_connector=ArvalAcquisitionConnector(
                browser,
                canonical_key_builder=key,
            ),
            ayvens_connector=AyvensAcquisitionConnector(
                browser,
                canonical_key_builder=key,
            ),
        )

        result = router.execute(
            initial,
            arval,
            ayvens,
        )

        financial = [
            c for c in result.execution.candidates
            if (
                c.target_dimension == "FINANCIAL"
                and c.provider == "Ayvens"
            )
        ]

        assert len(financial) == 1

        c = financial[0]

        print("\nStatus:", c.status)
        print("Source:", c.source_type)
        print("URL:", c.source_url)
        print("Payload:", c.payload)
        print("Diagnostic:", c.diagnostic)

        assert c.status == "VALIDATED"
        assert c.payload.get(
            "down_payment_percent"
        ) == 0.0

        assert c.payload.get(
            "pricing_basis"
        ) == "OBSERVED_ZERO_DOWN_PAYMENT_STATE"

        assert c.payload.get(
            "monthly_fee"
        ) == 223990

        variants = c.payload.get(
            "financial_variants"
        )

        assert variants
        assert any(
            v.get("down_payment_percent") == 20.0
            and v.get("monthly_fee") == 189990
            for v in variants
        )
        assert any(
            v.get("down_payment_percent") == 0.0
            and v.get("monthly_fee") == 223990
            for v in variants
        )

        print(
            "\nTEST PASSED - AYVENS FINANCIAL DISCOVERY RETURNS "
            "AN OBSERVED 0% DOWN-PAYMENT BASELINE AND PRESERVES "
            "THE OBSERVED 20% ALTERNATE STATE."
        )

        browser.close()


if __name__ == "__main__":
    main()
