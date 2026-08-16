from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class ManufacturerEquipmentEvidence:
    status: str
    source_type: Optional[str]
    source_url: Optional[str]
    source_text: Optional[str]
    provider_equipment_status: str
    manufacturer_equipment_status: str
    brand: Optional[str] = None
    model: Optional[str] = None
    trim: Optional[str] = None
    fuel_type: Optional[str] = None
    equipment: Tuple[str, ...] = ()
    diagnostic: str = ""


class ManufacturerEquipmentAcquisition:
    """
    Manufacturer Equipment Acquisition V2.

    This layer validates already-discovered manufacturer evidence.
    Discovery itself is injected as a callback so the comparison engine
    never silently searches arbitrary third-party sources.

    Safety rules:
    - provider PUBLISHED evidence wins; manufacturer fallback is not needed;
    - provider NOT_PUBLISHED is preserved as NOT_PUBLISHED;
    - manufacturer evidence is stored separately;
    - brand/model/fuel must match canonical identity;
    - trim/derivative must be explicitly compatible;
    - different model year / trim evidence is rejected;
    - manufacturer evidence never becomes provider-published evidence.
    """

    ALLOWED_SOURCE_TYPES = {
        "MANUFACTURER_MODEL_PAGE",
        "MANUFACTURER_BROCHURE_OR_PDF",
        "MANUFACTURER_SPECIFICATION",
    }

    def __init__(
        self,
        *,
        canonical_identity_builder,
        manufacturer_discovery=None,
    ):
        self.canonical_identity_builder = canonical_identity_builder
        self.manufacturer_discovery = manufacturer_discovery

    def acquire(self, task, offer, provider_equipment_status):
        # Provider-published evidence wins.
        if provider_equipment_status == "PUBLISHED":
            return ManufacturerEquipmentEvidence(
                status="NOT_REQUIRED",
                source_type=None,
                source_url=None,
                source_text=None,
                provider_equipment_status="PUBLISHED",
                manufacturer_equipment_status="NOT_REQUIRED",
                diagnostic=(
                    "Provider-published equipment evidence already exists; "
                    "manufacturer fallback not required."
                ),
            )

        # PARSING_UNRESOLVED is a provider-parser problem, not proof that
        # equipment is unpublished. Manufacturer fallback must not silently
        # bypass a recoverable provider evidence path.
        if provider_equipment_status == "PARSING_UNRESOLVED":
            return ManufacturerEquipmentEvidence(
                status="UNRESOLVED",
                source_type=None,
                source_url=None,
                source_text=None,
                provider_equipment_status="PARSING_UNRESOLVED",
                manufacturer_equipment_status="NOT_ATTEMPTED",
                diagnostic=(
                    "Provider equipment exists but parsing is unresolved; "
                    "provider parsing recovery is required before manufacturer "
                    "fallback may be considered."
                ),
            )

        # V2 only permits manufacturer fallback for explicit NOT_PUBLISHED.
        if provider_equipment_status != "NOT_PUBLISHED":
            return self._unresolved(
                provider_equipment_status,
                "Manufacturer fallback requires explicit NOT_PUBLISHED status.",
            )

        if self.manufacturer_discovery is None:
            return self._unresolved(
                provider_equipment_status,
                "No manufacturer equipment discovery callback configured.",
            )

        candidate = self.manufacturer_discovery(task, offer)

        if not candidate:
            return self._unresolved(
                provider_equipment_status,
                "No manufacturer equipment evidence discovered.",
            )

        source_type = candidate.get("source_type")

        if source_type not in self.ALLOWED_SOURCE_TYPES:
            return self._unresolved(
                provider_equipment_status,
                "Manufacturer evidence source type is not allowed.",
            )

        if candidate.get("different_model_year") is True:
            return self._unresolved(
                provider_equipment_status,
                "Manufacturer evidence belongs to a different model year.",
            )

        target_identity = self.canonical_identity_builder(
            offer.brand,
            offer.model,
            offer.trim,
            offer.fuel_type,
        )

        candidate_identity = self.canonical_identity_builder(
            candidate.get("brand", ""),
            candidate.get("model", ""),
            candidate.get("trim", ""),
            candidate.get("fuel_type", ""),
        )

        if (
            target_identity["brand"] != candidate_identity["brand"]
            or target_identity["model"] != candidate_identity["model"]
            or target_identity["fuel_type"] != candidate_identity["fuel_type"]
        ):
            return self._unresolved(
                provider_equipment_status,
                "Manufacturer evidence does not match canonical brand/model/fuel.",
            )

        variant_status = candidate.get("variant_match_status")

        if variant_status not in {
            "EXACT",
            "EXPLICITLY_COMPATIBLE",
        }:
            return self._unresolved(
                provider_equipment_status,
                "Exact derivative/trim compatibility is not proven.",
            )

        equipment = tuple(
            x.strip()
            for x in candidate.get("equipment", ())
            if isinstance(x, str) and x.strip()
        )

        if not equipment:
            return self._unresolved(
                provider_equipment_status,
                "Manufacturer source contains no safely extracted equipment items.",
            )

        return ManufacturerEquipmentEvidence(
            status="VALIDATED",
            source_type=source_type,
            source_url=candidate.get("source_url"),
            source_text=candidate.get("source_text"),
            provider_equipment_status=provider_equipment_status,
            manufacturer_equipment_status="VALIDATED",
            brand=candidate.get("brand"),
            model=candidate.get("model"),
            trim=candidate.get("trim"),
            fuel_type=candidate.get("fuel_type"),
            equipment=equipment,
            diagnostic=(
                "Exact manufacturer equipment evidence validated separately "
                "from provider-published equipment evidence."
            ),
        )

    @staticmethod
    def _unresolved(provider_status, diagnostic):
        return ManufacturerEquipmentEvidence(
            status="UNRESOLVED",
            source_type=None,
            source_url=None,
            source_text=None,
            provider_equipment_status=provider_status,
            manufacturer_equipment_status="UNRESOLVED",
            diagnostic=diagnostic,
        )
