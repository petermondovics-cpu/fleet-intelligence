from dataclasses import dataclass
from typing import Dict, Tuple

from comparison.service_package_normalizer import (
    ServicePackageNormalizer,
)


SEMANTIC_MATCH = "MATCH"
SEMANTIC_PARTIAL_EQUIVALENCE = "PARTIAL_EQUIVALENCE"
SEMANTIC_DIFFERENCE = "DIFFERENCE"
SEMANTIC_INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


@dataclass(frozen=True)
class ServiceSemanticContradiction:
    code: str
    left_included: object
    right_included: object


@dataclass(frozen=True)
class ServiceSemanticEquivalenceResult:
    status: str
    core_equivalent: bool
    shared_codes: Tuple[str, ...]
    shared_core_codes: Tuple[str, ...]
    left_only_codes: Tuple[str, ...]
    right_only_codes: Tuple[str, ...]
    unresolved_common_codes: Tuple[str, ...]
    left_unknown_wording: Tuple[str, ...]
    right_unknown_wording: Tuple[str, ...]
    contradictions: Tuple[ServiceSemanticContradiction, ...]
    functional_domains: Tuple[Tuple[str, Tuple[str, ...]], ...]
    diagnostic: str

    @property
    def price_comparison_safe(self) -> bool:
        return self.status == SEMANTIC_MATCH


