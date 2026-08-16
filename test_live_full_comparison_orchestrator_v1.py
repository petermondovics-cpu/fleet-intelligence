from playwright.sync_api import sync_playwright

from scrapers.arval.evidence_aware_builder import (
    ArvalEvidenceAwareBuilder,
)
from scrapers.ayvens.evidence_aware_builder import (
    AyvensEvidenceAwareBuilder,
)
from comparison.full_comparison_orchestrator import (
    FullComparisonOrchestrator,
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
        "FULL COMPARISON ORCHESTRATOR LIVE V1"
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

        result = (
            FullComparisonOrchestrator()
            .compare(
                arval,
                ayvens,
                observed_offer_pool=[
                    arval.composite.offer,
                    ayvens.composite.offer,
                ],
            )
        )

        print(
            "\nStatus:",
            result.status,
        )

        print(
            "Price comparison allowed:",
            result.price_comparison_allowed,
        )

        print(
            "Price winner:",
            result.price_winner,
        )

        print(
            "\nComponent status:"
        )
        print(
            "Vehicle:",
            result.vehicle_status,
        )
        print(
            "Services:",
            result.service_status,
        )
        print(
            "Equipment:",
            result.equipment_status,
        )
        print(
            "Contract:",
            result.contract_status,
        )
        print(
            "Financial:",
            result.financial_status,
        )

        print(
            "\nNormalized fees:"
        )
        print(
            "Arval:",
            result.normalized_monthly_fee_left,
        )
        print(
            "Ayvens:",
            result.normalized_monthly_fee_right,
        )

        print(
            "\nBlockers / diagnostics:"
        )

        for barrier in result.barriers:
            print(
                "-",
                barrier.code,
                "| HARD" if barrier.hard else "| EVIDENCE",
                ":",
                barrier.message,
            )

        assert (
            result.price_comparison_allowed
            is False
        )

        assert result.price_winner is None

        codes = set(
            result.blocker_codes
        )

        assert (
            "SERVICE_EVIDENCE_INCOMPLETE"
            in codes
        )

        assert (
            "EQUIPMENT_EVIDENCE_INCOMPLETE"
            in codes
        )

        assert (
            "CONTRACT_NORMALIZATION_INCOMPLETE"
            in codes
        )

        assert (
            "DOWN_PAYMENT_EVIDENCE_INCOMPLETE"
            in codes
        )

        print(
            "\nTEST PASSED - "
            "LIVE ORCHESTRATOR REFUSES FALSE PRICE WINNER "
            "AND REPORTS ALL MAJOR BLOCKERS"
        )

        browser.close()


if __name__ == "__main__":
    main()
