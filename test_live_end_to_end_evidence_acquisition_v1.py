from playwright.sync_api import sync_playwright

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
from comparison.full_comparison_orchestrator import (
    FullComparisonOrchestrator,
)
from comparison.evidence_acquisition_orchestrator import (
    EvidenceAcquisitionOrchestrator,
)
from comparison.provider_acquisition_router import (
    ProviderAcquisitionRouter,
)


ARVAL_URL = (
    "https://www.arval.hu/kis-es-kozepvallalkozasok/"
    "tartos-berleti-ajantlat/"
    "byd-atto-2-15-phev-boost-at/"
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

        if loc.count() == 0:
            continue

        try:
            loc.first.click(timeout=1500)
            page.wait_for_timeout(200)
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
        page.wait_for_timeout(1500)
        dismiss(page)
        return builder.build(page)
    finally:
        page.close()


def canonical_key(wrapped):
    return (
        EvidenceAcquisitionOrchestrator()
        ._vehicle_key(
            wrapped
        )
    )


def main():

    print("=" * 80)
    print(
        "END-TO-END LIVE EVIDENCE ACQUISITION V1"
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

        arval_connector = (
            ArvalAcquisitionConnector(
                browser,
                canonical_key_builder=canonical_key,
            )
        )

        ayvens_connector = (
            AyvensAcquisitionConnector(
                browser,
                canonical_key_builder=canonical_key,
            )
        )

        result = (
            ProviderAcquisitionRouter(
                arval_connector=arval_connector,
                ayvens_connector=ayvens_connector,
            )
            .execute(
                comparison,
                arval,
                ayvens,
            )
        )

        execution = result.execution

        print(
            "\nPlan status:",
            result.plan_status,
        )

        print(
            "Tasks:",
            result.task_count,
        )

        print(
            "Execution status:",
            execution.status,
        )

        print(
            "Validated candidates:",
            execution.validated_count,
        )

        print(
            "\nResults:"
        )

        for item in execution.candidates:
            print(
                "-",
                item.provider,
                "|",
                item.target_dimension,
                "|",
                item.action_type,
                "|",
                item.status,
            )

            if item.source_type:
                print(
                    "  source:",
                    item.source_type,
                )

            print(
                "  diagnostic:",
                item.diagnostic,
            )

        # Expected live safety behavior:
        # service evidence should resolve on both providers.
        services = [
            item
            for item in execution.candidates
            if item.target_dimension == "SERVICES"
        ]

        assert services

        assert any(
            item.provider == "Arval"
            and item.status == "VALIDATED"
            for item in services
        )

        assert any(
            item.provider == "Ayvens"
            and item.status == "VALIDATED"
            for item in services
        )

        # Current live pages have no explicit down payment.
        financial = [
            item
            for item in execution.candidates
            if item.target_dimension == "FINANCIAL"
        ]

        assert financial

        assert all(
            item.status in {
                "VALIDATED",
                "UNRESOLVED",
            }
            for item in financial
        )

        # Contract discovery must never validate Ayvens slider metadata.
        ayvens_contract = [
            item
            for item in execution.candidates
            if (
                item.provider == "Ayvens"
                and
                item.target_dimension == "CONTRACT"
            )
        ]

        assert ayvens_contract

        assert all(
            item.source_type
            != "AYVENS_DURATION_MILEAGE_SLIDER"
            for item in ayvens_contract
        )

        # Equipment remains unresolved in V1 because no equipment
        # discovery callback is configured in the router.
        equipment = [
            item
            for item in execution.candidates
            if item.target_dimension == "EQUIPMENT"
        ]

        assert equipment

        assert all(
            item.status == "UNRESOLVED"
            for item in equipment
        )

        print(
            "\nTEST PASSED - "
            "END-TO-END LIVE ACQUISITION EXECUTED BOTH "
            "PROVIDER CONNECTORS WITHOUT FABRICATING EVIDENCE"
        )

        browser.close()


if __name__ == "__main__":
    main()
