from playwright.sync_api import sync_playwright

from scrapers.arval.acquisition_connector import (
    ArvalAcquisitionConnector,
)
from comparison.acquisition_executor import (
    AcquisitionExecutor,
)
from comparison.evidence_acquisition_orchestrator import (
    AcquisitionTask,
)


def vehicle_key(wrapped):
    from models.vehicle_identity_normalizer import (
        VehicleIdentityNormalizer,
    )

    vehicle = wrapped.composite.vehicle

    normalized = (
        VehicleIdentityNormalizer()
        .normalize(
            vehicle.brand,
            vehicle.model,
            vehicle.trim,
            vehicle.fuel_type,
        )
    )

    return "|".join(
        (
            normalized.brand,
            normalized.model,
            normalized.fuel_type,
        )
    )


def make_task(
    action,
    dimension,
    allowed,
    prohibited=(),
):
    return AcquisitionTask(
        provider="Arval",
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


def main():

    print("=" * 80)
    print("ARVAL ACQUISITION CONNECTOR LIVE V1")
    print("=" * 80)

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
        )

        connector = ArvalAcquisitionConnector(
            browser,
            canonical_key_builder=vehicle_key,
        )

        executor = AcquisitionExecutor(
            contract_discovery=connector.contract_discovery,
            service_discovery=connector.service_discovery,
            financial_discovery=connector.financial_discovery,
        )

        # ----------------------------------------------------
        # SERVICES
        # ----------------------------------------------------

        service_task = make_task(
            "FIND_PROVIDER_SERVICE_DOCUMENTATION",
            "SERVICES",
            (
                "PROVIDER_OFFER_PAGE",
                "PROVIDER_SERVICE_PAGE",
                "PROVIDER_TERMS_OR_PDF",
            ),
        )

        service_result = executor.execute_task(
            service_task
        )

        print(
            "\nSERVICES:",
            service_result.status,
        )

        print(
            service_result.diagnostic
        )

        if service_result.payload:
            print(
                "Assertions:",
                len(
                    service_result.payload.get(
                        "services",
                        [],
                    )
                ),
            )

        assert (
            service_result.status
            == "VALIDATED"
        )

        # ----------------------------------------------------
        # FINANCIAL
        # ----------------------------------------------------

        financial_task = make_task(
            "FIND_EXPLICIT_DOWN_PAYMENT_CONDITION",
            "FINANCIAL",
            (
                "PROVIDER_OFFER_PAGE",
                "PROVIDER_TERMS_OR_PDF",
                "PROVIDER_QUOTE_DOCUMENT",
            ),
            (
                "DEFAULT_20_PERCENT_ASSUMPTION",
            ),
        )

        financial_result = executor.execute_task(
            financial_task
        )

        print(
            "\nFINANCIAL:",
            financial_result.status,
        )

        print(
            financial_result.diagnostic
        )

        # VALIDATED or UNRESOLVED are both acceptable live outcomes.
        # REJECTED would mean the connector produced unsafe evidence.
        assert financial_result.status in {
            "VALIDATED",
            "UNRESOLVED",
        }

        # ----------------------------------------------------
        # CONTRACT
        # ----------------------------------------------------

        contract_task = make_task(
            "COLLECT_OBSERVED_PRICED_CONTRACT_VARIANT",
            "CONTRACT",
            (
                "PROVIDER_PRICED_OFFER_PAGE",
                "PROVIDER_PRICED_OFFER_ARCHIVE",
            ),
            (
                "UNPRICED_QUOTE_CONTROL",
                "SYNTHETIC_PRICE_FACTOR",
            ),
        )

        contract_result = executor.execute_task(
            contract_task
        )

        print(
            "\nCONTRACT:",
            contract_result.status,
        )

        print(
            contract_result.diagnostic
        )

        if contract_result.payload:
            print(
                "Offer:",
                contract_result.payload.get("duration"),
                "hó /",
                contract_result.payload.get("mileage"),
                "km /",
                contract_result.payload.get("monthly_fee"),
                "Ft",
            )

        assert contract_result.status in {
            "VALIDATED",
            "UNRESOLVED",
        }

        print(
            "\nTEST PASSED - "
            "ARVAL CONNECTOR EXECUTED LIVE ACQUISITION "
            "WITHOUT FABRICATING COMMERCIAL EVIDENCE"
        )

        browser.close()


if __name__ == "__main__":
    main()
