from dataclasses import dataclass
from typing import Optional

from playwright.sync_api import sync_playwright

from api.comparison_presenter import ComparisonPresenterV1
from comparison.evidence_acquisition_orchestrator import (
    EvidenceAcquisitionOrchestrator,
)
from comparison.evidence_enrichment_bridge import (
    EvidenceEnrichmentBridge,
)
from comparison.full_comparison_orchestrator import (
    FullComparisonOrchestrator,
)
from comparison.manufacturer_equipment_acquisition import (
    ManufacturerEquipmentAcquisition,
)
from comparison.provider_acquisition_router import (
    ProviderAcquisitionRouter,
)
from models.vehicle_identity_normalizer import (
    VehicleIdentityNormalizer,
)
from scrapers.arval.acquisition_connector import (
    ArvalAcquisitionConnector,
)
from scrapers.arval.evidence_aware_builder import (
    ArvalEvidenceAwareBuilder,
)
from scrapers.ayvens.acquisition_connector import (
    AyvensAcquisitionConnector,
)
from scrapers.ayvens.evidence_aware_builder import (
    AyvensEvidenceAwareBuilder,
)
from scrapers.manufacturers.byd_equipment_connector import (
    BYDManufacturerEquipmentConnector,
)


DEFAULT_ARVAL_URL = (
    "https://www.arval.hu/kis-es-kozepvallalkozasok/"
    "tartos-berleti-ajantlat/byd-atto-2-15-phev-boost-at/"
    "byd-atto-2-15-phev-boost-at"
)

DEFAULT_AYVENS_URL = (
    "https://autotartosberlet.ayvens.com/"
    "byd/atto-2-dm-i"
)


@dataclass(frozen=True)
class LiveComparisonRun:
    response: object
    initial_result: object
    final_result: object
    acquisition: object
    enrichment: object


class LiveComparisonService:
    """
    Live Comparison Service V1.

    Frontend-facing application service:
    provider pages
      -> evidence-aware scrape
      -> initial comparison
      -> evidence acquisition
      -> enrichment
      -> full reassessment
      -> ComparisonResponseV1

    No domain object is mutated.
    """

    def run(
        self,
        *,
        arval_url: str = DEFAULT_ARVAL_URL,
        ayvens_url: str = DEFAULT_AYVENS_URL,
        headless: bool = False,
    ) -> LiveComparisonRun:

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=headless
            )

            try:
                arval = self._load(
                    browser,
                    arval_url,
                    ArvalEvidenceAwareBuilder(),
                )

                ayvens = self._load(
                    browser,
                    ayvens_url,
                    AyvensEvidenceAwareBuilder(),
                )

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

                manufacturer_connector = (
                    BYDManufacturerEquipmentConnector(
                        browser
                    )
                )

                manufacturer = (
                    ManufacturerEquipmentAcquisition(
                        canonical_identity_builder=(
                            self._canonical_identity
                        ),
                        manufacturer_discovery=(
                            manufacturer_connector.discover
                        ),
                    )
                )

                router = ProviderAcquisitionRouter(
                    arval_connector=(
                        ArvalAcquisitionConnector(
                            browser,
                            canonical_key_builder=(
                                self._canonical_key
                            ),
                        )
                    ),
                    ayvens_connector=(
                        AyvensAcquisitionConnector(
                            browser,
                            canonical_key_builder=(
                                self._canonical_key
                            ),
                        )
                    ),
                    manufacturer_equipment=manufacturer,
                )

                acquisition = router.execute(
                    initial,
                    arval,
                    ayvens,
                )

                enrichment = (
                    EvidenceEnrichmentBridge()
                    .enrich(
                        arval,
                        ayvens,
                        acquisition,
                    )
                )

                final = (
                    FullComparisonOrchestrator()
                    .compare(
                        arval,
                        ayvens,
                        observed_offer_pool=[
                            arval.composite.offer,
                            ayvens.composite.offer,
                        ],
                        left_variant_items=(
                            enrichment
                            .left_equipment
                            .items
                        ),
                        right_variant_items=(
                            enrichment
                            .right_equipment
                            .items
                        ),
                        left_variant_equipment_status=(
                            enrichment
                            .left_equipment
                            .usable_status
                        ),
                        right_variant_equipment_status=(
                            enrichment
                            .right_equipment
                            .usable_status
                        ),
                        left_service_package=(
                            enrichment
                            .left_services
                            .package
                        ),
                        right_service_package=(
                            enrichment
                            .right_services
                            .package
                        ),
                        left_financial=(
                            enrichment
                            .left_financial
                            .financial
                        ),
                        right_financial=(
                            enrichment
                            .right_financial
                            .financial
                        ),
                    )
                )

                response = (
                    ComparisonPresenterV1()
                    .present(
                        final,
                        arval,
                        ayvens,
                        left_financial=(
                            enrichment
                            .left_financial
                            .financial
                        ),
                        right_financial=(
                            enrichment
                            .right_financial
                            .financial
                        ),
                        left_pricing_basis=(
                            enrichment
                            .left_financial
                            .pricing_basis
                        ),
                        right_pricing_basis=(
                            enrichment
                            .right_financial
                            .pricing_basis
                        ),
                    )
                )

                return LiveComparisonRun(
                    response=response,
                    initial_result=initial,
                    final_result=final,
                    acquisition=acquisition,
                    enrichment=enrichment,
                )

            finally:
                browser.close()

    @staticmethod
    def _dismiss(page):
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
                loc.first.click(
                    timeout=1800
                )
                page.wait_for_timeout(300)
                return
            except Exception:
                pass

    @classmethod
    def _load(
        cls,
        browser,
        url,
        builder,
    ):
        page = browser.new_page()

        try:
            page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=60000,
            )
            page.wait_for_timeout(1800)
            cls._dismiss(page)
            return builder.build(page)

        finally:
            page.close()

    @staticmethod
    def _canonical_key(wrapped):
        return (
            EvidenceAcquisitionOrchestrator()
            ._vehicle_key(wrapped)
        )

    @staticmethod
    def _canonical_identity(
        brand,
        model,
        trim,
        fuel,
    ):
        normalized = (
            VehicleIdentityNormalizer()
            .normalize(
                brand,
                model,
                trim,
                fuel,
            )
        )

        return {
            "brand": normalized.brand,
            "model": normalized.model,
            "fuel_type": normalized.fuel_type,
            "trim": (
                (trim or "")
                .upper()
                .strip()
            ),
        }
