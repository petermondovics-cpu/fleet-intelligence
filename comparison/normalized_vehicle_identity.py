from dataclasses import dataclass

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
from models.vehicle_identity_normalizer import (
    VehicleIdentityNormalizer,
)


@dataclass(frozen=True)
class NormalizedIdentityPair:
    left_brand: str
    left_model: str
    left_fuel: str
    right_brand: str
    right_model: str
    right_fuel: str


class NormalizedVehicleComparabilityEngine:
    """
    Vehicle identity barrier V1.

    This layer only decides whether the normalized vehicle identity
    can pass to later comparability checks.

    It does NOT declare price winners and does NOT normalize contract
    duration/mileage.
    """

    def __init__(self):
        self.normalizer = (
            VehicleIdentityNormalizer()
        )

    def normalize_pair(
        self,
        left: EvidenceAwareCompositeOffer,
        right: EvidenceAwareCompositeOffer,
    ) -> NormalizedIdentityPair:

        lc = left.composite
        rc = right.composite

        l = self.normalizer.normalize(
            lc.offer.brand,
            lc.offer.model,
            lc.offer.trim,
            lc.offer.fuel_type,
        )

        r = self.normalizer.normalize(
            rc.offer.brand,
            rc.offer.model,
            rc.offer.trim,
            rc.offer.fuel_type,
        )

        return NormalizedIdentityPair(
            left_brand=l.brand,
            left_model=l.model,
            left_fuel=l.fuel_type,
            right_brand=r.brand,
            right_model=r.model,
            right_fuel=r.fuel_type,
        )

    def compare_identity(
        self,
        left: EvidenceAwareCompositeOffer,
        right: EvidenceAwareCompositeOffer,
    ) -> ComparableOfferResult:

        pair = self.normalize_pair(
            left,
            right,
        )

        if (
            pair.left_brand
            != pair.right_brand
        ):
            return self._not_comparable(
                "VEHICLE_BRAND_MISMATCH",
                "Normalized vehicle brands do not match.",
            )

        if (
            pair.left_model
            != pair.right_model
        ):
            return self._not_comparable(
                "VEHICLE_MODEL_MISMATCH",
                "Normalized vehicle models do not match.",
            )

        if (
            pair.left_fuel
            != pair.right_fuel
        ):
            return self._not_comparable(
                "FUEL_TYPE_MISMATCH",
                "Normalized fuel types do not match.",
            )

        return ComparableOfferResult(
            status=COMPARABLE,
            reasons=[
                ComparabilityReason(
                    code="NORMALIZED_VEHICLE_IDENTITY_MATCH",
                    message=(
                        "Provider-specific vehicle identity names "
                        "normalize to the same brand/model/fuel."
                    ),
                )
            ],
        )

    @staticmethod
    def _not_comparable(
        code,
        message,
    ):

        return ComparableOfferResult(
            status=NOT_COMPARABLE,
            reasons=[
                ComparabilityReason(
                    code=code,
                    message=message,
                )
            ],
        )
