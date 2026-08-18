from dataclasses import dataclass
from time import perf_counter
from typing import Any, Dict, Optional, Tuple


EXECUTOR_READY = "EXECUTOR_READY"
EXECUTOR_PARTIAL = "EXECUTOR_PARTIAL"
EXECUTOR_BLOCKED = "EXECUTOR_BLOCKED"


@dataclass(frozen=True)
class EvidenceCandidate:
    provider: str
    target_dimension: str
    action_type: str
    blocker_code: str

    status: str
    candidate_type: str

    canonical_vehicle_key: str

    source_type: Optional[str]
    source_url: Optional[str]
    source_text: Optional[str]

    payload: Dict[str, Any]
    diagnostic: str

    @property
    def accepted(self) -> bool:
        return self.status == "VALIDATED"


@dataclass(frozen=True)
class AcquisitionTaskTiming:
    provider: str
    target_dimension: str
    action_type: str
    seconds: float


@dataclass(frozen=True)
class AcquisitionExecutionResult:
    status: str
    candidates: Tuple[EvidenceCandidate, ...]
    task_timings: Tuple[AcquisitionTaskTiming, ...] = ()

    @property
    def candidate_count(self) -> int:
        return len(self.candidates)

    @property
    def validated_count(self) -> int:
        return sum(
            1
            for item in self.candidates
            if item.accepted
        )


