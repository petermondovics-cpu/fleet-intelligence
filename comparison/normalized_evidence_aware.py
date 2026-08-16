from models.comparable_offer import (
    COMPARABLE,
    NORMALIZATION_REQUIRED,
    NOT_COMPARABLE,
    INSUFFICIENT_EVIDENCE,
    ComparabilityReason,
    ComparableOfferResult,
)
from comparison.evidence_aware_comparable import (
    EvidenceAwareCompositeOffer,
)
from comparison.normalized_vehicle_identity import (
    NormalizedVehicleComparabilityEngine,
)
from comparison.service_package_comparison import (
    SERVICE_DIFFERENCE,
    SERVICE_INSUFFICIENT_EVIDENCE,
    ServicePackageComparisonEngine,
)


class NormalizedEvidenceAwareComparableEngine:
    """
    Full comparability barrier V3.

    V3 replaces raw provider service-name matching with canonical
    ServicePackageComparisonEngine semantics.

    Ordering:
    1. canonical brand/model/fuel identity
    2. variant/trim difference
    3. contract term/mileage
    4. canonical service comparison
    5. equipment evidence
    6. equipment-set equivalence

    No price winner is declared here.
    """

    def __init__(self):
        self.identity = NormalizedVehicleComparabilityEngine()
        self.services = ServicePackageComparisonEngine()

    def compare(
        self,
        left: EvidenceAwareCompositeOffer,
        right: EvidenceAwareCompositeOffer,
    ) -> ComparableOfferResult:

        identity_result = self.identity.compare_identity(left, right)

        if identity_result.status != COMPARABLE:
            return identity_result

        lc = left.composite
        rc = right.composite
        reasons = list(identity_result.reasons)

        # ----------------------------------------------------
        # VARIANT / TRIM
        # ----------------------------------------------------

        trim_differs = (
            lc.vehicle.trim.strip().casefold()
            != rc.vehicle.trim.strip().casefold()
        )

        if trim_differs:
            reasons.append(
                ComparabilityReason(
                    code="VEHICLE_VARIANT_DIFFERENCE",
                    message=(
                        "Canonical vehicle family and fuel match, "
                        "but the advertised trim/version differs. "
                        "Equipment evidence is required before a fair "
                        "price comparison can be made."
                    ),
                )
            )

        normalization_required = False

        # ----------------------------------------------------
        # CONTRACT
        # ----------------------------------------------------

        if lc.duration != rc.duration:
            normalization_required = True
            reasons.append(
                ComparabilityReason(
                    code="TERM_NORMALIZATION_REQUIRED",
                    message=(
                        "Contract duration differs and requires normalization."
                    ),
                )
            )

        if lc.mileage != rc.mileage:
            normalization_required = True
            reasons.append(
                ComparabilityReason(
                    code="MILEAGE_NORMALIZATION_REQUIRED",
                    message=(
                        "Annual mileage differs and requires normalization."
                    ),
                )
            )

        # ----------------------------------------------------
        # CANONICAL SERVICES
        # ----------------------------------------------------

        service_result = self.services.compare(
            lc.services,
            rc.services,
        )

        if service_result.status == SERVICE_DIFFERENCE:
            for diff in service_result.differences:
                reasons.append(
                    ComparabilityReason(
                        code="SERVICE_MISMATCH",
                        message=(
                            f"Canonical service {diff.code} has an "
                            f"explicit inclusion contradiction: "
                            f"{diff.left_included} vs {diff.right_included}."
                        ),
                    )
                )

            return ComparableOfferResult(
                status=NOT_COMPARABLE,
                reasons=reasons,
            )

        if service_result.status == SERVICE_INSUFFICIENT_EVIDENCE:
            if service_result.left_only_codes:
                reasons.append(
                    ComparabilityReason(
                        code="SERVICE_LEFT_ONLY_PUBLISHED",
                        message=(
                            "Canonical services published only by the "
                            "left provider: "
                            + ", ".join(service_result.left_only_codes)
                            + "."
                        ),
                    )
                )

            if service_result.right_only_codes:
                reasons.append(
                    ComparabilityReason(
                        code="SERVICE_RIGHT_ONLY_PUBLISHED",
                        message=(
                            "Canonical services published only by the "
                            "right provider: "
                            + ", ".join(service_result.right_only_codes)
                            + "."
                        ),
                    )
                )

            if service_result.left_unknown:
                reasons.append(
                    ComparabilityReason(
                        code="SERVICE_LEFT_UNKNOWN_WORDING",
                        message=(
                            "Unnormalized left-provider service wording: "
                            + "; ".join(service_result.left_unknown)
                            + "."
                        ),
                    )
                )

            if service_result.right_unknown:
                reasons.append(
                    ComparabilityReason(
                        code="SERVICE_RIGHT_UNKNOWN_WORDING",
                        message=(
                            "Unnormalized right-provider service wording: "
                            + "; ".join(service_result.right_unknown)
                            + "."
                        ),
                    )
                )

            reasons.append(
                ComparabilityReason(
                    code="SERVICE_EVIDENCE_INCOMPLETE",
                    message=(
                        "Published service coverage is not sufficient to "
                        "prove equivalent service packages. Missing publication "
                        "is not treated as exclusion."
                    ),
                )
            )

            return ComparableOfferResult(
                status=INSUFFICIENT_EVIDENCE,
                reasons=reasons,
            )

        # ----------------------------------------------------
        # EQUIPMENT EVIDENCE
        # ----------------------------------------------------

        if not (
            left.equipment_evidence.fully_comparable
            and right.equipment_evidence.fully_comparable
        ):
            reasons.append(
                ComparabilityReason(
                    code="EQUIPMENT_EVIDENCE_INCOMPLETE",
                    message=(
                        "At least one provider does not publish or could "
                        "not safely expose complete equipment evidence."
                    ),
                )
            )

            return ComparableOfferResult(
                status=INSUFFICIENT_EVIDENCE,
                reasons=reasons,
            )

        # ----------------------------------------------------
        # EQUIPMENT SETS
        # ----------------------------------------------------

        left_equipment = {
            item.name.casefold(): item
            for item in lc.vehicle.all_equipment
            if item.included is True
        }

        right_equipment = {
            item.name.casefold(): item
            for item in rc.vehicle.all_equipment
            if item.included is True
        }

        if set(left_equipment) != set(right_equipment):
            reasons.append(
                ComparabilityReason(
                    code="EQUIPMENT_VALUE_NORMALIZATION_REQUIRED",
                    message=(
                        "Published included-equipment sets differ. "
                        "The offers require an equipment-value "
                        "normalization layer before price comparison."
                    ),
                )
            )

            return ComparableOfferResult(
                status=INSUFFICIENT_EVIDENCE,
                reasons=reasons,
            )

        if normalization_required:
            return ComparableOfferResult(
                status=NORMALIZATION_REQUIRED,
                reasons=reasons,
            )

        return ComparableOfferResult(
            status=COMPARABLE,
            reasons=reasons,
        )
