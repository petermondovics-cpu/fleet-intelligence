from dataclasses import dataclass, field
from typing import List

from models.composite_offer import CompositeOffer


COMPARABLE = "COMPARABLE"
NORMALIZATION_REQUIRED = "NORMALIZATION_REQUIRED"
NOT_COMPARABLE = "NOT_COMPARABLE"
INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


@dataclass(frozen=True)
class ComparabilityReason:
    code: str
    message: str


@dataclass(frozen=True)
class ComparableOfferResult:
    status: str
    reasons: List[ComparabilityReason] = field(
        default_factory=list
    )

    @property
    def comparable(self) -> bool:
        return self.status in {
            COMPARABLE,
            NORMALIZATION_REQUIRED,
        }


class ComparableOfferEngine:
    """
    Comparable Offer V1.

    This engine decides whether two CompositeOffer objects can be
    compared. It deliberately does NOT calculate price advantage.

    Rules:
    1. Vehicle identity must match.
    2. Fuel type must match when both are known.
    3. Duration must match, otherwise normalization is required.
    4. Mileage must match, otherwise normalization is required.
    5. Explicit service contradictions make offers non-comparable.
    6. Explicit equipment contradictions make offers non-comparable.
    7. UNKNOWN evidence cannot be interpreted as exclusion.
    8. Missing evidence prevents a definitive comparison when the
       missing fact is material.
    """

    def compare(
        self,
        left: CompositeOffer,
        right: CompositeOffer,
    ) -> ComparableOfferResult:

        reasons: List[ComparabilityReason] = []
        normalization_required = False

        # --------------------------------------------------------
        # VEHICLE
        # --------------------------------------------------------

        if not self._same_known(
            left.vehicle.brand,
            right.vehicle.brand,
        ):
            return self._not_comparable(
                "VEHICLE_BRAND_MISMATCH",
                "Vehicle brands do not match.",
            )

        if not self._same_known(
            left.vehicle.model,
            right.vehicle.model,
        ):
            return self._not_comparable(
                "VEHICLE_MODEL_MISMATCH",
                "Vehicle models do not match.",
            )

        if not self._same_known(
            left.vehicle.trim,
            right.vehicle.trim,
        ):
            return self._not_comparable(
                "VEHICLE_TRIM_MISMATCH",
                "Vehicle trims do not match.",
            )

        if (
            left.vehicle.fuel_type is not None
            and right.vehicle.fuel_type is not None
            and left.vehicle.fuel_type.lower()
            != right.vehicle.fuel_type.lower()
        ):
            return self._not_comparable(
                "FUEL_TYPE_MISMATCH",
                "Fuel types do not match.",
            )

        if (
            left.vehicle.fuel_type is None
            or right.vehicle.fuel_type is None
        ):
            return self._insufficient(
                "FUEL_TYPE_UNKNOWN",
                "Fuel type is not established for both offers.",
            )

        # --------------------------------------------------------
        # CONTRACT
        # --------------------------------------------------------

        if left.duration != right.duration:
            normalization_required = True

            reasons.append(
                ComparabilityReason(
                    code="TERM_NORMALIZATION_REQUIRED",
                    message=(
                        "Contract duration differs and "
                        "requires normalization."
                    ),
                )
            )

        if left.mileage != right.mileage:
            normalization_required = True

            reasons.append(
                ComparabilityReason(
                    code="MILEAGE_NORMALIZATION_REQUIRED",
                    message=(
                        "Annual mileage differs and "
                        "requires normalization."
                    ),
                )
            )

        # --------------------------------------------------------
        # SERVICES
        # --------------------------------------------------------

        service_result = self._compare_services(
            left,
            right,
        )

        if service_result is not None:
            return service_result

        # --------------------------------------------------------
        # EQUIPMENT
        # --------------------------------------------------------

        equipment_result = self._compare_equipment(
            left,
            right,
        )

        if equipment_result is not None:
            return equipment_result

        # --------------------------------------------------------
        # RESULT
        # --------------------------------------------------------

        if normalization_required:
            return ComparableOfferResult(
                status=NORMALIZATION_REQUIRED,
                reasons=reasons,
            )

        return ComparableOfferResult(
            status=COMPARABLE,
            reasons=reasons,
        )

    # ============================================================
    # SERVICE COMPARISON
    # ============================================================

    def _compare_services(
        self,
        left: CompositeOffer,
        right: CompositeOffer,
    ):

        left_items = {
            (item.category, item.name): item
            for item in left.services.items
        }

        right_items = {
            (item.category, item.name): item
            for item in right.services.items
        }

        keys = set(left_items) | set(right_items)

        for key in keys:

            l_item = left_items.get(key)
            r_item = right_items.get(key)

            # No assertion on either side.
            if l_item is None or r_item is None:
                continue

            # UNKNOWN must not become False.
            if (
                l_item.included is None
                or r_item.included is None
            ):
                continue

            if (
                l_item.included
                != r_item.included
            ):
                return self._not_comparable(
                    "SERVICE_MISMATCH",
                    (
                        f"Service differs: "
                        f"{key[0]} / {key[1]}"
                    ),
                )

        return None

    # ============================================================
    # EQUIPMENT COMPARISON
    # ============================================================

    def _compare_equipment(
        self,
        left: CompositeOffer,
        right: CompositeOffer,
    ):

        left_items = {
            item.name.lower(): item
            for item in left.vehicle.all_equipment
        }

        right_items = {
            item.name.lower(): item
            for item in right.vehicle.all_equipment
        }

        common = (
            set(left_items)
            & set(right_items)
        )

        for name in common:

            l_item = left_items[name]
            r_item = right_items[name]

            if (
                l_item.included is None
                or r_item.included is None
            ):
                continue

            if (
                l_item.included
                != r_item.included
            ):
                return self._not_comparable(
                    "EQUIPMENT_MISMATCH",
                    (
                        f"Equipment differs: "
                        f"{l_item.name}"
                    ),
                )

        return None

    # ============================================================
    # HELPERS
    # ============================================================

    @staticmethod
    def _same_known(
        left,
        right,
    ) -> bool:

        if left is None or right is None:
            return False

        return (
            left.strip().lower()
            == right.strip().lower()
        )

    @staticmethod
    def _not_comparable(
        code: str,
        message: str,
    ) -> ComparableOfferResult:

        return ComparableOfferResult(
            status=NOT_COMPARABLE,
            reasons=[
                ComparabilityReason(
                    code=code,
                    message=message,
                )
            ],
        )

    @staticmethod
    def _insufficient(
        code: str,
        message: str,
    ) -> ComparableOfferResult:

        return ComparableOfferResult(
            status=INSUFFICIENT_EVIDENCE,
            reasons=[
                ComparabilityReason(
                    code=code,
                    message=message,
                )
            ],
        )
