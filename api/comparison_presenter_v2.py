from typing import Optional

from api.comparison_contract import (
    BlockerDTO,
    ContractDTO,
    DimensionStatusDTO,
    DownPaymentDTO,
    EvidenceDTO,
    OfferDTO,
    PriceDTO,
    VehicleDTO,
)
from api.comparison_contract_v2 import (
    API_VERSION_V2,
    ComparisonResponseV2,
    DecisionDTO,
    ObservedPriceDifferenceDTO,
)

class ComparisonPresenterV2:
    def present(
        self,
        result,
        decision,
        left,
        right,
        *,
        left_financial=None,
        right_financial=None,
        left_pricing_basis: Optional[str] = None,
        right_pricing_basis: Optional[str] = None,
    ) -> ComparisonResponseV2:

        if decision is None:
            raise ValueError("ComparisonPresenterV2 requires a validated decision object.")

        lc = left.composite
        rc = right.composite
        lf = lc.financial if left_financial is None else left_financial
        rf = rc.financial if right_financial is None else right_financial

        return ComparisonResponseV2(
            api_version=API_VERSION_V2,
            status=result.status,
            price_comparison_allowed=result.price_comparison_allowed,
            price_winner=result.price_winner,
            left_offer=self._offer(lc, lf, result.normalized_monthly_fee_left, left_pricing_basis),
            right_offer=self._offer(rc, rf, result.normalized_monthly_fee_right, right_pricing_basis),
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
            contract_normalization_confidence=result.contract_normalization_confidence,
            equipment_score_left=result.equipment_score_left,
            equipment_score_right=result.equipment_score_right,
            decision=self._decision(decision),
        )

    @staticmethod
    def _decision(decision) -> DecisionDTO:
        observed = decision.observed_price_difference
        return DecisionDTO(
            verdict=decision.verdict,
            price_winner=decision.price_winner,
            price_comparison_allowed=decision.price_comparison_allowed,
            observed_price_difference=ObservedPriceDifferenceDTO(
                lower_provider=observed.lower_provider,
                difference_huf=observed.difference_huf,
                difference_percent=observed.difference_percent,
                normalized=observed.normalized,
            ),
            decision_reasons=tuple(decision.decision_reasons),
            confidence=decision.confidence,
            management_summary=decision.management_summary,
            next_best_action=decision.next_best_action,
        )

    @classmethod
    def _offer(cls, composite, financial, normalized_fee, pricing_basis):
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
