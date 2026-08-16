from dataclasses import dataclass
from typing import Optional, Tuple
from comparison.equipment_value_normalizer import EquipmentValueComparison, EquipmentValueNormalizer

VARIANT_EQUIVALENT = "EQUIVALENT"
VARIANT_VALUE_DIFFERENCE = "VALUE_DIFFERENCE"
VARIANT_NOT_EQUIVALENT = "NOT_EQUIVALENT"
VARIANT_INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"

@dataclass(frozen=True)
class VariantEquivalenceResult:
    status: str
    identity_status: str
    trim_differs: bool
    left_equipment_status: str
    right_equipment_status: str
    equipment_comparison: Optional[EquipmentValueComparison]
    reasons: Tuple[str, ...]

    @property
    def price_comparison_safe(self) -> bool:
        return self.status == VARIANT_EQUIVALENT

class VariantEquivalenceAssessor:
    """Variant Equivalence Assessment V1.

    Equipment scores are comparison weights only, never HUF.
    Unknown or incomplete evidence cannot prove equivalence.
    """

    def __init__(self):
        self.equipment_value = EquipmentValueNormalizer()

    def assess(self, left, right, identity_status: str, left_items=None,
               right_items=None, left_equipment_status=None,
               right_equipment_status=None) -> VariantEquivalenceResult:
        lc, rc = left.composite, right.composite
        trim_differs = ((lc.vehicle.trim or "").strip().casefold() !=
                        (rc.vehicle.trim or "").strip().casefold())
        ls = left_equipment_status or self._evidence_status(left)
        rs = right_equipment_status or self._evidence_status(right)

        if identity_status != "COMPARABLE":
            return self._result(VARIANT_NOT_EQUIVALENT, identity_status,
                                trim_differs, ls, rs, None,
                                "Canonical vehicle identity is not comparable.")

        if not trim_differs:
            return self._result(VARIANT_EQUIVALENT, identity_status, False,
                                ls, rs, None,
                                "Canonical identity and advertised trim/version match.")

        if not (self._usable(ls) and self._usable(rs)):
            return self._result(
                VARIANT_INSUFFICIENT_EVIDENCE, identity_status, True, ls, rs, None,
                "Advertised trim/version differs and complete usable equipment "
                "evidence is not available for both sides.")

        left_items = lc.vehicle.all_equipment if left_items is None else left_items
        right_items = rc.vehicle.all_equipment if right_items is None else right_items
        comparison = self.equipment_value.compare(left_items, right_items)

        if not comparison.fully_scored:
            return self._result(
                VARIANT_INSUFFICIENT_EVIDENCE, identity_status, True, ls, rs,
                comparison, "One or more equipment items have no canonical valuation rule.")

        if comparison.score_delta != 0:
            return self._result(
                VARIANT_VALUE_DIFFERENCE, identity_status, True, ls, rs,
                comparison, "Canonical equipment value scores differ; V1 does not "
                "convert the difference to HUF.")

        return self._result(
            VARIANT_EQUIVALENT, identity_status, True, ls, rs, comparison,
            "Different advertised trim/version has equal fully-scored canonical "
            "equipment value.")

    @staticmethod
    def _result(status, identity, trim_differs, ls, rs, comparison, reason):
        return VariantEquivalenceResult(status, identity, trim_differs, ls, rs,
                                        comparison, (reason,))

    @staticmethod
    def _evidence_status(side) -> str:
        return ("VALIDATED" if getattr(side.equipment_evidence,
                                       "fully_comparable", False)
                else "INSUFFICIENT_EVIDENCE")

    @staticmethod
    def _usable(status: str) -> bool:
        return status in {"VALIDATED", "PUBLISHED", "MANUFACTURER_VALIDATED"}
