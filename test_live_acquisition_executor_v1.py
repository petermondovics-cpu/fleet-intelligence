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
from comparison.acquisition_executor import (
    AcquisitionExecutor,
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
    print("LIVE ACQUISITION EXECUTOR V1")
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

        # V1 executor is intentionally callback-driven.
        # This live test proves that without an acquisition connector,
        # tasks remain unresolved rather than fabricating evidence.
        executor = AcquisitionExecutor()

        result = executor.execute_plan(
            plan
        )

        print(
            "\nExecution status:",
            result.status,
        )

        print(
            "Candidates:",
            result.candidate_count,
        )

        print(
            "Validated:",
            result.validated_count,
        )

        for item in result.candidates:
            print(
                "-",
                item.provider,
                "|",
                item.target_dimension,
                "|",
                item.status,
                "|",
                item.diagnostic,
            )

        assert result.candidate_count == plan.task_count
        assert result.validated_count == 0

        assert all(
            item.status == "UNRESOLVED"
            for item in result.candidates
        )

        print(
            "\nTEST PASSED - "
            "EXECUTOR DOES NOT FABRICATE EVIDENCE "
            "WHEN NO ACQUISITION CALLBACK IS CONFIGURED"
        )

        browser.close()


if __name__ == "__main__":
    main()
