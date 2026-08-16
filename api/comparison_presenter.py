from typing import Optional

from api.comparison_contract import (
    API_VERSION,
    BlockerDTO,
    ComparisonResponseV1,
    ContractDTO,
    DimensionStatusDTO,
    DownPaymentDTO,
    EvidenceDTO,
    OfferDTO,
    PriceDTO,
    VehicleDTO,
)


class ComparisonPresenterV1:
    """
    Stable frontend-facing presenter.

    Domain objects remain the source of truth. Enriched financial views may be
    supplied for presentation, but the original CompositeOffer is never mutated.
    """

    def present(
        self,
        result,
        left,
        right,
        *,
        left_financial=None,
        right_financial=None,
        left_pricing_basis: Optional[str] = None,
        right_pricing_basis: Optional[str] = None,
    ) -> ComparisonResponseV1:

        lc = left.composite
        rc = right.composite

        lf = lc.financial if left_financial is None else left_financial
        rf = rc.financial if right_financial is None else right_financial

        return ComparisonResponseV1(
            api_version=API_VERSION,
            status=result.status,
            price_comparison_allowed=result.price_comparison_allowed,
            price_winner=result.price_winner,
            left_offer=self._offer(
                lc,
                lf,
                result.normalized_monthly_fee_left,
                left_pricing_basis,
            ),
            right_offer=self._offer(
                rc,
                rf,
                result.normalized_monthly_fee_right,
                right_pricing_basis,
            ),
            dimensions=DimensionStatusDTO(
                vehicle=result.vehicle_status,
                variant=result.variant_status,
                services=result.service_status,
                equipment=result.equipment_status,
                contract=result.contract_status,
                financial=result.financial_status,
            ),
            blockers=tuple(
                BlockerDTO(
                    code=item.code,
                    severity="HARD" if item.hard else "EVIDENCE",
                    message=item.message,
                )
                for item in result.barriers
            ),
            contract_normalization_method=result.contract_normalization_method,
            contract_normalization_confidence=(
                result.contract_normalization_confidence
            ),
            equipment_score_left=result.equipment_score_left,
            equipment_score_right=result.equipment_score_right,
        )

    @classmethod
    def _offer(
        cls,
        composite,
        financial,
        normalized_fee,
        pricing_basis,
    ):
        offer = composite.offer
        vehicle = composite.vehicle

        return OfferDTO(
            provider=composite.provider,
            vehicle=VehicleDTO(
                brand=vehicle.brand,
                model=vehicle.model,
                trim=vehicle.trim,
                fuel_type=vehicle.fuel_type,
            ),
            contract=ContractDTO(
                duration_months=offer.duration,
                mileage_km_per_year=offer.mileage,
            ),
            price=PriceDTO(
                # Advertised price always means the original provider-facing
                # commercial record, never the enriched comparison baseline.
                advertised_monthly_fee_huf=offer.monthly_fee,
                comparable_monthly_fee_huf=normalized_fee,
                down_payment=cls._down_payment(financial.down_payment),
                pricing_basis=pricing_basis,
            ),
            source_url=offer.url,
        )

    @staticmethod
    def _down_payment(down_payment):
        evidence = down_payment.evidence

        return DownPaymentDTO(
            status=down_payment.status,
            percent=down_payment.percent,
            amount_huf=down_payment.amount,
            evidence=EvidenceDTO(
                status=evidence.status,
                source_url=evidence.source_url or None,
                source_text=evidence.source_text or None,
            ),
        )
