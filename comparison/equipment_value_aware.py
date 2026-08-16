from models.comparable_offer import (
    COMPARABLE,
    NORMALIZATION_REQUIRED,
    INSUFFICIENT_EVIDENCE,
    ComparabilityReason,
    ComparableOfferResult,
)
from comparison.normalized_evidence_aware import (
    NormalizedEvidenceAwareComparableEngine,
)
from comparison.equipment_value_normalizer import (
    EquipmentValueNormalizer,
)


class EquipmentValueAwareComparableEngine:
    """
    Comparison V3.

    Extends the normalized/evidence-aware barrier with conservative
    equipment scoring.

    IMPORTANT:
    Equipment scores are qualitative comparison points only.
    They do not alter monthly fees.
    """

    def __init__(self):
        self.base = (
            NormalizedEvidenceAwareComparableEngine()
        )

        self.equipment_value = (
            EquipmentValueNormalizer()
        )

    def compare(
        self,
        left,
        right,
    ) -> ComparableOfferResult:

        base_result = self.base.compare(
            left,
            right,
        )

        codes = {
            reason.code
            for reason in base_result.reasons
        }

        # If equipment evidence is incomplete, valuation cannot rescue it.
        if (
            "EQUIPMENT_EVIDENCE_INCOMPLETE"
            in codes
        ):
            return base_result

        # If the base layer already produced a hard conclusion unrelated
        # to equipment-set normalization, preserve it.
        if (
            base_result.status
            not in {
                INSUFFICIENT_EVIDENCE,
                COMPARABLE,
                NORMALIZATION_REQUIRED,
            }
        ):
            return base_result

        if (
            "EQUIPMENT_VALUE_NORMALIZATION_REQUIRED"
            not in codes
        ):
            return base_result

        comparison = (
            self.equipment_value.compare(
                left.composite.vehicle.all_equipment,
                right.composite.vehicle.all_equipment,
            )
        )

        reasons = [
            r
            for r in base_result.reasons
            if (
                r.code
                != "EQUIPMENT_VALUE_NORMALIZATION_REQUIRED"
            )
        ]

        reasons.append(
            ComparabilityReason(
                code="EQUIPMENT_SCORE_DELTA",
                message=(
                    "Known relative equipment score delta "
                    f"(right - left): {comparison.score_delta} points."
                ),
            )
        )

        if not comparison.fully_scored:

            reasons.append(
                ComparabilityReason(
                    code="EQUIPMENT_VALUE_EVIDENCE_INCOMPLETE",
                    message=(
                        "One or more published equipment items "
                        "have no canonical valuation rule yet."
                    ),
                )
            )

            return ComparableOfferResult(
                status=INSUFFICIENT_EVIDENCE,
                reasons=reasons,
            )

        # Equipment is fully scored, but a non-zero delta still means
        # the two offers are not yet price-equivalent.
        if comparison.score_delta != 0:

            reasons.append(
                ComparabilityReason(
                    code="EQUIPMENT_VALUE_DIFFERENCE",
                    message=(
                        "Published equipment differs in relative "
                        "comparison value. Price comparison requires "
                        "a later business-defined tolerance or HUF "
                        "valuation model."
                    ),
                )
            )

            return ComparableOfferResult(
                status=INSUFFICIENT_EVIDENCE,
                reasons=reasons,
            )

        # Equal known equipment value allows the prior contract status.
        contract_codes = {
            r.code
            for r in reasons
        }

        if (
            "TERM_NORMALIZATION_REQUIRED"
            in contract_codes
            or
            "MILEAGE_NORMALIZATION_REQUIRED"
            in contract_codes
        ):
            return ComparableOfferResult(
                status=NORMALIZATION_REQUIRED,
                reasons=reasons,
            )

        return ComparableOfferResult(
            status=COMPARABLE,
            reasons=reasons,
        )
