from dataclasses import dataclass, field
from typing import List, Optional


# ============================================================
# VEHICLE SPECIFICATION V1
#
# Evidence-first model.
#
# IMPORTANT:
# - OBSERVED means the source explicitly supports the value.
# - INFERRED is reserved for later, explicitly controlled
#   inference logic.
# - UNKNOWN means the source does not support the value.
#
# UNKNOWN must never be silently converted to "not included".
# ============================================================


EVIDENCE_OBSERVED = "OBSERVED"
EVIDENCE_INFERRED = "INFERRED"
EVIDENCE_UNKNOWN = "UNKNOWN"

EVIDENCE_STATUSES = {
    EVIDENCE_OBSERVED,
    EVIDENCE_INFERRED,
    EVIDENCE_UNKNOWN,
}


@dataclass(frozen=True)
class VehicleEvidence:
    """
    Evidence attached to a vehicle specification fact.

    source_url:
        URL where the fact was observed.

    source_text:
        Small source excerpt supporting the fact.

    status:
        OBSERVED / INFERRED / UNKNOWN.
    """

    status: str
    source_url: str = ""
    source_text: str = ""

    def __post_init__(self):
        if self.status not in EVIDENCE_STATUSES:
            raise ValueError(
                f"Invalid evidence status: {self.status}"
            )

        if self.status == EVIDENCE_UNKNOWN:
            if self.source_url or self.source_text:
                raise ValueError(
                    "UNKNOWN evidence cannot contain "
                    "source data."
                )


@dataclass(frozen=True)
class EquipmentItem:
    """
    One equipment item.

    included:
        True  -> explicitly included.
        False -> explicitly excluded.
        None  -> not established.

    standard:
        True  -> standard equipment.
        False -> optional equipment.
        None  -> standard/optional status unknown.
    """

    name: str
    category: str
    included: Optional[bool]
    standard: Optional[bool]
    evidence: VehicleEvidence

    def __post_init__(self):
        if not self.name.strip():
            raise ValueError(
                "Equipment item name cannot be empty."
            )

        if not self.category.strip():
            raise ValueError(
                "Equipment category cannot be empty."
            )

        if (
            self.evidence.status
            == EVIDENCE_UNKNOWN
            and (
                self.included is not None
                or self.standard is not None
            )
        ):
            raise ValueError(
                "UNKNOWN equipment evidence cannot "
                "contain an asserted inclusion or "
                "standard/optional classification."
            )

        if (
            self.standard is True
            and self.included is False
        ):
            raise ValueError(
                "Standard equipment cannot be "
                "explicitly excluded."
            )


@dataclass(frozen=True)
class VehicleSpecification:
    """
    Structured vehicle specification V1.

    Only explicitly supported information is stored as
    observed. Missing source information remains UNKNOWN.

    This model deliberately does not calculate a monetary
    value for equipment yet.
    """

    brand: Optional[str]
    model: Optional[str]
    trim: Optional[str]
    fuel_type: Optional[str]

    brand_evidence: VehicleEvidence
    model_evidence: VehicleEvidence
    trim_evidence: VehicleEvidence
    fuel_evidence: VehicleEvidence

    standard_equipment: List[EquipmentItem] = field(
        default_factory=list
    )

    optional_equipment: List[EquipmentItem] = field(
        default_factory=list
    )

    def __post_init__(self):
        self._validate_field(
            "brand",
            self.brand,
            self.brand_evidence,
        )

        self._validate_field(
            "model",
            self.model,
            self.model_evidence,
        )

        self._validate_field(
            "trim",
            self.trim,
            self.trim_evidence,
        )

        self._validate_field(
            "fuel_type",
            self.fuel_type,
            self.fuel_evidence,
        )

        for item in self.standard_equipment:
            if item.standard is not True:
                raise ValueError(
                    "standard_equipment may contain only "
                    "items explicitly classified as standard."
                )

        for item in self.optional_equipment:
            if item.standard is not False:
                raise ValueError(
                    "optional_equipment may contain only "
                    "items explicitly classified as optional."
                )

    @staticmethod
    def _validate_field(
        name: str,
        value: Optional[str],
        evidence: VehicleEvidence,
    ) -> None:

        if value is None:
            if evidence.status != EVIDENCE_UNKNOWN:
                raise ValueError(
                    f"{name} is None but evidence is not UNKNOWN."
                )
            return

        if not value.strip():
            raise ValueError(
                f"{name} cannot be empty."
            )

    @property
    def all_equipment(self) -> List[EquipmentItem]:
        return [
            *self.standard_equipment,
            *self.optional_equipment,
        ]

    @property
    def standard_equipment_count(self) -> int:
        return len(
            self.standard_equipment
        )

    @property
    def optional_equipment_count(self) -> int:
        return len(
            self.optional_equipment
        )
