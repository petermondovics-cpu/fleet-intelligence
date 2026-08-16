from playwright.sync_api import sync_playwright

from comparison.full_comparison_orchestrator import (
    FullComparisonOrchestrator,
)
from comparison.provider_acquisition_router import (
    ProviderAcquisitionRouter,
)
from comparison.evidence_enrichment_bridge import (
    EvidenceEnrichmentBridge,
)
from comparison.evidence_acquisition_orchestrator import (
    EvidenceAcquisitionOrchestrator,
)
from comparison.manufacturer_equipment_acquisition import (
    ManufacturerEquipmentAcquisition,
)
from comparison.service_package_comparison import (
    ServicePackageComparisonEngine,
)

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
from scrapers.manufacturers.byd_equipment_connector import (
    BYDManufacturerEquipmentConnector,
)

from models.vehicle_identity_normalizer import (
    VehicleIdentityNormalizer,
)


ARVAL_URL = (
    "https://www.arval.hu/kis-es-kozepvallalkozasok/"
    "tartos-berleti-ajantlat/byd-atto-2-15-phev-boost-at/"
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
        page.wait_for_timeout(2000)
        dismiss(page)
        return builder.build(page)

    finally:
        page.close()


def canonical_key(wrapped):
    return (
        EvidenceAcquisitionOrchestrator()
        ._vehicle_key(wrapped)
    )


def canonical_identity(brand, model, trim, fuel):
    n = VehicleIdentityNormalizer().normalize(
        brand,
        model,
        trim,
        fuel,
    )

    return {
        "brand": n.brand,
        "model": n.model,
        "fuel_type": n.fuel_type,
        "trim": (trim or "").upper().strip(),
    }


def service_blocker_codes(result):
    return tuple(
        b.code
        for b in result.barriers
        if b.code.startswith("SERVICE_")
    )


def main():
    print("=" * 88)
    print("LIVE SERVICE ENRICH → REASSESS V1")
    print("=" * 88)

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

        # ----------------------------------------------------
        # INITIAL
        # ----------------------------------------------------

        initial = FullComparisonOrchestrator().compare(
            arval,
            ayvens,
            observed_offer_pool=[
                arval.composite.offer,
                ayvens.composite.offer,
            ],
        )

        initial_codes = service_blocker_codes(
            initial
        )

        print("\n--- INITIAL SERVICE STATE ---")
        print("Service status:", initial.service_status)
        print("Service blockers:", initial_codes)

        # ----------------------------------------------------
        # ACQUIRE
        # ----------------------------------------------------

        manufacturer_connector = (
            BYDManufacturerEquipmentConnector(
                browser
            )
        )

        manufacturer = (
            ManufacturerEquipmentAcquisition(
                canonical_identity_builder=canonical_identity,
                manufacturer_discovery=(
                    manufacturer_connector.discover
                ),
            )
        )

        router = ProviderAcquisitionRouter(
            arval_connector=ArvalAcquisitionConnector(
                browser,
                canonical_key_builder=canonical_key,
            ),
            ayvens_connector=AyvensAcquisitionConnector(
                browser,
                canonical_key_builder=canonical_key,
            ),
            manufacturer_equipment=manufacturer,
        )

        acquisition = router.execute(
            initial,
            arval,
            ayvens,
        )

        # ----------------------------------------------------
        # ENRICH
        # ----------------------------------------------------

        enriched = EvidenceEnrichmentBridge().enrich(
            arval,
            ayvens,
            acquisition,
        )

        print("\n--- ENRICHED SERVICE STATE ---")

        print(
            "Arval:",
            enriched.left_services.usable_status,
            "| acquisition used:",
            enriched.left_services.acquisition_used,
            "| acquired codes:",
            enriched.left_services.acquired_codes,
        )

        print(
            "Ayvens:",
            enriched.right_services.usable_status,
            "| acquisition used:",
            enriched.right_services.acquisition_used,
            "| acquired codes:",
            enriched.right_services.acquired_codes,
        )

        # Current scope policy:
        # Arval generic docs are NOT promoted.
        assert (
            enriched.left_services.acquisition_used
            is False
        )

        # Ayvens exact-offer services ARE promoted.
        assert (
            enriched.right_services.acquisition_used
            is True
        )

        assert set(
            enriched.right_services.acquired_codes
        ) >= {
            "MAINTENANCE",
            "TYRES",
            "ROADSIDE_ASSISTANCE",
            "FLEET_PORTAL",
            "TAXES",
            "INSURANCE",
        }

        # ----------------------------------------------------
        # DIRECT SERVICE REASSESSMENT
        # ----------------------------------------------------

        direct = ServicePackageComparisonEngine().compare(
            enriched.left_services.package,
            enriched.right_services.package,
        )

        print("\n--- DIRECT SERVICE REASSESSMENT ---")
        print("Status:", direct.status)
        print("Left only:", direct.left_only_codes)
        print("Right only:", direct.right_only_codes)
        print("Left unknown:", direct.left_unknown)
        print("Right unknown:", direct.right_unknown)

        # ----------------------------------------------------
        # FULL REASSESSMENT
        # ----------------------------------------------------

        rerun = FullComparisonOrchestrator().compare(
            arval,
            ayvens,
            observed_offer_pool=[
                arval.composite.offer,
                ayvens.composite.offer,
            ],
            left_variant_items=(
                enriched.left_equipment.items
            ),
            right_variant_items=(
                enriched.right_equipment.items
            ),
            left_variant_equipment_status=(
                enriched.left_equipment.usable_status
            ),
            right_variant_equipment_status=(
                enriched.right_equipment.usable_status
            ),
            left_service_package=(
                enriched.left_services.package
            ),
            right_service_package=(
                enriched.right_services.package
            ),
        )

        rerun_codes = service_blocker_codes(
            rerun
        )

        print("\n--- FULL SERVICE REASSESSMENT ---")
        print("Service status:", rerun.service_status)
        print("Service blockers BEFORE:", initial_codes)
        print("Service blockers AFTER :", rerun_codes)

        print("\nAll remaining blockers:")
        for barrier in rerun.barriers:
            print(
                "-",
                barrier.code,
                "|",
                "HARD" if barrier.hard else "EVIDENCE",
                "|",
                barrier.message,
            )

        # Safety expectation: Ayvens can enrich, but Arval generic service
        # docs cannot prove exact-offer inclusion, so service may remain
        # INSUFFICIENT_EVIDENCE. The test does not require false closure.
        assert (
            rerun.price_comparison_allowed
            is False
        )

        assert rerun.price_winner is None

        # Original service packages must remain unchanged.
        assert (
            arval.composite.services
            is not enriched.left_services.package
        )

        assert (
            ayvens.composite.services
            is not enriched.right_services.package
        )

        print(
            "\nTEST PASSED - AYVENS EXACT-OFFER SERVICE EVIDENCE "
            "IS PROMOTED, ARVAL GENERIC DOCUMENTATION IS NOT, "
            "AND THE FULL COMPARISON REASSESSES SERVICES WITHOUT "
            "FABRICATING OFFER-LEVEL INCLUSION."
        )

        browser.close()


if __name__ == "__main__":
    main()
