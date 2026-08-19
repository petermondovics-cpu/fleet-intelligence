from dataclasses import dataclass
from time import perf_counter
from typing import Optional
from typing import Tuple

from playwright.sync_api import sync_playwright

from api.comparison_presenter_v2 import ComparisonPresenterV2
from comparison.evidence_acquisition_orchestrator import (
    EvidenceAcquisitionOrchestrator,
)
from comparison.evidence_enrichment_bridge import (
    EvidenceEnrichmentBridge,
)
from comparison.full_comparison_orchestrator import (
    FullComparisonOrchestrator,
)
from comparison.comparison_decision_explainer_v1 import (
    ComparisonDecisionExplainerV1,
)
from comparison.financial_evidence_provenance import (
    FinancialEvidenceProvenanceResolverV1_1,
)
from contract_normalization.contract_normalization_evidence_resolver_v3 import (
    ContractNormalizationEvidenceResolverV3,
)
from comparison.manufacturer_equipment_acquisition import (
    ManufacturerEquipmentAcquisition,
)
from comparison.provider_acquisition_router import (
    ProviderAcquisitionRouter,
)
from market_intelligence.market_match_engine import (
    MarketOfferPair,
)
from models.vehicle_identity_normalizer import (
    VehicleIdentityNormalizer,
)
from scrapers.arval.acquisition_connector_integrated import (
    ArvalServiceIntegratedAcquisitionConnector,
)
from scrapers.arval.evidence_aware_builder import (
    ArvalEvidenceAwareBuilder,
)
from scrapers.arval.offer_route_resolver import (
    ROUTE_LIVE,
    ArvalOfferRouteResolver,
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


PAIR_EVALUATED = "EVALUATED"
PAIR_UNSUPPORTED_PROVIDER = "UNSUPPORTED_PROVIDER"
PAIR_LOAD_FAILED = "LOAD_FAILED"


@dataclass(frozen=True)
class MarketPairFullComparisonResult:
    pair_key: str
    status: str
    pair_status: str
    group_key: str
    initial_comparison: Optional[object]
    acquisition: Optional[object]
    enrichment: Optional[object]
    final_comparison: Optional[object]
    response: Optional[object]
    decision: Optional[object] = None
    diagnostic: str = ""
    stage_timings: Tuple[Tuple[str, float], ...] = ()


class MarketPairFullComparisonBridge:
    """
    Market Pair -> Full Comparison Bridge V2.

    V2 adds structured Arval exact-offer service acquisition before the
    existing generic Arval service-discovery fallback.
    """

    SUPPORTED_PROVIDERS = {
        "arval",
        "ayvens",
    }

    def evaluate(
        self,
        pair: MarketOfferPair,
        *,
        headless: bool = False,
    ) -> MarketPairFullComparisonResult:

        if not self._supported_pair(pair):
            return MarketPairFullComparisonResult(
                pair_key=pair.pair_key,
                status=PAIR_UNSUPPORTED_PROVIDER,
                pair_status=pair.pair_status,
                group_key=pair.group_key,
                initial_comparison=None,
                acquisition=None,
                enrichment=None,
                final_comparison=None,
                response=None,
                diagnostic=(
                    "Market Pair Full Comparison V2 supports only "
                    "Arval/Ayvens provider pairs."
                ),
            )

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=headless
            )
            stage_timings = []

            try:
                try:
                    left = self._measure(
                        stage_timings,
                        "load_left",
                        lambda: self._load(
                            browser,
                            pair.left_provider,
                            pair.left_url,
                        ),
                    )
                    right = self._measure(
                        stage_timings,
                        "load_right",
                        lambda: self._load(
                            browser,
                            pair.right_provider,
                            pair.right_url,
                        ),
                    )
                except Exception as exc:
                    return MarketPairFullComparisonResult(
                        pair_key=pair.pair_key,
                        status=PAIR_LOAD_FAILED,
                        pair_status=pair.pair_status,
                        group_key=pair.group_key,
                        initial_comparison=None,
                        acquisition=None,
                        enrichment=None,
                        final_comparison=None,
                        response=None,
                        diagnostic=(
                            f"{type(exc).__name__}: {exc}"
                        ),
                        stage_timings=tuple(
                            stage_timings
                        ),
                    )

                initial = (
                    self._measure(
                        stage_timings,
                        "initial_comparison",
                        lambda: FullComparisonOrchestrator()
                        .compare(
                            left,
                            right,
                            observed_offer_pool=[
                                left.composite.offer,
                                right.composite.offer,
                            ],
                        ),
                    )
                )

                manufacturer = (
                    self._manufacturer_acquisition(
                        browser,
                        pair,
                    )
                )

                router = ProviderAcquisitionRouter(
                    arval_connector=(
                        ArvalServiceIntegratedAcquisitionConnector(
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
                    # Contract normalization is performed immediately below
                    # by the authoritative V3 resolver. Its explicit priced
                    # observations, not legacy acquisition candidates, feed
                    # the final comparison.
                    excluded_dimensions=("CONTRACT",),
                )

                acquisition = self._measure(
                    stage_timings,
                    "acquisition",
                    lambda: router.execute(
                        initial,
                        left,
                        right,
                    ),
                )

                for timing in (
                    acquisition
                    .execution
                    .task_timings
                ):
                    stage_timings.append(
                        (
                            (
                                "acquisition:"
                                f"{timing.provider}:"
                                f"{timing.target_dimension}:"
                                f"{timing.action_type}"
                            ),
                            timing.seconds,
                        )
                    )

                enrichment = (
                    self._measure(
                        stage_timings,
                        "enrichment",
                        lambda: EvidenceEnrichmentBridge()
                        .enrich(
                            left,
                            right,
                            acquisition,
                        ),
                    )
                )

                contract_evidence = (
                    self._measure(
                        stage_timings,
                        "contract_evidence",
                        lambda: ContractNormalizationEvidenceResolverV3(
                            browser
                        )
                        .resolve(
                            left.composite.offer,
                            right.composite.offer,
                        ),
                    )
                )

                for provider, seconds in (
                    contract_evidence
                    .discovery_timings
                ):
                    stage_timings.append(
                        (
                            f"contract_evidence:{provider}",
                            seconds,
                        )
                    )

                financial_reviewer = (
                    FinancialEvidenceProvenanceResolverV1_1(
                        browser
                    )
                )

                left_financial_review = (
                    self._measure(
                        stage_timings,
                        "financial_review_left",
                        lambda: financial_reviewer.resolve(
                            pair.left_provider,
                            pair.left_url,
                            enrichment.left_financial.financial,
                        ),
                    )
                )

                for surface, seconds in (
                    getattr(
                        left_financial_review,
                        "surface_timings",
                        (),
                    )
                ):
                    stage_timings.append(
                        (
                            f"financial_review_left:{surface}",
                            seconds,
                        )
                    )

                right_financial_review = (
                    self._measure(
                        stage_timings,
                        "financial_review_right",
                        lambda: financial_reviewer.resolve(
                            pair.right_provider,
                            pair.right_url,
                            enrichment.right_financial.financial,
                        ),
                    )
                )

                for surface, seconds in (
                    getattr(
                        right_financial_review,
                        "surface_timings",
                        (),
                    )
                ):
                    stage_timings.append(
                        (
                            f"financial_review_right:{surface}",
                            seconds,
                        )
                    )

                final = (
                    self._measure(
                        stage_timings,
                        "final_comparison",
                        lambda: FullComparisonOrchestrator()
                        .compare(
                            left,
                            right,
                            observed_offer_pool=[
                                left.composite.offer,
                                right.composite.offer,
                            ],
                            left_variant_items=(
                                enrichment.left_equipment.items
                            ),
                            right_variant_items=(
                                enrichment.right_equipment.items
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
                                enrichment.left_services.package
                            ),
                            right_service_package=(
                                enrichment.right_services.package
                            ),
                            left_financial=(
                                enrichment.left_financial.financial
                            ),
                            right_financial=(
                                enrichment.right_financial.financial
                            ),
                            contract_evidence=contract_evidence,
                            left_financial_review=(
                                left_financial_review
                            ),
                            right_financial_review=(
                                right_financial_review
                            ),
                        ),
                    )
                )

                decision = (
                    self._measure(
                        stage_timings,
                        "decision",
                        lambda: ComparisonDecisionExplainerV1()
                        .explain(
                            final,
                            left,
                            right,
                        ),
                    )
                )

                response = (
                    self._measure(
                        stage_timings,
                        "presentation",
                        lambda: ComparisonPresenterV2()
                        .present(
                            final,
                            decision,
                            left,
                            right,
                            left_financial=(
                                enrichment.left_financial.financial
                            ),
                            right_financial=(
                                enrichment.right_financial.financial
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
                        ),
                    )
                )

                return MarketPairFullComparisonResult(
                    pair_key=pair.pair_key,
                    status=PAIR_EVALUATED,
                    pair_status=pair.pair_status,
                    group_key=pair.group_key,
                    initial_comparison=initial,
                    acquisition=acquisition,
                    enrichment=enrichment,
                    final_comparison=final,
                    response=response,
                    decision=decision,
                    diagnostic=(
                        "Live pair evaluation completed through "
                        "structured Arval exact-offer service acquisition, "
                        "enrichment and full reassessment."
                    ),
                    stage_timings=tuple(
                        stage_timings
                    ),
                )

            finally:
                browser.close()

    @staticmethod
    def _measure(
        stage_timings,
        stage_name,
        operation,
    ):
        started = perf_counter()

        try:
            return operation()
        finally:
            stage_timings.append(
                (
                    stage_name,
                    round(
                        perf_counter()
                        - started,
                        3,
                    ),
                )
            )

    @classmethod
    def _load(
        cls,
        browser,
        provider: str,
        url: str,
    ):
        builder = cls._builder_for(
            provider
        )
        page = browser.new_page()

        try:
            provider_key = (
                provider
                .strip()
                .casefold()
            )

            if provider_key == "arval":
                route = (
                    ArvalOfferRouteResolver()
                    .resolve(
                        page,
                        url,
                        timeout=60000,
                        settle_ms=1500,
                    )
                )

                if (
                    route.status
                    != ROUTE_LIVE
                    or not route.resolved_url
                ):
                    raise ValueError(
                        "Arval exact-offer route could not be "
                        "validated before builder execution. "
                        + route.diagnostic
                    )

                # Route resolver has already navigated the page to the
                # validated exact-offer route. Do not navigate again.
                cls._dismiss(page)
                page.wait_for_timeout(300)
                return builder.build(page)

            page.goto(
                url,
                wait_until="commit",
                timeout=60000,
            )
            cls._wait_for_ayvens_priced_offer(
                page
            )
            page.wait_for_timeout(300)
            cls._dismiss(page)
            return builder.build(page)

        finally:
            page.close()

    @staticmethod
    def _builder_for(
        provider: str,
    ):
        p = provider.strip().casefold()

        if p == "arval":
            return ArvalEvidenceAwareBuilder()

        if p == "ayvens":
            return AyvensEvidenceAwareBuilder()

        raise ValueError(
            f"Unsupported provider: {provider}"
        )

    @staticmethod
    def _wait_for_ayvens_priced_offer(
        page,
    ):
        # Ayvens' Vue application can return HTTP 200 while its
        # DOMContentLoaded event remains pending. Synchronize on explicit
        # priced-offer DOM evidence instead. This is only a readiness signal;
        # the evidence-aware builder still validates identity, fee, duration
        # and mileage independently.
        price = page.locator(
            "div.font-size-40px.font-size-40px, "
            "div.font-size-40px.fw-500.whitespace-nowrap"
        )
        price.first.wait_for(
            state="attached",
            timeout=60000,
        )

    @classmethod
    def _manufacturer_acquisition(
        cls,
        browser,
        pair,
    ):
        if (
            (pair.brand or "")
            .strip()
            .upper()
            != "BYD"
        ):
            return None

        connector = (
            BYDManufacturerEquipmentConnector(
                browser
            )
        )

        return ManufacturerEquipmentAcquisition(
            canonical_identity_builder=(
                cls._canonical_identity
            ),
            manufacturer_discovery=(
                connector.discover
            ),
        )

    @staticmethod
    def _canonical_key(
        wrapped,
    ):
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
        n = (
            VehicleIdentityNormalizer()
            .normalize(
                brand,
                model,
                trim,
                fuel,
            )
        )

        return {
            "brand": n.brand,
            "model": n.model,
            "fuel_type": n.fuel_type,
            "trim": (
                (trim or "")
                .upper()
                .strip()
            ),
        }

    @classmethod
    def _supported_pair(
        cls,
        pair,
    ) -> bool:
        providers = {
            (
                pair.left_provider
                or ""
            ).strip().casefold(),
            (
                pair.right_provider
                or ""
            ).strip().casefold(),
        }

        return providers == cls.SUPPORTED_PROVIDERS

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
                loc.first.click(timeout=1800)
                page.wait_for_timeout(300)
                return
            except Exception:
                pass
