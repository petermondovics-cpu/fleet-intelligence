from types import SimpleNamespace

from playwright.sync_api import sync_playwright

from comparison.evidence_acquisition_orchestrator import (
    EvidenceAcquisitionOrchestrator,
)
from scrapers.arval.acquisition_connector_integrated import (
    ArvalServiceIntegratedAcquisitionConnector,
)


ARVAL_URL = (
    "https://www.arval.hu/kis-es-kozepvallalkozasok/"
    "tartos-berleti-ajantlat/byd-atto-2-15-phev-boost-at/"
    "byd-atto-2-15-phev-boost-at"
)


EXPECTED = {
    "INSURANCE",
    "CLAIMS_MANAGEMENT",
    "FINANCING",
    "TYRES",
    "MAINTENANCE",
    "ROADSIDE_ASSISTANCE",
    "FLEET_PORTAL",
}


def canonical_key(wrapped):
    return (
        EvidenceAcquisitionOrchestrator()
        ._vehicle_key(wrapped)
    )


def main():
    print("=" * 100)
    print("ARVAL SERVICE ACQUISITION INTEGRATION LIVE V1")
    print("=" * 100)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False
        )

        try:
            connector = (
                ArvalServiceIntegratedAcquisitionConnector(
                    browser,
                    canonical_key_builder=canonical_key,
                )
            )

            task = SimpleNamespace(
                current_url=ARVAL_URL,
            )

            payload = connector.service_discovery(
                task
            )

            assert payload is not None

            print()
            print(
                "Source type:",
                payload.get("source_type"),
            )
            print(
                "Scope:",
                payload.get(
                    "applicability_scope"
                ),
            )
            print(
                "Method:",
                payload.get(
                    "evidence_method"
                ),
            )

            services = (
                payload.get("services")
                or ()
            )

            codes = {
                item.get("code")
                for item in services
            }

            print(
                "Codes:",
                tuple(sorted(codes)),
            )

            assert (
                payload.get(
                    "applicability_scope"
                )
                == "EXACT_OFFER"
            )

            assert (
                payload.get(
                    "source_type"
                )
                == "PROVIDER_OFFER_PAGE_DOM"
            )

            assert codes == EXPECTED

            assert all(
                item.get("included")
                is True
                for item in services
            )

            print()
            print(
                "TEST PASSED - ARVAL EXACT-OFFER SERVICE "
                "RESOLVER IS INTEGRATED INTO ACQUISITION "
                "PAYLOAD GENERATION."
            )

        finally:
            browser.close()


if __name__ == "__main__":
    main()
