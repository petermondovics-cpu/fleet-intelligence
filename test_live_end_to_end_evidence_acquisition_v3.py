from playwright.sync_api import sync_playwright

from scrapers.arval.evidence_aware_builder import ArvalEvidenceAwareBuilder
from scrapers.ayvens.evidence_aware_builder import AyvensEvidenceAwareBuilder
from scrapers.arval.acquisition_connector import ArvalAcquisitionConnector
from scrapers.ayvens.acquisition_connector import AyvensAcquisitionConnector
from scrapers.manufacturers.byd_equipment_connector import (
    BYDManufacturerEquipmentConnector,
)
from comparison.manufacturer_equipment_acquisition import (
    ManufacturerEquipmentAcquisition,
)
from comparison.full_comparison_orchestrator import FullComparisonOrchestrator
from comparison.evidence_acquisition_orchestrator import (
    EvidenceAcquisitionOrchestrator,
)
from comparison.provider_acquisition_router import ProviderAcquisitionRouter
from models.vehicle_identity_normalizer import VehicleIdentityNormalizer


ARVAL_URL = (
    "https://www.arval.hu/kis-es-kozepvallalkozasok/"
    "tartos-berleti-ajantlat/byd-atto-2-15-phev-boost-at/"
    "byd-atto-2-15-phev-boost-at"
)
AYVENS_URL = "https://autotartosberlet.ayvens.com/byd/atto-2-dm-i"


def dismiss(page):
    for selector in (
        "#onetrust-reject-all-handler",
        "#onetrust-accept-btn-handler",
        "button:has-text('Összes elfogadása')",
        "button:has-text('Elfogadom')",
        "button:has-text('Elutasítom')",
    ):
        loc = page.locator(selector)
        if loc.count():
            try:
                loc.first.click(timeout=1500)
                return
            except Exception:
                pass


def load(browser, url, builder):
    page = browser.new_page()
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(1500)
        dismiss(page)
        return builder.build(page)
    finally:
        page.close()


def canonical_key(wrapped):
    return EvidenceAcquisitionOrchestrator()._vehicle_key(wrapped)


def canonical_identity(brand, model, trim, fuel):
    n = VehicleIdentityNormalizer().normalize(
        brand, model, trim, fuel
    )
    return {
        "brand": n.brand,
        "model": n.model,
        "fuel_type": n.fuel_type,
        "trim": (trim or "").upper().strip(),
    }


def main():
    print("=" * 80)
    print("END-TO-END LIVE EVIDENCE ACQUISITION V3 + MANUFACTURER EQUIPMENT")
    print("=" * 80)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        arval = load(browser, ARVAL_URL, ArvalEvidenceAwareBuilder())
        ayvens = load(browser, AYVENS_URL, AyvensEvidenceAwareBuilder())

        comparison = FullComparisonOrchestrator().compare(
            arval,
            ayvens,
            observed_offer_pool=[
                arval.composite.offer,
                ayvens.composite.offer,
            ],
        )

        manufacturer_connector = BYDManufacturerEquipmentConnector(browser)

        manufacturer = ManufacturerEquipmentAcquisition(
            canonical_identity_builder=canonical_identity,
            manufacturer_discovery=manufacturer_connector.discover,
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

        result = router.execute(
            comparison,
            arval,
            ayvens,
        )

        execution = result.execution

        print("\nPlan:", result.plan_status)
        print("Tasks:", result.task_count)
        print("Execution:", execution.status)
        print("Validated:", execution.validated_count)

        print("\nResults:")

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
                print("  source:", item.source_type)

            if item.payload:
                owner = item.payload.get("evidence_owner")
                provider_status = item.payload.get(
                    "provider_equipment_status"
                )
                manufacturer_status = item.payload.get(
                    "manufacturer_equipment_status"
                )
                equipment = item.payload.get("equipment")

                if owner:
                    print("  owner:", owner)
                if provider_status:
                    print("  provider equipment:", provider_status)
                if manufacturer_status:
                    print("  manufacturer equipment:", manufacturer_status)
                if equipment:
                    print("  equipment count:", len(equipment))

            print("  diagnostic:", item.diagnostic)

        arval_equipment = [
            x for x in execution.candidates
            if (
                x.provider == "Arval"
                and x.target_dimension == "EQUIPMENT"
            )
        ]

        assert arval_equipment

        assert any(
            x.status == "VALIDATED"
            and x.source_type in {
                "MANUFACTURER_MODEL_PAGE",
                "MANUFACTURER_SPECIFICATION",
                "MANUFACTURER_BROCHURE_OR_PDF",
            }
            and x.payload.get("evidence_owner") == "MANUFACTURER"
            and x.payload.get("provider_equipment_status") == "NOT_PUBLISHED"
            and x.payload.get("manufacturer_equipment_status") == "VALIDATED"
            for x in arval_equipment
        )

        ayvens_equipment = [
            x for x in execution.candidates
            if (
                x.provider == "Ayvens"
                and x.target_dimension == "EQUIPMENT"
            )
        ]

        assert ayvens_equipment

        assert all(
            x.status == "UNRESOLVED"
            for x in ayvens_equipment
        )

        print(
            "\nTEST PASSED - END-TO-END PIPELINE NOW ACQUIRES "
            "OFFICIAL MANUFACTURER EQUIPMENT FOR ARVAL WITHOUT "
            "RECLASSIFYING IT AS ARVAL-PUBLISHED EVIDENCE"
        )

        browser.close()


if __name__ == "__main__":
    main()
