from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple


@dataclass(frozen=True)
class CanonicalService:
    """
    Canonical service observation.

    included:
        True / False / None is preserved from the source ServiceItem.

    source_name:
        Original provider wording, kept for auditability.
    """

    code: str
    included: object
    source_name: str
    source_category: str


@dataclass(frozen=True)
class ServiceNormalizationResult:
    """
    Normalized provider service package.

    unknown_items are never silently discarded or treated as excluded.
    """

    services: Tuple[CanonicalService, ...]
    unknown_items: Tuple[str, ...]

    @property
    def fully_normalized(self) -> bool:
        return len(self.unknown_items) == 0

    def by_code(self) -> Dict[str, CanonicalService]:
        return {
            item.code: item
            for item in self.services
        }


class ServicePackageNormalizer:
    """
    Service Package Normalization V1.

    Purpose:
    map provider-specific service wording to a common semantic layer.

    Safety rules:
    - no unknown service becomes False;
    - original source wording is preserved;
    - one provider phrase may map to multiple canonical service codes;
    - normalization does not assign a monetary value.
    """

    # Exact / normalized aliases learned from current Arval + Ayvens pages.
    #
    # Multiple codes are allowed where one provider phrase bundles
    # several service concepts.
    ALIASES = {
        # ---------------- AYVENS ----------------
        "teljes körű karbantartás": (
            "MAINTENANCE",
        ),
        "téli-, nyári gumiabroncs": (
            "TYRES",
        ),
        "assistance szolgáltatás": (
            "ROADSIDE_ASSISTANCE",
        ),
        "myayvens online ügyintézési rendszer": (
            "FLEET_PORTAL",
        ),
        "vonatkozó adók": (
            "TAXES",
        ),
        "biztosítási csomag": (
            "INSURANCE",
        ),

        # ---------------- ARVAL ----------------
        "biztosítás és káresemény-kezelés": (
            "INSURANCE",
            "CLAIMS_MANAGEMENT",
        ),
        "finanszírozás": (
            "FINANCING",
        ),
        "gumiabroncs kezelés": (
            "TYRES",
        ),
        "karbantartás és javítás": (
            "MAINTENANCE",
        ),
        "közúti segítségnyújtás": (
            "ROADSIDE_ASSISTANCE",
        ),
        "my arval": (
            "FLEET_PORTAL",
        ),

        # ---------------- GENERIC / FUTURE ----------------
        "üzemanyagkártya": (
            "FUEL_CARD",
        ),
        "üzemanyag kártya": (
            "FUEL_CARD",
        ),
        "csereautó": (
            "REPLACEMENT_CAR",
        ),
        "kötelező biztosítás": (
            "INSURANCE",
        ),
        "casco": (
            "INSURANCE",
        ),
    }

    def normalize(
        self,
        service_package,
    ) -> ServiceNormalizationResult:

        canonical: Dict[str, CanonicalService] = {}
        unknown: List[str] = []

        for item in service_package.items:

            key = self._normalize(
                item.name
            )

            codes = self.ALIASES.get(
                key
            )

            if codes is None:
                unknown.append(
                    item.name
                )
                continue

            for code in codes:

                existing = canonical.get(
                    code
                )

                observation = CanonicalService(
                    code=code,
                    included=item.included,
                    source_name=item.name,
                    source_category=item.category,
                )

                if existing is None:
                    canonical[code] = observation
                    continue

                # Same provider package may expose aliases that collapse
                # to the same canonical service. Contradictory explicit
                # observations are unsafe and must fail loudly.
                if (
                    existing.included is not None
                    and observation.included is not None
                    and existing.included
                    != observation.included
                ):
                    raise ValueError(
                        "Contradictory service observations for "
                        f"{code}: "
                        f"{existing.source_name!r} vs "
                        f"{observation.source_name!r}"
                    )

                # Prefer explicit True/False over None.
                if (
                    existing.included is None
                    and observation.included is not None
                ):
                    canonical[code] = observation

        return ServiceNormalizationResult(
            services=tuple(
                canonical.values()
            ),
            unknown_items=tuple(
                unknown
            ),
        )

    @staticmethod
    def _normalize(
        text: str,
    ) -> str:

        return " ".join(
            text.casefold()
            .replace("–", "-")
            .split()
        )
