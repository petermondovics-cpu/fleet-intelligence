from dataclasses import replace
from playwright.sync_api import sync_playwright

from scrapers.arval.acquisition_connector import (
    ArvalAcquisitionConnector,
)
from scrapers.arval.evidence_aware_builder import (
    ArvalEvidenceAwareBuilder,
)
from comparison.acquisition_executor import (
    AcquisitionExecutor,
)
from comparison.evidence_acquisition_orchestrator import (
    AcquisitionTask,
)


ARVAL_URL = (
    "https://www.arval.hu/kis-es-kozepvallalkozasok/"
    "tartos-berleti-ajantlat/byd-atto-2-15-phev-boost-at/"
    "byd-atto-2-15-phev-boost-at"
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


def canonical_key(wrapped):
    from models.vehicle_identity_normalizer import (
        VehicleIdentityNormalizer,
    )

    v = wrapped.composite.vehicle

    n = VehicleIdentityNormalizer().normalize(
        v.brand,
        v.model,
        v.trim,
        v.fuel_type,
    )

    return "|".join(
        (n.brand, n.model, n.fuel_type)
    )


def main():

    print("=" * 80)
    print("ARVAL ACQUISITION CONNECTOR LIVE V2")
    print("=" * 80)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False
        )

        page = browser.new_page()

        page.goto(
            ARVAL_URL,
            wait_until="domcontentloaded",
            timeout=60000,
        )
        page.wait_for_timeout(1500)
        dismiss(page)

        current = (
            ArvalEvidenceAwareBuilder()
            .build(page)
        )

        page.close()

        connector = ArvalAcquisitionConnector(
            browser,
            canonical_key_builder=canonical_key,
        )

        executor = AcquisitionExecutor(
            contract_discovery=connector.contract_discovery,
        )

        task = AcquisitionTask(
            provider="Arval",
            action_type="COLLECT_OBSERVED_PRICED_CONTRACT_VARIANT",
            target_dimension="CONTRACT",
            priority=10,
            blocker_code="CONTRACT_NORMALIZATION_INCOMPLETE",
            strategy="LIVE_TEST",
            allowed_sources=(
                "PROVIDER_PRICED_OFFER_PAGE",
                "PROVIDER_PRICED_OFFER_ARCHIVE",
            ),
            prohibited_sources=(
                "UNPRICED_QUOTE_CONTROL",
                "SYNTHETIC_PRICE_FACTOR",
            ),
            canonical_vehicle_key=canonical_key(current),
            message="",
        )

        # V2 adds runtime context attributes without changing the
        # public AcquisitionTask dataclass yet.
        object.__setattr__(
            task,
            "current_duration",
            current.composite.duration,
        )

        object.__setattr__(
            task,
            "current_mileage",
            current.composite.mileage,
        )

        result = executor.execute_task(
            task
        )

        print(
            "\nCurrent contract:",
            current.composite.duration,
            "hó /",
            current.composite.mileage,
            "km",
        )

        print(
            "Discovery status:",
            result.status,
        )

        if result.payload:
            print(
                "Discovered:",
                result.payload.get("duration"),
                "hó /",
                result.payload.get("mileage"),
                "km /",
                result.payload.get("monthly_fee"),
                "Ft",
            )

            assert not (
                result.payload.get("duration")
                == current.composite.duration
                and
                result.payload.get("mileage")
                == current.composite.mileage
            )

        assert result.status in {
            "VALIDATED",
            "UNRESOLVED",
        }

        print(
            "\nTEST PASSED - "
            "ARVAL CONTRACT DISCOVERY NO LONGER RETURNS "
            "THE CURRENT CONTRACT AS GAP-RESOLVING EVIDENCE"
        )

        browser.close()


if __name__ == "__main__":
    main()