class ServiceSemanticEquivalenceAssessor:
    """
    Service Semantic Equivalence V1.

    Purpose
    -------
    Move beyond raw "left-only/right-only published code" reporting while
    preserving evidence-first comparison safety.

    The current canonical service taxonomy already represents distinct
    service semantics. V1 therefore does NOT fabricate equivalence between
    different canonical codes such as FINANCING and TAXES.

    Instead it:
    - establishes a shared operational/core service baseline;
    - groups codes into functional domains for explainability;
    - distinguishes partial semantic equivalence from total evidence failure;
    - preserves side-only services as unresolved differences, never exclusions;
    - preserves explicit True-vs-False contradictions as hard differences.

    Current core baseline
    ---------------------
    These five functions materially describe the recurring operating package
    and are directly published by both current providers:

        MAINTENANCE
        TYRES
        ROADSIDE_ASSISTANCE
        FLEET_PORTAL
        INSURANCE

    Additional published semantics remain distinct:
        CLAIMS_MANAGEMENT
        FINANCING
        TAXES

    Safety
    ------
    - FINANCING != TAXES.
    - INSURANCE does not automatically imply CLAIMS_MANAGEMENT.
    - missing publication does not mean False.
    - unknown provider wording blocks full semantic match.
    - no service is assigned a HUF value.
    """

    CORE_CODES = frozenset(
        {
            "MAINTENANCE",
            "TYRES",
            "ROADSIDE_ASSISTANCE",
            "FLEET_PORTAL",
            "INSURANCE",
        }
    )

    DOMAIN_BY_CODE = {
        "MAINTENANCE": "VEHICLE_UPTIME",
        "TYRES": "VEHICLE_UPTIME",
        "ROADSIDE_ASSISTANCE": "VEHICLE_UPTIME",
        "INSURANCE": "RISK_PROTECTION",
        "CLAIMS_MANAGEMENT": "RISK_PROTECTION",
        "FLEET_PORTAL": "DIGITAL_ADMINISTRATION",
        "FINANCING": "COMMERCIAL_STRUCTURE",
        "TAXES": "COMMERCIAL_STRUCTURE",
        "MOBILITY": "MOBILITY",
        "REPLACEMENT_CAR": "MOBILITY",
        "FUEL_CARD": "FLEET_OPERATIONS",
    }

    def __init__(self):
        self.normalizer = ServicePackageNormalizer()

    def assess(
        self,
        left_package,
        right_package,
    ) -> ServiceSemanticEquivalenceResult:

        left = self.normalizer.normalize(
            left_package
        )

        right = self.normalizer.normalize(
            right_package
        )

        lmap = left.by_code()
        rmap = right.by_code()

        common = set(lmap) & set(rmap)

        contradictions = []
        unresolved_common = []
        shared_true = []

        for code in sorted(common):
            lvalue = lmap[code].included
            rvalue = rmap[code].included

            if (
                lvalue is not None
                and rvalue is not None
                and lvalue != rvalue
            ):
                contradictions.append(
                    ServiceSemanticContradiction(
                        code=code,
                        left_included=lvalue,
                        right_included=rvalue,
                    )
                )
                continue

            if (
                lvalue is None
                or rvalue is None
            ):
                unresolved_common.append(
                    code
                )
                continue

            if (
                lvalue is True
                and rvalue is True
            ):
                shared_true.append(
                    code
                )

        left_only = tuple(
            sorted(
                set(lmap)
                - set(rmap)
            )
        )

        right_only = tuple(
            sorted(
                set(rmap)
                - set(lmap)
            )
        )

        shared_codes = tuple(
            sorted(
                shared_true
            )
        )

        shared_core = tuple(
            sorted(
                self.CORE_CODES
                & set(shared_true)
            )
        )

        core_equivalent = (
            set(shared_core)
            == set(self.CORE_CODES)
        )

        domains = self._domains(
            set(lmap)
            | set(rmap)
        )

        if contradictions:
            status = (
                SEMANTIC_DIFFERENCE
            )

            diagnostic = (
                "One or more canonical service semantics have an explicit "
                "inclusion contradiction."
            )

        elif (
            left.unknown_items
            or right.unknown_items
            or unresolved_common
        ):
            status = (
                SEMANTIC_INSUFFICIENT_EVIDENCE
            )

            diagnostic = (
                "Service semantics cannot be fully assessed because unknown "
                "wording or unresolved common-service evidence remains."
            )

        elif (
            core_equivalent
            and not left_only
            and not right_only
        ):
            status = SEMANTIC_MATCH

            diagnostic = (
                "Both providers explicitly publish the same canonical "
                "service semantics, including the full core baseline."
            )

        elif core_equivalent:
            status = (
                SEMANTIC_PARTIAL_EQUIVALENCE
            )

            diagnostic = (
                "The full recurring operational/core service baseline is "
                "explicitly shared, but one or more additional published "
                "service semantics remain one-sided and cannot be assumed "
                "equivalent or absent."
            )

        else:
            status = (
                SEMANTIC_INSUFFICIENT_EVIDENCE
            )

            missing_left = sorted(
                self.CORE_CODES
                - {
                    code
                    for code, item
                    in lmap.items()
                    if item.included is True
                }
            )

            missing_right = sorted(
                self.CORE_CODES
                - {
                    code
                    for code, item
                    in rmap.items()
                    if item.included is True
                }
            )

            diagnostic = (
                "The shared operational/core service baseline is not "
                "explicitly established for both providers. "
                f"Left unresolved core: {missing_left}; "
                f"right unresolved core: {missing_right}."
            )

        return (
            ServiceSemanticEquivalenceResult(
                status=status,
                core_equivalent=core_equivalent,
                shared_codes=shared_codes,
                shared_core_codes=shared_core,
                left_only_codes=left_only,
                right_only_codes=right_only,
                unresolved_common_codes=tuple(
                    unresolved_common
                ),
                left_unknown_wording=(
                    left.unknown_items
                ),
                right_unknown_wording=(
                    right.unknown_items
                ),
                contradictions=tuple(
                    contradictions
                ),
                functional_domains=domains,
                diagnostic=diagnostic,
            )
        )

    def _domains(
        self,
        codes,
    ):
        grouped: Dict[
            str,
            list,
        ] = {}

        for code in sorted(
            codes
        ):
            domain = (
                self.DOMAIN_BY_CODE
                .get(
                    code,
                    "OTHER",
                )
            )

            grouped.setdefault(
                domain,
                [],
            ).append(
                code
            )

        return tuple(
            (
                domain,
                tuple(values),
            )
            for domain, values
            in sorted(
                grouped.items()
            )
        )
