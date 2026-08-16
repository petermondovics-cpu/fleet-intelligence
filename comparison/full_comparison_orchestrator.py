from dataclasses import dataclass
from typing import Optional, Tuple

from comparison.normalized_vehicle_identity import (
    NormalizedVehicleComparabilityEngine,
)
from comparison.service_package_comparison import (
    SERVICE_DIFFERENCE,
    SERVICE_INSUFFICIENT_EVIDENCE,
    ServicePackageComparisonEngine,
)
from comparison.equipment_value_normalizer import (
    EquipmentValueNormalizer,
)
from comparison.contract_normalization_bridge import (
    ContractNormalizationBridge,
)
from comparison.variant_equivalence_assessor import (
    VARIANT_EQUIVALENT,
    VARIANT_INSUFFICIENT_EVIDENCE,
    VARIANT_NOT_EQUIVALENT,
    VARIANT_VALUE_DIFFERENCE,
    VariantEquivalenceAssessor,
)
from comparison.service_semantic_equivalence import (
    SEMANTIC_DIFFERENCE,
    SEMANTIC_INSUFFICIENT_EVIDENCE,
    SEMANTIC_MATCH,
    SEMANTIC_PARTIAL_EQUIVALENCE,
    ServiceSemanticEquivalenceAssessor,
)

from models.financial_conditions import EVIDENCE_OBSERVED


FULL_READY = "READY_FOR_PRICE_COMPARISON"
FULL_BLOCKED = "INSUFFICIENT_EVIDENCE"
FULL_NOT_COMPARABLE = "NOT_COMPARABLE"


@dataclass(frozen=True)
class FullComparisonBarrier:
    code: str
    message: str
    hard: bool = False


@dataclass(frozen=True)
class FullComparisonResult:
    status: str
    price_comparison_allowed: bool
    price_winner: Optional[str]
    normalized_monthly_fee_left: Optional[int]
    normalized_monthly_fee_right: Optional[int]
    barriers: Tuple[FullComparisonBarrier, ...]
    vehicle_status: str
    service_status: str
    equipment_status: str
    contract_status: str
    financial_status: str
    contract_normalization_method: str
    contract_normalization_confidence: int
    equipment_score_left: Optional[int]
    equipment_score_right: Optional[int]
    variant_status: str = "NOT_EVALUATED"

    @property
    def blocker_codes(self):
        return tuple(
            item.code
            for item in self.barriers
        )


