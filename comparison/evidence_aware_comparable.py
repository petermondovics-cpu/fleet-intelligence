from dataclasses import dataclass

from models.comparable_offer import (
    COMPARABLE,
    NORMALIZATION_REQUIRED,
    NOT_COMPARABLE,
    INSUFFICIENT_EVIDENCE,
    ComparabilityReason,
    ComparableOfferEngine,
    ComparableOfferResult,
)
from models.composite_offer import CompositeOffer
from models.equipment_evidence import (
    EquipmentEvidenceStatus,
)


@dataclass(frozen=True)
class EvidenceAwareCompositeOffer:
    """
    CompositeOffer + provider-level equipment publication evidence.
    """

    composite: CompositeOffer
    equipment_evidence: EquipmentEvidenceStatus

    @property
    def provider(self) -> str:
        return self.composite.provider


class EvidenceAwareComparableOfferEngine:
    """
    Comparable Offer V2 barrier.

    Order of operations:
    1. Run the existing ComparableOfferEngine.
    2. Preserve hard mismatches such as vehicle/service mismatch.
    3. If the base result would allow price comparison but equipment
       publication evidence is incomplete on either side, return
       INSUFFICIENT_EVIDENCE instead of a false comparable result.
    """

    def __init__(self):
        self.base = ComparableOfferEngine()

    def compare(
        self,
        left: EvidenceAwareCompositeOffer,
        right: EvidenceAwareCompositeOffer,
    ) -> ComparableOfferResult:

        base_result = self.base.compare(
            left.composite,
            right.composite,
        )

        # Hard mismatches remain hard mismatches.
        if base_result.status == NOT_COMPARABLE:
            return base_result

        # Existing insufficient evidence remains insufficient.
        if (
            base_result.status
            == INSUFFICIENT_EVIDENCE
        ):
            return base_result

        # If equipment publication evidence is incomplete,
        # price comparison must not proceed.
        if not (
            left.equipment_evidence.fully_comparable
            and right.equipment_evidence.fully_comparable
        ):
            reasons = list(
                base_result.reasons
            )

            reasons.append(
                ComparabilityReason(
                    code="EQUIPMENT_EVIDENCE_INCOMPLETE",
                    message=(
                        "Equipment comparison cannot be completed "
                        "because at least one provider does not publish "
                        "or could not safely expose standard/optional "
                        "equipment evidence."
                    ),
                )
            )

            return ComparableOfferResult(
                status=INSUFFICIENT_EVIDENCE,
                reasons=reasons,
            )

        # Both providers publish equipment evidence.
        return base_result
