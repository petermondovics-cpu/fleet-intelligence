from dataclasses import dataclass
from typing import Optional, Tuple

from comparison.normalized_vehicle_identity import VehicleIdentityNormalizer
from comparison.evidence_gap_resolver import (
    EvidenceGapResolver,
    EvidenceResolutionAction,
)


ACQ_READY = "ACQUISITION_PLAN_READY"
ACQ_NO_GAPS = "NO_EVIDENCE_GAPS"
ACQ_MANUAL_REVIEW = "MANUAL_REVIEW_REQUIRED"


@dataclass(frozen=True)
class AcquisitionTask:
    provider: str
    action_type: str
    target_dimension: str
    priority: int
    blocker_code: str
    strategy: str
    allowed_sources: Tuple[str, ...]
    prohibited_sources: Tuple[str, ...]
    canonical_vehicle_key: str
    message: str


@dataclass(frozen=True)
class EvidenceAcquisitionPlan:
    status: str
    tasks: Tuple[AcquisitionTask, ...]

    @property
    def task_count(self) -> int:
        return len(self.tasks)

    def by_priority(self):
        return tuple(
            sorted(
                self.tasks,
                key=lambda x: (
                    x.priority,
                    x.target_dimension,
                    x.provider,
                    x.action_type,
                ),
            )
        )