class FullComparisonOrchestrator:
    """
    Full Comparison Orchestrator V5.

    V2 integrated VariantEquivalenceAssessor.
    V3 added enriched service comparison-view inputs.
    V4 added enriched financial comparison-view inputs.
    V5 makes the EQUIPMENT dimension use the same validated enriched
    comparison view already supplied to variant assessment.

    Safety:
    - canonical identity mismatch remains hard;
    - trim wording difference alone is informational, not blocking;
    - different trims require evidence-backed variant equivalence;
    - provider/manufacturer equipment is usable only when its supplied
      evidence status is explicitly trusted;
    - manufacturer equipment never mutates the original CompositeOffer;
    - equipment points never become HUF;
    - contract normalization requires observed pricing evidence;
    - down payment must be observed;
    - enriched service/financial/equipment evidence is comparison-view only;
    - no price winner is emitted while any blocker remains.
    """

    EQUIPMENT_USABLE_STATUSES = {
        "VALIDATED",
        "PUBLISHED",
        "PROVIDER_VALIDATED",
        "MANUFACTURER_VALIDATED",
    }

    def __init__(self):
        self.identity = (
            NormalizedVehicleComparabilityEngine()
        )
        self.services = (
            ServicePackageComparisonEngine()
        )
        self.service_semantics = (
            ServiceSemanticEquivalenceAssessor()
        )
        self.equipment_value = (
            EquipmentValueNormalizer()
        )
        self.contracts = (
            ContractNormalizationBridge()
        )
        self.variants = (
            VariantEquivalenceAssessor()
        )

    def compare(
        self,
        left,
        right,
        observed_offer_pool=None,
        left_variant_items=None,
        right_variant_items=None,
        left_variant_equipment_status=None,
        right_variant_equipment_status=None,
        left_service_package=None,
        right_service_package=None,
        left_financial=None,
        right_financial=None,
        contract_evidence=None,
        left_financial_review=None,
        right_financial_review=None,
    ) -> FullComparisonResult:

        barriers = []

        # ====================================================
        # 1. VEHICLE IDENTITY
        # ====================================================

        vehicle_result = (
            self.identity.compare_identity(
                left,
                right,
            )
        )

        vehicle_status = (
            vehicle_result.status
        )

        if vehicle_status != "COMPARABLE":

            for reason in vehicle_result.reasons:

                barriers.append(
                    FullComparisonBarrier(
                        code=reason.code,
                        message=reason.message,
                        hard=True,
                    )
                )

        lc = left.composite
        rc = right.composite

        # ====================================================
        # 2. VARIANT EQUIVALENCE
        # ====================================================

        variant_result = (
            self.variants.assess(
                left,
                right,
                identity_status=vehicle_status,
                left_items=left_variant_items,
                right_items=right_variant_items,
                left_equipment_status=(
                    left_variant_equipment_status
                ),
                right_equipment_status=(
                    right_variant_equipment_status
                ),
            )
        )

        variant_status = (
            variant_result.status
        )

        if variant_result.trim_differs:

            barriers.append(
                FullComparisonBarrier(
                    code="VEHICLE_VARIANT_DIFFERENCE",
                    message=(
                        "Canonical vehicle identity matches, but the "
                        "advertised trim/version differs."
                    ),
                    hard=False,
                )
            )

        if (
            variant_status
            == VARIANT_INSUFFICIENT_EVIDENCE
        ):

            barriers.append(
                FullComparisonBarrier(
                    code=(
                        "VARIANT_EQUIVALENCE_"
                        "EVIDENCE_INCOMPLETE"
                    ),
                    message=" ".join(
                        variant_result.reasons
                    ),
                    hard=False,
                )
            )

        elif (
            variant_status
            == VARIANT_VALUE_DIFFERENCE
        ):

            barriers.append(
                FullComparisonBarrier(
                    code=(
                        "VARIANT_EQUIPMENT_"
                        "VALUE_DIFFERENCE"
                    ),
                    message=" ".join(
                        variant_result.reasons
                    ),
                    hard=False,
                )
            )

        elif (
            variant_status
            == VARIANT_NOT_EQUIVALENT
        ):

            barriers.append(
                FullComparisonBarrier(
                    code="VARIANT_NOT_EQUIVALENT",
                    message=" ".join(
                        variant_result.reasons
                    ),
                    hard=True,
                )
            )

        # ====================================================
        # 3. SERVICES - SEMANTIC EQUIVALENCE V1
        # ====================================================

        service_left = (
            lc.services
            if left_service_package is None
            else left_service_package
        )
        service_right = (
            rc.services
            if right_service_package is None
            else right_service_package
        )

        semantic_result = self.service_semantics.assess(
            service_left,
            service_right,
        )
        service_status = semantic_result.status

        if service_status == SEMANTIC_DIFFERENCE:
            for diff in semantic_result.contradictions:
                barriers.append(
                    FullComparisonBarrier(
                        code="SERVICE_SEMANTIC_MISMATCH",
                        message=(
                            f"Canonical service {diff.code} has an explicit "
                            "inclusion contradiction."
                        ),
                        hard=True,
                    )
                )

        elif service_status == SEMANTIC_PARTIAL_EQUIVALENCE:
            unresolved = (
                tuple(
                    f"LEFT:{code}"
                    for code in semantic_result.left_only_codes
                )
                + tuple(
                    f"RIGHT:{code}"
                    for code in semantic_result.right_only_codes
                )
            )
            barriers.append(
                FullComparisonBarrier(
                    code="SERVICE_SEMANTIC_EQUIVALENCE_INCOMPLETE",
                    message=(
                        "Core service semantics match, but additional "
                        "one-sided published semantics remain unresolved: "
                        + ", ".join(unresolved)
                        + "."
                    ),
                    hard=False,
                )
            )

        elif service_status == SEMANTIC_INSUFFICIENT_EVIDENCE:
            barriers.append(
                FullComparisonBarrier(
                    code="SERVICE_SEMANTIC_EVIDENCE_INCOMPLETE",
                    message=semantic_result.diagnostic,
                    hard=False,
                )
            )

        elif service_status != SEMANTIC_MATCH:
            raise ValueError(
                "Unsupported semantic service status: "
                + str(service_status)
            )

        # ====================================================
        # 4. EQUIPMENT DIMENSION
        # ====================================================
        #
        # V5 fixes the split-brain behavior where variant assessment used
        # enriched equipment but the equipment dimension still inspected
        # only the original provider publication state.
        #
        # If a validated comparison-view status/items pair is supplied,
        # use it here too. Otherwise preserve the original provider-only
        # behavior used by initial comparisons.
        # ====================================================

        equipment_score_left = None
        equipment_score_right = None

        equipment_left_items = (
            tuple(lc.vehicle.all_equipment)
            if left_variant_items is None
            else tuple(left_variant_items)
        )

        equipment_right_items = (
            tuple(rc.vehicle.all_equipment)
            if right_variant_items is None
            else tuple(right_variant_items)
        )

        equipment_left_usable = (
            self._equipment_view_usable(
                left,
                left_variant_items,
                left_variant_equipment_status,
            )
        )

        equipment_right_usable = (
            self._equipment_view_usable(
                right,
                right_variant_items,
                right_variant_equipment_status,
            )
        )

        if not (
            equipment_left_usable
            and equipment_right_usable
        ):

            equipment_status = (
                "INSUFFICIENT_EVIDENCE"
            )

            barriers.append(
                FullComparisonBarrier(
                    code=(
                        "EQUIPMENT_EVIDENCE_INCOMPLETE"
                    ),
                    message=(
                        "At least one side lacks complete usable "
                        "provider or validated manufacturer equipment "
                        "evidence for the comparison view."
                    ),
                )
            )

        else:

            equipment_comparison = (
                self.equipment_value.compare(
                    equipment_left_items,
                    equipment_right_items,
                )
            )

            equipment_score_left = (
                equipment_comparison
                .left
                .known_score
            )

            equipment_score_right = (
                equipment_comparison
                .right
                .known_score
            )

            if not (
                equipment_comparison
                .fully_scored
            ):

                equipment_status = (
                    "INSUFFICIENT_EVIDENCE"
                )

                barriers.append(
                    FullComparisonBarrier(
                        code=(
                            "EQUIPMENT_VALUE_"
                            "EVIDENCE_INCOMPLETE"
                        ),
                        message=(
                            "One or more usable equipment "
                            "items have no canonical "
                            "valuation rule yet."
                        ),
                    )
                )

            elif (
                equipment_comparison
                .score_delta != 0
            ):

                equipment_status = (
                    "VALUE_DIFFERENCE"
                )

                barriers.append(
                    FullComparisonBarrier(
                        code=(
                            "EQUIPMENT_VALUE_DIFFERENCE"
                        ),
                        message=(
                            "Canonical equipment value "
                            "scores differ. V5 does not "
                            "convert that difference "
                            "to HUF."
                        ),
                    )
                )

            else:

                equipment_status = "MATCH"

        # ====================================================
        # 5. CONTRACT NORMALIZATION - EXPLICIT EVIDENCE V1
        # ====================================================

        contract_result = (
            self.contracts.normalize(
                left,
                right,
                observed_offer_pool=(
                    observed_offer_pool
                    or [
                        lc.offer,
                        rc.offer,
                    ]
                ),
                other_barriers_passed=False,
            )
        )

        normalization = (
            contract_result.normalization
        )

        contract_status = normalization.normalization_status
        contract_price_available = normalization.normalized_price_available
        contract_normalized_left = (
            normalization.normalized_monthly_fee_a
            if contract_price_available
            else None
        )
        contract_normalized_right = (
            normalization.normalized_monthly_fee_b
            if contract_price_available
            else None
        )
        contract_method = normalization.normalization_method
        contract_confidence = normalization.normalization_confidence
        contract_blocker_message = normalization.normalization_reason

        if contract_evidence is not None:
            selected = getattr(
                contract_evidence,
                "selected_coordinate",
                None,
            )

            if (
                getattr(
                    contract_evidence,
                    "status",
                    None,
                ) == "RESOLVED"
                and selected is not None
            ):
                contract_status = "EXACT_COMMON_CONTRACT_OBSERVED"
                contract_price_available = True
                contract_normalized_left = selected.left.monthly_fee
                contract_normalized_right = selected.right.monthly_fee
                contract_method = "EXPLICIT_COMMON_CONTRACT_STATE"
                contract_confidence = 100
                contract_blocker_message = ""

            else:
                contract_status = "EVIDENCE_UNRESOLVED"
                contract_price_available = False
                contract_normalized_left = None
                contract_normalized_right = None
                contract_method = "EXPLICIT_COMMON_CONTRACT_STATE"
                contract_confidence = 0

                left_observed = tuple(
                    getattr(
                        contract_evidence,
                        "left_observations",
                        (),
                    )
                )
                right_observed = tuple(
                    getattr(
                        contract_evidence,
                        "right_observations",
                        (),
                    )
                )
                attempted = tuple(
                    getattr(
                        contract_evidence,
                        "attempted_coordinates",
                        (),
                    )
                )

                left_text = ", ".join(
                    f"{item.provider} {item.duration}m/{item.mileage}km = "
                    f"{item.monthly_fee} Ft"
                    for item in left_observed
                ) or "none"

                right_text = ", ".join(
                    f"{item.provider} {item.duration}m/{item.mileage}km = "
                    f"{item.monthly_fee} Ft"
                    for item in right_observed
                ) or "none"

                attempted_text = ", ".join(
                    f"{duration}m/{mileage}km"
                    for duration, mileage in attempted
                ) or "none"

                contract_blocker_message = (
                    "No exact priced common contract coordinate was "
                    "observed for both providers. "
                    f"Observed left: {left_text}. "
                    f"Observed right: {right_text}. "
                    f"Attempted common coordinates: {attempted_text}. "
                    "No interpolation, extrapolation or provider term "
                    "factor was used."
                )

        if not contract_price_available:
            barriers.append(
                FullComparisonBarrier(
                    code="CONTRACT_NORMALIZATION_INCOMPLETE",
                    message=contract_blocker_message,
                )
            )

        # ====================================================
        # 6. FINANCIAL CONDITIONS
        # ====================================================

        financial_left = (
            lc.financial
            if left_financial is None
            else left_financial
        )

        financial_right = (
            rc.financial
            if right_financial is None
            else right_financial
        )

        financial_status = (
            self._financial_status(
                financial_left,
                financial_right,
                barriers,
                left_review=left_financial_review,
                right_review=right_financial_review,
            )
        )

        # ====================================================
        # 7. FINAL DECISION
        # ====================================================

        hard_blocker = any(
            item.hard
            for item in barriers
        )

        # Pure trim wording is informational only.
        # Variant/equipment assessment represents its economic consequence.
        blocking_codes = {
            item.code
            for item in barriers
            if (
                item.code
                != "VEHICLE_VARIANT_DIFFERENCE"
            )
        }

        allowed = (
            vehicle_status == "COMPARABLE"
            and variant_status
            == VARIANT_EQUIVALENT
            and not hard_blocker
            and not blocking_codes
            and contract_price_available
            and financial_status == "MATCH"
        )

        normalized_left = (
            contract_normalized_left
            if contract_price_available
            else None
        )

        normalized_right = (
            contract_normalized_right
            if contract_price_available
            else None
        )

        price_winner = None

        if allowed:

            if (
                normalized_left
                < normalized_right
            ):

                price_winner = lc.provider

            elif (
                normalized_right
                < normalized_left
            ):

                price_winner = rc.provider

            else:

                price_winner = "TIE"

        if hard_blocker:

            final_status = (
                FULL_NOT_COMPARABLE
            )

        elif allowed:

            final_status = FULL_READY

        else:

            final_status = FULL_BLOCKED

        return FullComparisonResult(
            status=final_status,
            price_comparison_allowed=allowed,
            price_winner=price_winner,
            normalized_monthly_fee_left=(
                normalized_left
            ),
            normalized_monthly_fee_right=(
                normalized_right
            ),
            barriers=tuple(barriers),
            vehicle_status=vehicle_status,
            service_status=service_status,
            equipment_status=equipment_status,
            contract_status=contract_status,
            financial_status=financial_status,
            contract_normalization_method=(
                contract_method
            ),
            contract_normalization_confidence=(
                contract_confidence
            ),
            equipment_score_left=(
                equipment_score_left
            ),
            equipment_score_right=(
                equipment_score_right
            ),
            variant_status=variant_status,
        )

    # ========================================================
    # EQUIPMENT COMPARISON VIEW
    # ========================================================

    @classmethod
    def _equipment_view_usable(
        cls,
        side,
        supplied_items,
        supplied_status,
    ) -> bool:
        """
        A supplied enriched equipment view is usable only with an explicit
        trusted status. If no enriched view is supplied, preserve legacy
        provider-only fully_comparable behavior.
        """

        if supplied_items is not None:
            return (
                supplied_status
                in cls.EQUIPMENT_USABLE_STATUSES
            )

        evidence = getattr(
            side,
            "equipment_evidence",
            None,
        )

        return bool(
            evidence is not None
            and getattr(
                evidence,
                "fully_comparable",
                False,
            )
        )

    # ========================================================
    # FINANCIAL COMPARISON
    # ========================================================

    def _financial_status(
        self,
        left,
        right,
        barriers,
        left_review=None,
        right_review=None,
    ) -> str:

        left_dp = left.down_payment
        right_dp = right.down_payment

        if (
            left_dp.status
            != EVIDENCE_OBSERVED
            or
            right_dp.status
            != EVIDENCE_OBSERVED
        ):

            barriers.append(
                FullComparisonBarrier(
                    code=(
                        "DOWN_PAYMENT_EVIDENCE_INCOMPLETE"
                    ),
                    message=(
                        self._down_payment_incomplete_message(
                            left,
                            right,
                            left_review,
                            right_review,
                        )
                    ),
                )
            )

            return (
                "INSUFFICIENT_EVIDENCE"
            )

        if not (
            self._same_down_payment(
                left_dp,
                right_dp,
            )
        ):

            barriers.append(
                FullComparisonBarrier(
                    code="DOWN_PAYMENT_MISMATCH",
                    message=(
                        "Observed down-payment "
                        "conditions differ."
                    ),
                    hard=True,
                )
            )

            return "DIFFERENCE"

        for attr, code in (
            (
                "other_one_off_fees",
                "ONE_OFF_FEE_MISMATCH",
            ),
            (
                "other_recurring_fees",
                "RECURRING_FEE_MISMATCH",
            ),
        ):

            a = getattr(left, attr)
            b = getattr(right, attr)

            if (
                a is not None
                and b is not None
                and a != b
            ):

                barriers.append(
                    FullComparisonBarrier(
                        code=code,
                        message=(
                            "Observed financial fee "
                            f"field {attr} differs."
                        ),
                        hard=True,
                    )
                )

                return "DIFFERENCE"

        return "MATCH"

    # ========================================================
    # HELPERS
    # ========================================================

    @staticmethod
    def _financial_review_summary(
        side_label,
        financial,
        review,
    ):
        down_payment = getattr(
            financial,
            "down_payment",
            None,
        )
        status = getattr(
            down_payment,
            "status",
            None,
        )

        if status == EVIDENCE_OBSERVED:
            percent = getattr(
                down_payment,
                "percent",
                None,
            )
            amount = getattr(
                down_payment,
                "amount",
                None,
            )

            if percent is not None:
                value = f"{percent}%"
            elif amount is not None:
                value = f"{amount} Ft"
            else:
                value = "explicit condition"

            return f"{side_label}: OBSERVED ({value})"

        if review is None:
            return (
                f"{side_label}: UNKNOWN "
                "(no deep publication review context)"
            )

        review_status = getattr(
            review,
            "status",
            "UNRESOLVED",
        )
        surfaces = ", ".join(
            getattr(
                review,
                "reviewed_surfaces",
                (),
            )
        ) or "none"

        if review_status == "REVIEWED_NOT_PUBLISHED":
            return (
                f"{side_label}: UNKNOWN / REVIEWED_NOT_PUBLISHED "
                f"(reviewed: {surfaces})"
            )

        if review_status == "OBSERVED":
            return (
                f"{side_label}: OBSERVED "
                f"(reviewed: {surfaces})"
            )

        return (
            f"{side_label}: UNKNOWN / REVIEW_UNRESOLVED "
            f"(reviewed: {surfaces})"
        )

    @classmethod
    def _down_payment_incomplete_message(
        cls,
        left,
        right,
        left_review,
        right_review,
    ):
        left_text = cls._financial_review_summary(
            "Left",
            left,
            left_review,
        )
        right_text = cls._financial_review_summary(
            "Right",
            right,
            right_review,
        )

        return (
            "Down payment is not explicitly observed for both offers. "
            + left_text
            + ". "
            + right_text
            + ". REVIEWED_NOT_PUBLISHED means publication was actively "
            "checked; it does not mean 0% down payment. "
            "No default 20% or zero-down assumption is allowed."
        )

    @staticmethod
    def _same_down_payment(
        left_dp,
        right_dp,
    ) -> bool:

        if (
            left_dp.percent is not None
            and right_dp.percent is not None
        ):
            return (
                abs(
                    left_dp.percent
                    - right_dp.percent
                )
                < 1e-9
            )

        if (
            left_dp.amount is not None
            and right_dp.amount is not None
        ):
            return (
                left_dp.amount
                == right_dp.amount
            )

        return False
