from playwright.sync_api import sync_playwright

from scrapers.ayvens.acquisition_connector import (
    AyvensAcquisitionConnector,
)
from scrapers.ayvens.evidence_aware_builder import (
    AyvensEvidenceAwareBuilder,
)
from comparison.acquisition_executor import AcquisitionExecutor
from comparison.evidence_acquisition_orchestrator import AcquisitionTask


AYVENS_URL = "https://autotartosberlet.ayvens.com/byd/atto-2-dm-i"


def dismiss(page):
    AyvensAcquisitionConnector._dismiss(page)


def canonical_key(wrapped):
    # Reuse the already-correct canonical-key implementation in the
    # acquisition orchestrator instead of duplicating normalizer imports.
    from comparison.evidence_acquisition_orchestrator import (
        EvidenceAcquisitionOrchestrator,
    )
    return EvidenceAcquisitionOrchestrator()._vehicle_key(wrapped)


def task(dimension, action, allowed, prohibited=()):
    t = AcquisitionTask(
        provider="Ayvens",
        action_type=action,
        target_dimension=dimension,
        priority=10,
        blocker_code="LIVE_TEST",
        strategy="LIVE_TEST",
        allowed_sources=tuple(allowed),
        prohibited_sources=tuple(prohibited),
        canonical_vehicle_key="BYD|ATTO 2|PHEV",
        message="",
    )
    return t


def main():
    print("=" * 80)
    print("AYVENS ACQUISITION CONNECTOR LIVE V1")
    print("=" * 80)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        page = browser.new_page()
        page.goto(
            AYVENS_URL,
            wait_until="domcontentloaded",
            timeout=60000,
        )
        page.wait_for_timeout(1500)
        dismiss(page)

        current = AyvensEvidenceAwareBuilder().build(page)
        page.close()

        connector = AyvensAcquisitionConnector(
            browser,
            canonical_key_builder=canonical_key,
        )

        executor = AcquisitionExecutor(
            contract_discovery=connector.contract_discovery,
            service_discovery=connector.service_discovery,
            financial_discovery=connector.financial_discovery,
        )

        service_task = task(
            "SERVICES",
            "FIND_PROVIDER_SERVICE_DOCUMENTATION",
            (
                "PROVIDER_OFFER_PAGE",
                "PROVIDER_SERVICE_PAGE",
                "PROVIDER_TERMS_OR_PDF",
            ),
        )
        object.__setattr__(service_task, "current_url", AYVENS_URL)

        sr = executor.execute_task(service_task)

        print("\nSERVICES:", sr.status)
        if sr.payload:
            print(
                "Assertions:",
                len(sr.payload.get("services", [])),
            )

        assert sr.status == "VALIDATED"

        financial_task = task(
            "FINANCIAL",
            "FIND_EXPLICIT_DOWN_PAYMENT_CONDITION",
            (
                "PROVIDER_OFFER_PAGE",
                "PROVIDER_TERMS_OR_PDF",
                "PROVIDER_QUOTE_DOCUMENT",
            ),
            (
                "DEFAULT_20_PERCENT_ASSUMPTION",
            ),
        )
        object.__setattr__(financial_task, "current_url", AYVENS_URL)

        fr = executor.execute_task(financial_task)

        print("\nFINANCIAL:", fr.status)
        print(fr.diagnostic)

        assert fr.status in {"VALIDATED", "UNRESOLVED"}

        contract_task = task(
            "CONTRACT",
            "COLLECT_OBSERVED_PRICED_CONTRACT_VARIANT",
            (
                "PROVIDER_PRICED_OFFER_PAGE",
                "PROVIDER_PRICED_OFFER_ARCHIVE",
            ),
            (
                "UNPRICED_QUOTE_CONTROL",
                "SYNTHETIC_PRICE_FACTOR",
                "AYVENS_DURATION_MILEAGE_SLIDER",
            ),
        )

        object.__setattr__(
            contract_task,
            "current_duration",
            current.composite.duration,
        )
        object.__setattr__(
            contract_task,
            "current_mileage",
            current.composite.mileage,
        )
        object.__setattr__(
            contract_task,
            "current_url",
            AYVENS_URL,
        )

        cr = executor.execute_task(contract_task)

        print("\nCURRENT CONTRACT:")
        print(
            current.composite.duration,
            "hó /",
            current.composite.mileage,
            "km /",
            current.composite.monthly_fee,
            "Ft",
        )

        print("CONTRACT:", cr.status)
        print(cr.diagnostic)

        if cr.payload:
            print(
                "Discovered:",
                cr.payload.get("duration"),
                "hó /",
                cr.payload.get("mileage"),
                "km /",
                cr.payload.get("monthly_fee"),
                "Ft",
            )

            assert (
                cr.payload.get("pricing_basis")
                == "ADVERTISED_CONTRACT"
            )

            assert not (
                cr.payload.get("duration")
                == current.composite.duration
                and
                cr.payload.get("mileage")
                == current.composite.mileage
            )

        assert cr.status in {"VALIDATED", "UNRESOLVED"}

        print(
            "\nTEST PASSED - AYVENS CONNECTOR EXECUTED LIVE "
            "WITHOUT USING QUOTE SLIDERS AS PRICING EVIDENCE"
        )

        browser.close()


if __name__ == "__main__":
    main()