class EvidenceAcquisitionOrchestrator:
    """
    Evidence Acquisition Orchestrator V2.

    Converts the generic EvidenceGapResolver plan into provider-specific
    acquisition tasks.

    This layer PLANS acquisition. It does not silently mutate offers and
    it does not treat a search result as evidence until a downstream
    parser validates and attaches explicit source evidence.

    Core safety rules:
    - provider-published evidence is preferred for commercial conditions;
    - manufacturer sources may enrich vehicle/equipment specification,
      but cannot silently overwrite provider-advertised commercial terms;
    - contract normalization accepts only observed PRICED offers;
    - Ayvens duration/mileage quote controls are explicitly prohibited as
      pricing evidence;
    - down payment must be explicit; no default percentage is allowed;
    - third-party sources are discovery-only in V1 unless separately
      validated by a future source-trust policy.
    """

    def __init__(self):
        self.gaps = EvidenceGapResolver()
        self.vehicle_identity = VehicleIdentityNormalizer()

    def plan(
        self,
        full_comparison_result,
        left,
        right,
    ) -> EvidenceAcquisitionPlan:

        gap_plan = self.gaps.resolve(
            full_comparison_result
        )

        if not gap_plan.actions:
            return EvidenceAcquisitionPlan(
                status=ACQ_NO_GAPS,
                tasks=(),
            )

        tasks = []

        for action in gap_plan.actions:
            tasks.extend(
                self._expand_action(
                    action,
                    left,
                    right,
                )
            )

        tasks = self._deduplicate(tasks)

        status = (
            ACQ_MANUAL_REVIEW
            if any(
                task.action_type
                == "REJECT_OR_REVIEW_HARD_MISMATCH"
                for task in tasks
            )
            else ACQ_READY
        )

        return EvidenceAcquisitionPlan(
            status=status,
            tasks=tuple(tasks),
        )

    def _expand_action(
        self,
        action: EvidenceResolutionAction,
        left,
        right,
    ):
        if action.action_type == "FIND_PROVIDER_SERVICE_DOCUMENTATION":
            return [
                self._provider_task(
                    left,
                    action,
                    "SEARCH_PROVIDER_SERVICE_DOCUMENTATION",
                    (
                        "PROVIDER_OFFER_PAGE",
                        "PROVIDER_SERVICE_PAGE",
                        "PROVIDER_TERMS_OR_PDF",
                    ),
                ),
                self._provider_task(
                    right,
                    action,
                    "SEARCH_PROVIDER_SERVICE_DOCUMENTATION",
                    (
                        "PROVIDER_OFFER_PAGE",
                        "PROVIDER_SERVICE_PAGE",
                        "PROVIDER_TERMS_OR_PDF",
                    ),
                ),
            ]

        if action.action_type == "VERIFY_RIGHT_PROVIDER_SERVICE":
            return [
                self._provider_task(
                    right,
                    action,
                    "VERIFY_CANONICAL_SERVICE",
                    (
                        "PROVIDER_OFFER_PAGE",
                        "PROVIDER_SERVICE_PAGE",
                        "PROVIDER_TERMS_OR_PDF",
                    ),
                )
            ]

        if action.action_type == "VERIFY_LEFT_PROVIDER_SERVICE":
            return [
                self._provider_task(
                    left,
                    action,
                    "VERIFY_CANONICAL_SERVICE",
                    (
                        "PROVIDER_OFFER_PAGE",
                        "PROVIDER_SERVICE_PAGE",
                        "PROVIDER_TERMS_OR_PDF",
                    ),
                )
            ]

        if action.action_type == "NORMALIZE_SERVICE_WORDING":
            return [
                self._provider_task(
                    left,
                    action,
                    "REVIEW_SERVICE_WORDING",
                    (
                        "PROVIDER_OFFER_PAGE",
                        "PROVIDER_SERVICE_PAGE",
                        "PROVIDER_TERMS_OR_PDF",
                    ),
                ),
                self._provider_task(
                    right,
                    action,
                    "REVIEW_SERVICE_WORDING",
                    (
                        "PROVIDER_OFFER_PAGE",
                        "PROVIDER_SERVICE_PAGE",
                        "PROVIDER_TERMS_OR_PDF",
                    ),
                ),
            ]

        if action.action_type == "FIND_EQUIPMENT_SPECIFICATION_SOURCE":
            return [
                self._equipment_task(left, action),
                self._equipment_task(right, action),
            ]

        if action.action_type == "EXTEND_EQUIPMENT_CANONICAL_MAP":
            return [
                self._equipment_task(left, action),
                self._equipment_task(right, action),
            ]

        if action.action_type == "VERIFY_VARIANT_EQUIVALENCE":
            return [
                self._equipment_task(left, action),
                self._equipment_task(right, action),
            ]

        if action.action_type == "COLLECT_OBSERVED_PRICED_CONTRACT_VARIANT":
            return [
                self._contract_task(left, action),
                self._contract_task(right, action),
            ]

        if action.action_type == "FIND_EXPLICIT_DOWN_PAYMENT_CONDITION":
            return [
                self._financial_task(left, action),
                self._financial_task(right, action),
            ]

        if action.action_type in {
            "NORMALIZE_DOWN_PAYMENT_ECONOMICS",
            "NORMALIZE_ADDITIONAL_FEES",
        }:
            return [
                self._financial_task(left, action),
                self._financial_task(right, action),
            ]

        if action.action_type == "DEFINE_EQUIPMENT_VALUE_POLICY":
            return [
                AcquisitionTask(
                    provider="INTERNAL",
                    action_type=action.action_type,
                    target_dimension=action.target_dimension,
                    priority=action.priority,
                    blocker_code=action.blocker_code,
                    strategy="BUSINESS_POLICY_REVIEW",
                    allowed_sources=("INTERNAL_APPROVED_POLICY",),
                    prohibited_sources=("UNAPPROVED_HEURISTIC",),
                    canonical_vehicle_key=self._vehicle_key(left),
                    message=action.message,
                )
            ]

        if action.action_type == "REJECT_OR_REVIEW_HARD_MISMATCH":
            return [
                AcquisitionTask(
                    provider="INTERNAL",
                    action_type=action.action_type,
                    target_dimension=action.target_dimension,
                    priority=action.priority,
                    blocker_code=action.blocker_code,
                    strategy="MANUAL_SOURCE_REVIEW",
                    allowed_sources=(
                        "ORIGINAL_PROVIDER_EVIDENCE",
                    ),
                    prohibited_sources=(
                        "FUZZY_MATCH_OVERRIDE",
                        "SYNTHETIC_CORRECTION",
                    ),
                    canonical_vehicle_key=self._vehicle_key(left),
                    message=action.message,
                )
            ]

        return []

    def _contract_task(
        self,
        side,
        action,
    ):
        provider = side.composite.provider

        prohibited = [
            "UNPRICED_QUOTE_CONTROL",
            "SYNTHETIC_PRICE_FACTOR",
            "THIRD_PARTY_UNVALIDATED_PRICE",
        ]

        if provider.strip().casefold() == "ayvens":
            prohibited.append(
                "AYVENS_DURATION_MILEAGE_SLIDER"
            )

        return AcquisitionTask(
            provider=provider,
            action_type=action.action_type,
            target_dimension="CONTRACT",
            priority=action.priority,
            blocker_code=action.blocker_code,
            strategy=(
                "DISCOVER_SAME_PROVIDER_SAME_CANONICAL_VEHICLE_"
                "OBSERVED_PRICED_OFFER"
            ),
            allowed_sources=(
                "PROVIDER_PRICED_OFFER_PAGE",
                "PROVIDER_PRICED_OFFER_ARCHIVE",
            ),
            prohibited_sources=tuple(prohibited),
            canonical_vehicle_key=self._vehicle_key(side),
            message=(
                action.message
                + " Preserve provider, canonical vehicle identity and "
                "the non-normalized contract dimension."
            ),
        )

    def _financial_task(
        self,
        side,
        action,
    ):
        return AcquisitionTask(
            provider=side.composite.provider,
            action_type=action.action_type,
            target_dimension="FINANCIAL",
            priority=action.priority,
            blocker_code=action.blocker_code,
            strategy="SEARCH_EXPLICIT_PROVIDER_FINANCIAL_CONDITION",
            allowed_sources=(
                "PROVIDER_OFFER_PAGE",
                "PROVIDER_TERMS_OR_PDF",
                "PROVIDER_QUOTE_DOCUMENT",
            ),
            prohibited_sources=(
                "DEFAULT_20_PERCENT_ASSUMPTION",
                "INDUSTRY_CUSTOM_ASSUMPTION",
                "THIRD_PARTY_UNVALIDATED_FINANCIAL_TERM",
            ),
            canonical_vehicle_key=self._vehicle_key(side),
            message=action.message,
        )

    def _equipment_task(
        self,
        side,
        action,
    ):
        return AcquisitionTask(
            provider=side.composite.provider,
            action_type=action.action_type,
            target_dimension="EQUIPMENT",
            priority=action.priority,
            blocker_code=action.blocker_code,
            strategy="PROVIDER_FIRST_THEN_MANUFACTURER_SPEC",
            allowed_sources=(
                "PROVIDER_OFFER_PAGE",
                "PROVIDER_SPECIFICATION",
                "MANUFACTURER_MODEL_PAGE",
                "MANUFACTURER_BROCHURE_OR_PDF",
            ),
            prohibited_sources=(
                "THIRD_PARTY_UNVALIDATED_SPEC",
                "DIFFERENT_MODEL_YEAR_SPEC",
                "DIFFERENT_TRIM_SPEC",
            ),
            canonical_vehicle_key=self._vehicle_key(side),
            message=(
                action.message
                + " Manufacturer evidence must be attached as a distinct "
                "source type and must match the exact derivative/model year "
                "where observable."
            ),
        )

    def _provider_task(
        self,
        side,
        action,
        strategy,
        allowed_sources,
    ):
        return AcquisitionTask(
            provider=side.composite.provider,
            action_type=action.action_type,
            target_dimension=action.target_dimension,
            priority=action.priority,
            blocker_code=action.blocker_code,
            strategy=strategy,
            allowed_sources=tuple(allowed_sources),
            prohibited_sources=(
                "THIRD_PARTY_UNVALIDATED_COMMERCIAL_TERM",
                "ASSUMED_EXCLUSION_FROM_NON_PUBLICATION",
            ),
            canonical_vehicle_key=self._vehicle_key(side),
            message=action.message,
        )

    def _vehicle_key(self, side):
        vehicle = side.composite.vehicle

        normalized = self.vehicle_identity.normalize(
            vehicle.brand,
            vehicle.model,
            getattr(vehicle, "trim", "") or "",
            vehicle.fuel_type,
        )

        return "|".join(
            [
                normalized.brand.strip().upper(),
                normalized.model.strip().upper(),
                normalized.fuel_type.strip().upper(),
            ]
        )

    @staticmethod
    def _deduplicate(tasks):
        unique = []
        seen = set()

        for task in tasks:
            key = (
                task.provider,
                task.action_type,
                task.target_dimension,
                task.blocker_code,
                task.strategy,
                task.canonical_vehicle_key,
            )

            if key in seen:
                continue

            seen.add(key)
            unique.append(task)

        return unique
