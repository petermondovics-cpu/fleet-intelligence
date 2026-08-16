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
from comparison.variant_equivalence_assessor import (
    VariantEquivalenceAssessor,
    VARIANT_INSUFFICIENT_EVIDENCE,
)
from comparison.evidence_acquisition_orchestrator import (
    EvidenceAcquisitionOrchestrator,
)
from comparison.manufacturer_equipment_acquisition import (
    ManufacturerEquipmentAcquisition,
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


def main():
    print("=" * 88)
    print("LIVE ACQUIRE → ENRICH → REASSESS V1")
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
        # 1. INITIAL COMPARISON
        # ----------------------------------------------------

        initial = (
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

        print("\n--- INITIAL COMPARISON ---")
        print("Status:", initial.status)
        print("Variant:", initial.variant_status)
        print(
            "Price comparison allowed:",
            initial.price_comparison_allowed,
        )

        assert (
            initial.price_comparison_allowed
            is False
        )

        # ----------------------------------------------------
        # 2. ACQUIRE
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

        print("\n--- ACQUISITION ---")
        print(
            "Execution:",
            acquisition.execution.status,
        )
        print(
            "Validated:",
            acquisition.execution.validated_count,
        )

        # ----------------------------------------------------
        # 3. ENRICH
        # ----------------------------------------------------

        enriched = (
            EvidenceEnrichmentBridge()
            .enrich(
                arval,
                ayvens,
                acquisition,
            )
        )

        print("\n--- ENRICHED EQUIPMENT ---")

        print(
            "Arval:",
            enriched.left_equipment.usable_status,
            "| owner:",
            enriched.left_equipment.source_owner,
            "| provider published:",
            enriched.left_equipment.provider_published,
            "| items:",
            len(enriched.left_equipment.items),
        )

        print(
            "Ayvens:",
            enriched.right_equipment.usable_status,
            "| owner:",
            enriched.right_equipment.source_owner,
            "| provider published:",
            enriched.right_equipment.provider_published,
            "| items:",
            len(enriched.right_equipment.items),
        )

        assert (
            enriched.left_equipment.usable_status
            == "MANUFACTURER_VALIDATED"
        )

        assert (
            enriched.left_equipment.provider_published
            is False
        )

        assert (
            len(enriched.left_equipment.items)
            > 0
        )

        assert (
            enriched.right_equipment.usable_status
            == "UNRESOLVED"
        )

        # ----------------------------------------------------
        # 4. REASSESS VARIANT USING ENRICHED VIEW
        # ----------------------------------------------------

        reassessed_variant = (
            VariantEquivalenceAssessor()
            .assess(
                arval,
                ayvens,
                identity_status=initial.vehicle_status,
                left_items=(
                    enriched.left_equipment.items
                ),
                right_items=(
                    enriched.right_equipment.items
                ),
                left_equipment_status=(
                    enriched.left_equipment.usable_status
                ),
                right_equipment_status=(
                    enriched.right_equipment.usable_status
                ),
            )
        )

        print("\n--- VARIANT REASSESSMENT ---")
        print(
            "Status:",
            reassessed_variant.status,
        )
        print(
            "Left equipment:",
            reassessed_variant.left_equipment_status,
        )
        print(
            "Right equipment:",
            reassessed_variant.right_equipment_status,
        )

        for reason in reassessed_variant.reasons:
            print("-", reason)

        assert (
            reassessed_variant.status
            == VARIANT_INSUFFICIENT_EVIDENCE
        )

        assert (
            reassessed_variant.price_comparison_safe
            is False
        )

        # ----------------------------------------------------
        # 5. FULL COMPARISON RE-RUN WITH ENRICHED VARIANT INPUT
        # ----------------------------------------------------

        rerun = (
            FullComparisonOrchestrator()
            .compare(
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
            )
        )

        print("\n--- FULL REASSESSMENT ---")
        print("Status:", rerun.status)
        print("Variant:", rerun.variant_status)
        print(
            "Price comparison allowed:",
            rerun.price_comparison_allowed,
        )
        print("Price winner:", rerun.price_winner)

        print("\nBlockers:")

        for barrier in rerun.barriers:
            print(
                "-",
                barrier.code,
                "|",
                "HARD" if barrier.hard else "EVIDENCE",
                "|",
                barrier.message,
            )

        assert (
            rerun.variant_status
            == VARIANT_INSUFFICIENT_EVIDENCE
        )

        assert (
            rerun.price_comparison_allowed
            is False
        )

        assert rerun.price_winner is None

        # Important provenance regression:
        # enrichment must not mutate original provider evidence.
        assert (
            arval.equipment_evidence.standard_status
            == "NOT_PUBLISHED"
        )

        assert (
            ayvens.equipment_evidence.standard_status
            == "PARSING_UNRESOLVED"
        )

        print(
            "\nTEST PASSED - LIVE ACQUIRE → ENRICH → REASSESS "
            "USES VALIDATED MANUFACTURER EVIDENCE FOR ARVAL, "
            "PRESERVES AYVENS PARSING_UNRESOLVED, AND STILL "
            "REFUSES A FALSE PRICE COMPARISON."
        )

        browser.close()


if __name__ == "__main__":
    main()
