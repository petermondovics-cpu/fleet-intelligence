from playwright.sync_api import sync_playwright

from scrapers.arval.evidence_aware_builder import (
    ArvalEvidenceAwareBuilder,
)
from scrapers.ayvens.evidence_aware_builder import (
    AyvensEvidenceAwareBuilder,
)
from comparison.contract_normalization_bridge import (
    ContractNormalizationBridge,
)


ARVAL_URL = (
    "https://www.arval.hu/kis-es-kozepvallalkozasok/"
    "tartos-berleti-ajantlat/byd-atto-2-15-phev-boost-at/"
    "byd-atto-2-15-phev-boost-at"
)

AYVENS_URL = (
    "https://autotartosberlet.ayvens.com/byd/atto-2-dm-i"
)


def dismiss(page):
    for selector in [
        "#onetrust-reject-all-handler",
        "#onetrust-accept-btn-handler",
        "button:has-text('Összes elfogadása')",
        "button:has-text('Elfogadom')",
        "button:has-text('Elutasítom')",
    ]:
        loc = page.locator(selector)
        if loc.count() == 0:
            continue
        try:
            loc.first.click(timeout=2000)
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


def main():

    print("=" * 80)
    print(
        "LIVE CONTRACT NORMALIZATION BRIDGE V1"
    )
    print("=" * 80)

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

        observed_pool = [
            arval.composite.offer,
            ayvens.composite.offer,
        ]

        result = (
            ContractNormalizationBridge()
            .normalize(
                arval,
                ayvens,
                observed_offer_pool=observed_pool,
                # Current service/equipment evidence does NOT pass,
                # so even a future normalized contract price could not
                # yet produce a valid price winner.
                other_barriers_passed=False,
            )
        )

        n = result.normalization

        print(
            "\nArval:",
            arval.composite.duration,
            "hó /",
            f"{arval.composite.mileage:,} km /",
            f"{arval.composite.monthly_fee:,} Ft",
        )

        print(
            "Ayvens:",
            ayvens.composite.duration,
            "hó /",
            f"{ayvens.composite.mileage:,} km /",
            f"{ayvens.composite.monthly_fee:,} Ft",
        )

        print(
            "\nNormalization status:",
            n.normalization_status,
        )

        print(
            "Method:",
            n.normalization_method,
        )

        print(
            "Normalized price available:",
            n.normalized_price_available,
        )

        print(
            "Term evidence:",
            result.evidence.get(
                "term_evidence"
            ),
        )

        print(
            "Mileage evidence:",
            result.evidence.get(
                "mileage_evidence"
            ),
        )

        print(
            "Final price comparison ready:",
            result.final_price_comparison_ready,
        )

        assert (
            n.normalization_status
            == "NEEDS_TERM_NORMALIZATION"
        )

        assert (
            n.normalized_price_available
            is False
        )

        assert (
            result.evidence.get(
                "term_evidence"
            )
            is None
        )

        assert (
            result.final_price_comparison_ready
            is False
        )

        print(
            "\nTEST PASSED - "
            "LIVE CONTRACT DIFFERENCE IS NOT NORMALIZED "
            "WITHOUT OBSERVED PROVIDER PRICE EVIDENCE"
        )

        print(
            "\nIMPORTANT:"
        )

        print(
            "Ayvens 36-60 month quote-request slider metadata "
            "is not part of observed_offer_pool and therefore "
            "cannot become pricing evidence."
        )

        browser.close()


if __name__ == "__main__":
    main()
