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
from models.financial_conditions import (
    EVIDENCE_OBSERVED,
    EVIDENCE_UNKNOWN,
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

        if not loc.count():
            continue

        try:
            loc.first.click(timeout=1800)
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


def financial_blocker_codes(result):
    return tuple(
        b.code
        for b in result.barriers
        if (
            b.code.startswith("DOWN_PAYMENT")
            or b.code.startswith("ONE_OFF_FEE")
            or b.code.startswith("RECURRING_FEE")
        )
    )


def main():
    print("=" * 92)
    print("LIVE ACQUIRE → ENRICH → FULL FINANCIAL REASSESS V1")
    print("=" * 92)

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

        initial = FullComparisonOrchestrator().compare(
            arval,
            ayvens,
            observed_offer_pool=[
                arval.composite.offer,
                ayvens.composite.offer,
            ],
        )

        print("\n--- INITIAL FINANCIAL STATE ---")
        print(
            "Arval down payment:",
            arval.composite.financial.down_payment.status,
            arval.composite.financial.down_payment.percent,
        )
        print(
            "Ayvens down payment:",
            ayvens.composite.financial.down_payment.status,
            ayvens.composite.financial.down_payment.percent,
        )
        print(
            "Ayvens raw monthly fee:",
            ayvens.composite.financial.monthly_fee,
        )
        print(
            "Financial status:",
            initial.financial_status,
        )
        print(
            "Financial blockers:",
            financial_blocker_codes(initial),
        )

        assert (
            arval.composite.financial.down_payment.status
            == EVIDENCE_UNKNOWN
        )
        assert (
            ayvens.composite.financial.down_payment.status
            == EVIDENCE_UNKNOWN
        )

        # ----------------------------------------------------
        # 2. ACQUISITION
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

        ayvens_financial_candidates = [
            c
            for c in acquisition.execution.candidates
            if (
                c.target_dimension == "FINANCIAL"
                and c.provider == "Ayvens"
            )
        ]

        assert len(
            ayvens_financial_candidates
        ) == 1

        candidate = (
            ayvens_financial_candidates[0]
        )

        print("\n--- ACQUIRED AYVENS FINANCIAL EVIDENCE ---")
        print("Status:", candidate.status)
        print("Payload:", candidate.payload)

        assert candidate.status == "VALIDATED"
        assert (
            candidate.payload.get(
                "down_payment_percent"
            )
            == 0.0
        )
        assert (
            candidate.payload.get(
                "monthly_fee"
            )
            == 223990
        )
        assert (
            candidate.payload.get(
                "pricing_basis"
            )
            == "OBSERVED_ZERO_DOWN_PAYMENT_STATE"
        )

        # ----------------------------------------------------
        # 3. ENRICHMENT
        # ----------------------------------------------------

        enriched = (
            EvidenceEnrichmentBridge()
            .enrich(
                arval,
                ayvens,
                acquisition,
            )
        )

        print("\n--- ENRICHED FINANCIAL VIEW ---")

        print(
            "Arval:",
            enriched.left_financial.usable_status,
            "| acquisition used:",
            enriched.left_financial.acquisition_used,
            "| DP:",
            enriched.left_financial.financial.down_payment.status,
            enriched.left_financial.financial.down_payment.percent,
            "| fee:",
            enriched.left_financial.financial.monthly_fee,
        )

        print(
            "Ayvens:",
            enriched.right_financial.usable_status,
            "| acquisition used:",
            enriched.right_financial.acquisition_used,
            "| DP:",
            enriched.right_financial.financial.down_payment.status,
            enriched.right_financial.financial.down_payment.percent,
            "| fee:",
            enriched.right_financial.financial.monthly_fee,
            "| basis:",
            enriched.right_financial.pricing_basis,
        )

        assert (
            enriched.left_financial.acquisition_used
            is False
        )
        assert (
            enriched.left_financial.financial.down_payment.status
            == EVIDENCE_UNKNOWN
        )

        assert (
            enriched.right_financial.acquisition_used
            is True
        )
        assert (
            enriched.right_financial.financial.down_payment.status
            == EVIDENCE_OBSERVED
        )
        assert (
            enriched.right_financial.financial.down_payment.percent
            == 0.0
        )
        assert (
            enriched.right_financial.financial.monthly_fee
            == 223990
        )

        # ----------------------------------------------------
        # 4. FULL REASSESSMENT WITH ALL ENRICHED VIEWS
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
            left_financial=(
                enriched.left_financial.financial
            ),
            right_financial=(
                enriched.right_financial.financial
            ),
        )

        print("\n--- FULL FINANCIAL REASSESSMENT ---")
        print(
            "Financial status:",
            rerun.financial_status,
        )
        print(
            "Financial blockers BEFORE:",
            financial_blocker_codes(initial),
        )
        print(
            "Financial blockers AFTER :",
            financial_blocker_codes(rerun),
        )
        print(
            "Price comparison allowed:",
            rerun.price_comparison_allowed,
        )
        print(
            "Price winner:",
            rerun.price_winner,
        )

        assert (
            rerun.financial_status
            == "INSUFFICIENT_EVIDENCE"
        )

        assert (
            "DOWN_PAYMENT_EVIDENCE_INCOMPLETE"
            in financial_blocker_codes(rerun)
        )

        assert (
            rerun.price_comparison_allowed
            is False
        )

        assert rerun.price_winner is None

        # ----------------------------------------------------
        # 5. IMMUTABILITY REGRESSION
        # ----------------------------------------------------

        assert (
            ayvens.composite.financial.monthly_fee
            == 189990
        )
        assert (
            ayvens.composite.financial.down_payment.status
            == EVIDENCE_UNKNOWN
        )
        assert (
            ayvens.composite.financial.down_payment.percent
            is None
        )

        print(
            "\nTEST PASSED - AYVENS FINANCIAL PIPELINE IS END-TO-END: "
            "LIVE 0% / 223990 EVIDENCE IS ACQUIRED, ENRICHED, AND USED BY "
            "FULL COMPARISON V4, WHILE ARVAL UNKNOWN EVIDENCE STILL "
            "CORRECTLY BLOCKS PRICE COMPARISON."
        )

        browser.close()


if __name__ == "__main__":
    main()