class AcquisitionExecutor:
    """
    Acquisition Executor V1.

    IMPORTANT:
    This executor does NOT automatically turn discoveries into trusted
    model evidence.

    It executes provider-specific acquisition tasks and returns
    EvidenceCandidate records that downstream validators may accept,
    reject, or preserve as unresolved.

    V1 supports execution hooks for:
    - provider offer/page evidence already available in the browser;
    - provider service page candidate extraction;
    - provider financial condition candidate extraction;
    - provider equipment-page candidate extraction;
    - observed priced contract variants supplied by a discovery callback.

    External search/navigation itself is callback-driven in V1 so the
    executor remains testable and does not invent network results.

    Safety rules:
    - prohibited source types are rejected;
    - Ayvens slider metadata cannot produce a priced-contract candidate;
    - no silent 20% down-payment candidate;
    - manufacturer equipment may be a candidate, but stays a distinct
      source type;
    - missing data returns UNRESOLVED, not empty/false evidence.
    """

    def __init__(
        self,
        *,
        contract_discovery=None,
        service_discovery=None,
        financial_discovery=None,
        equipment_discovery=None,
    ):
        self.contract_discovery = contract_discovery
        self.service_discovery = service_discovery
        self.financial_discovery = financial_discovery
        self.equipment_discovery = equipment_discovery

    def execute_plan(
        self,
        plan,
    ) -> AcquisitionExecutionResult:

        candidates = []
        task_timings = []

        for task in plan.by_priority():
            started = perf_counter()

            try:
                candidates.append(
                    self.execute_task(task)
                )
            finally:
                task_timings.append(
                    AcquisitionTaskTiming(
                        provider=task.provider,
                        target_dimension=(
                            task.target_dimension
                        ),
                        action_type=task.action_type,
                        seconds=round(
                            perf_counter()
                            - started,
                            3,
                        ),
                    )
                )

        if not candidates:
            status = EXECUTOR_READY

        elif all(
            item.status == "UNRESOLVED"
            for item in candidates
        ):
            status = EXECUTOR_BLOCKED

        elif any(
            item.status == "VALIDATED"
            for item in candidates
        ):
            status = EXECUTOR_PARTIAL

        else:
            status = EXECUTOR_PARTIAL

        return AcquisitionExecutionResult(
            status=status,
            candidates=tuple(candidates),
            task_timings=tuple(task_timings),
        )

    def execute_task(
        self,
        task,
    ) -> EvidenceCandidate:

        if task.target_dimension == "CONTRACT":
            return self._execute_contract(task)

        if task.target_dimension == "FINANCIAL":
            return self._execute_financial(task)

        if task.target_dimension == "SERVICES":
            return self._execute_services(task)

        if task.target_dimension == "EQUIPMENT":
            return self._execute_equipment(task)

        return self._unresolved(
            task,
            "Unsupported acquisition task dimension in V1.",
        )

    # ========================================================
    # CONTRACT
    # ========================================================

    def _execute_contract(
        self,
        task,
    ) -> EvidenceCandidate:

        if self.contract_discovery is None:
            return self._unresolved(
                task,
                "No contract discovery callback configured.",
            )

        raw = self.contract_discovery(
            task
        )

        if raw is None:
            return self._unresolved(
                task,
                "No observed priced contract variant discovered.",
            )

        source_type = raw.get(
            "source_type"
        )

        if source_type in task.prohibited_sources:
            return self._rejected(
                task,
                source_type,
                raw,
                "Discovered contract source type is prohibited.",
            )

        if source_type not in task.allowed_sources:
            return self._rejected(
                task,
                source_type,
                raw,
                "Discovered contract source type is not allowed.",
            )

        # Strong V1 guard:
        # priced contract evidence needs explicit observed price +
        # duration + mileage.
        fee = raw.get(
            "monthly_fee"
        )
        duration = raw.get(
            "duration"
        )
        mileage = raw.get(
            "mileage"
        )

        if (
            fee is None
            or duration is None
            or mileage is None
        ):
            return self._rejected(
                task,
                source_type,
                raw,
                "Priced contract candidate lacks fee/duration/mileage.",
            )

        if fee <= 0:
            return self._rejected(
                task,
                source_type,
                raw,
                "Priced contract candidate has invalid monthly fee.",
            )

        return self._validated(
            task,
            "OBSERVED_PRICED_CONTRACT_VARIANT",
            source_type,
            raw,
            (
                "Observed priced contract candidate contains explicit "
                "monthly fee, duration and mileage."
            ),
        )

    # ========================================================
    # FINANCIAL
    # ========================================================

    def _execute_financial(
        self,
        task,
    ) -> EvidenceCandidate:

        if self.financial_discovery is None:
            return self._unresolved(
                task,
                "No financial discovery callback configured.",
            )

        raw = self.financial_discovery(
            task
        )

        if raw is None:
            return self._unresolved(
                task,
                "No explicit financial condition discovered.",
            )

        source_type = raw.get(
            "source_type"
        )

        if source_type in task.prohibited_sources:
            return self._rejected(
                task,
                source_type,
                raw,
                "Financial source type is prohibited.",
            )

        if source_type not in task.allowed_sources:
            return self._rejected(
                task,
                source_type,
                raw,
                "Financial source type is not allowed.",
            )

        percent = raw.get(
            "down_payment_percent"
        )
        amount = raw.get(
            "down_payment_amount"
        )

        if (
            percent is None
            and amount is None
        ):
            return self._rejected(
                task,
                source_type,
                raw,
                "No explicit down-payment value found.",
            )

        if (
            percent is not None
            and (
                percent < 0
                or percent > 100
            )
        ):
            return self._rejected(
                task,
                source_type,
                raw,
                "Down-payment percentage is out of range.",
            )

        if (
            amount is not None
            and amount < 0
        ):
            return self._rejected(
                task,
                source_type,
                raw,
                "Down-payment amount is negative.",
            )

        return self._validated(
            task,
            "EXPLICIT_DOWN_PAYMENT_CONDITION",
            source_type,
            raw,
            "Explicit provider down-payment condition discovered.",
        )

    # ========================================================
    # SERVICES
    # ========================================================

    def _execute_services(
        self,
        task,
    ) -> EvidenceCandidate:

        if self.service_discovery is None:
            return self._unresolved(
                task,
                "No service discovery callback configured.",
            )

        raw = self.service_discovery(
            task
        )

        if raw is None:
            return self._unresolved(
                task,
                "No provider service documentation discovered.",
            )

        source_type = raw.get(
            "source_type"
        )

        if source_type in task.prohibited_sources:
            return self._rejected(
                task,
                source_type,
                raw,
                "Service source type is prohibited.",
            )

        if source_type not in task.allowed_sources:
            return self._rejected(
                task,
                source_type,
                raw,
                "Service source type is not allowed.",
            )

        services = raw.get(
            "services"
        )

        if not services:
            return self._rejected(
                task,
                source_type,
                raw,
                "No explicit service assertions found.",
            )

        return self._validated(
            task,
            "PROVIDER_SERVICE_ASSERTIONS",
            source_type,
            raw,
            "Provider service documentation produced explicit assertions.",
        )

    # ========================================================
    # EQUIPMENT
    # ========================================================

    def _execute_equipment(
        self,
        task,
    ) -> EvidenceCandidate:

        if self.equipment_discovery is None:
            return self._unresolved(
                task,
                "No equipment discovery callback configured.",
            )

        raw = self.equipment_discovery(
            task
        )

        if raw is None:
            return self._unresolved(
                task,
                "No equipment specification discovered.",
            )

        source_type = raw.get(
            "source_type"
        )

        if source_type in task.prohibited_sources:
            return self._rejected(
                task,
                source_type,
                raw,
                "Equipment source type is prohibited.",
            )

        if source_type not in task.allowed_sources:
            return self._rejected(
                task,
                source_type,
                raw,
                "Equipment source type is not allowed.",
            )

        items = raw.get(
            "equipment_items"
        )

        if items is None:
            return self._rejected(
                task,
                source_type,
                raw,
                "Equipment candidate contains no item field.",
            )

        if len(items) == 0:
            return self._rejected(
                task,
                source_type,
                raw,
                (
                    "Empty equipment candidate is not accepted as evidence "
                    "that the derivative has zero equipment."
                ),
            )

        return self._validated(
            task,
            "EQUIPMENT_SPECIFICATION",
            source_type,
            raw,
            (
                "Equipment specification candidate contains explicit items; "
                "source type is preserved for downstream trust policy."
            ),
        )

    # ========================================================
    # RESULT HELPERS
    # ========================================================

    def _validated(
        self,
        task,
        candidate_type,
        source_type,
        raw,
        diagnostic,
    ):
        return EvidenceCandidate(
            provider=task.provider,
            target_dimension=task.target_dimension,
            action_type=task.action_type,
            blocker_code=task.blocker_code,
            status="VALIDATED",
            candidate_type=candidate_type,
            canonical_vehicle_key=task.canonical_vehicle_key,
            source_type=source_type,
            source_url=raw.get("source_url"),
            source_text=raw.get("source_text"),
            payload=dict(raw),
            diagnostic=diagnostic,
        )

    def _rejected(
        self,
        task,
        source_type,
        raw,
        diagnostic,
    ):
        return EvidenceCandidate(
            provider=task.provider,
            target_dimension=task.target_dimension,
            action_type=task.action_type,
            blocker_code=task.blocker_code,
            status="REJECTED",
            candidate_type="REJECTED_CANDIDATE",
            canonical_vehicle_key=task.canonical_vehicle_key,
            source_type=source_type,
            source_url=raw.get("source_url"),
            source_text=raw.get("source_text"),
            payload=dict(raw),
            diagnostic=diagnostic,
        )

    def _unresolved(
        self,
        task,
        diagnostic,
    ):
        return EvidenceCandidate(
            provider=task.provider,
            target_dimension=task.target_dimension,
            action_type=task.action_type,
            blocker_code=task.blocker_code,
            status="UNRESOLVED",
            candidate_type="NO_CANDIDATE",
            canonical_vehicle_key=task.canonical_vehicle_key,
            source_type=None,
            source_url=None,
            source_text=None,
            payload={},
            diagnostic=diagnostic,
        )
