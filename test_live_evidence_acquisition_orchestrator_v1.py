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
from comparison.evidence_acquisition_orchestrator import (
    EvidenceAcquisitionOrchestrator,
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
    print("LIVE EVIDENCE ACQUISITION ORCHESTRATOR V1")
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
            EvidenceAcquisitionOrchestrator()
            .plan(
                comparison,
                arval,
                ayvens,
            )
        )

        print("\nPlan status:", plan.status)
        print("Task count:", plan.task_count)

        for i, task in enumerate(
            plan.by_priority(),
            start=1,
        ):
            print(
                f"\n{i:02d}. P{task.priority} | "
                f"{task.provider} | "
                f"{task.target_dimension}"
            )
            print("    action:", task.action_type)
            print("    strategy:", task.strategy)
            print(
                "    vehicle:",
                task.canonical_vehicle_key,
            )
            print(
                "    allowed:",
                ", ".join(task.allowed_sources),
            )
            print(
                "    prohibited:",
                ", ".join(task.prohibited_sources),
            )

        assert plan.task_count > 0

        ayvens_contract = [
            task
            for task in plan.tasks
            if (
                task.provider == "Ayvens"
                and task.target_dimension == "CONTRACT"
            )
        ]

        assert ayvens_contract

        assert (
            "AYVENS_DURATION_MILEAGE_SLIDER"
            in ayvens_contract[0].prohibited_sources
        )

        financial = [
            task
            for task in plan.tasks
            if task.target_dimension == "FINANCIAL"
        ]

        assert financial

        assert all(
            "DEFAULT_20_PERCENT_ASSUMPTION"
            in task.prohibited_sources
            for task in financial
        )

        print(
            "\nTEST PASSED - "
            "LIVE EVIDENCE GAPS EXPANDED TO SAFE "
            "PROVIDER-SPECIFIC ACQUISITION TASKS"
        )

        browser.close()


if __name__ == "__main__":
    main()
