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
from comparison.evidence_gap_resolver import (
    EvidenceGapResolver,
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
    print("LIVE EVIDENCE GAP RESOLVER V1")
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

        comparison = (
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

        plan = (
            EvidenceGapResolver()
            .resolve(comparison)
        )

        print(
            "\nComparison status:",
            comparison.status,
        )

        print(
            "Price comparison allowed:",
            comparison.price_comparison_allowed,
        )

        print(
            "\nEvidence acquisition plan:"
        )

        for index, action in enumerate(
            plan.by_priority(),
            start=1,
        ):
            print(
                f"{index:02d}. "
                f"P{action.priority} | "
                f"{action.target_dimension} | "
                f"{action.action_type}"
            )
            print(
                "    blocker:",
                action.blocker_code,
            )
            print(
                "    action:",
                action.message,
            )

        action_types = {
            action.action_type
            for action in plan.actions
        }

        assert (
            "COLLECT_OBSERVED_PRICED_CONTRACT_VARIANT"
            in action_types
        )

        assert (
            "FIND_EXPLICIT_DOWN_PAYMENT_CONDITION"
            in action_types
        )

        assert (
            "FIND_PROVIDER_SERVICE_DOCUMENTATION"
            in action_types
        )

        assert (
            "FIND_EQUIPMENT_SPECIFICATION_SOURCE"
            in action_types
        )

        print(
            "\nTEST PASSED - "
            "LIVE BLOCKERS CONVERTED TO ACTIONABLE "
            "EVIDENCE ACQUISITION PLAN"
        )

        browser.close()


if __name__ == "__main__":
    main()
