from dataclasses import dataclass
from typing import Optional, Tuple

from comparison.acquisition_executor import AcquisitionExecutor, AcquisitionExecutionResult
from comparison.evidence_acquisition_orchestrator import EvidenceAcquisitionOrchestrator

@dataclass(frozen=True)
class RoutedAcquisitionTask:
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
    current_duration: Optional[int] = None
    current_mileage: Optional[int] = None
    current_url: Optional[str] = None
    target_duration: Optional[int] = None
    target_mileage: Optional[int] = None

@dataclass(frozen=True)
class EndToEndAcquisitionResult:
    plan_status: str
    task_count: int
    execution: AcquisitionExecutionResult

class ProviderAcquisitionRouter:
    def __init__(
        self,
        *,
        arval_connector,
        ayvens_connector,
        manufacturer_equipment=None,
        excluded_dimensions: Tuple[str, ...] = (),
    ):
        self.planner = EvidenceAcquisitionOrchestrator()
        self.arval = arval_connector
        self.ayvens = ayvens_connector
        self.manufacturer_equipment = manufacturer_equipment
        self.excluded_dimensions = frozenset(
            str(item).strip().upper()
            for item in excluded_dimensions
        )
        self._left = None
        self._right = None
        self.executor = AcquisitionExecutor(
            contract_discovery=self._contract_discovery,
            service_discovery=self._service_discovery,
            financial_discovery=self._financial_discovery,
            equipment_discovery=self._equipment_discovery,
        )

    def execute(self, full_comparison_result, left, right):
        self._left, self._right = left, right
        plan = self.planner.plan(full_comparison_result, left, right)
        routed_tasks = tuple(
            self._route_task(task, left, right)
            for task in plan.by_priority()
            if task.target_dimension.strip().upper()
            not in self.excluded_dimensions
        )
        execution = self.executor.execute_plan(_RoutedPlan(tasks=routed_tasks))
        return EndToEndAcquisitionResult(plan.status, len(routed_tasks), execution)

    def _route_task(self, task, left, right):
        side = self._side_for_provider(task.provider, left, right)
        if side is None:
            return RoutedAcquisitionTask(
                task.provider, task.action_type, task.target_dimension, task.priority,
                task.blocker_code, task.strategy, task.allowed_sources,
                task.prohibited_sources, task.canonical_vehicle_key, task.message
            )

        offer = side.composite.offer
        other = right if side is left else left
        other_offer = other.composite.offer

        target_duration = None
        target_mileage = None
        if task.target_dimension == "CONTRACT":
            target_duration = other_offer.duration
            target_mileage = other_offer.mileage

        return RoutedAcquisitionTask(
            task.provider, task.action_type, task.target_dimension, task.priority,
            task.blocker_code, task.strategy, task.allowed_sources,
            task.prohibited_sources, task.canonical_vehicle_key, task.message,
            current_duration=offer.duration,
            current_mileage=offer.mileage,
            current_url=offer.url,
            target_duration=target_duration,
            target_mileage=target_mileage,
        )

    @staticmethod
    def _side_for_provider(provider, left, right):
        p = provider.strip().casefold()
        if left.composite.provider.strip().casefold() == p:
            return left
        if right.composite.provider.strip().casefold() == p:
            return right
        return None

    def _connector_for(self, provider):
        p = provider.strip().casefold()
        if p == "arval":
            return self.arval
        if p == "ayvens":
            return self.ayvens
        return None

    def _contract_discovery(self, task):
        c = self._connector_for(task.provider)
        return None if c is None else c.contract_discovery(task)

    def _service_discovery(self, task):
        c = self._connector_for(task.provider)
        return None if c is None else c.service_discovery(task)

    def _financial_discovery(self, task):
        c = self._connector_for(task.provider)
        return None if c is None else c.financial_discovery(task)

    def _equipment_discovery(self, task):
        if self.manufacturer_equipment is None:
            return None
        side = self._side_for_provider(task.provider, self._left, self._right)
        if side is None:
            return None
        offer = side.composite.offer
        provider_status = self._provider_equipment_status(side)
        result = self.manufacturer_equipment.acquire(
            task=task, offer=offer, provider_equipment_status=provider_status
        )
        if result.status != "VALIDATED":
            return None
        return {
            "source_type": result.source_type,
            "source_url": result.source_url,
            "source_text": result.source_text,
            "provider": task.provider,
            "brand": result.brand,
            "model": result.model,
            "trim": result.trim,
            "fuel_type": result.fuel_type,
            "equipment_items": result.equipment,
            "equipment": result.equipment,
            "provider_equipment_status": result.provider_equipment_status,
            "manufacturer_equipment_status": result.manufacturer_equipment_status,
            "evidence_owner": "MANUFACTURER",
        }

    @staticmethod
    def _provider_equipment_status(side):
        evidence = getattr(side, "equipment_evidence", None)
        if evidence is not None:
            value = getattr(evidence, "standard_status", None)
            if value:
                return value
        return "UNKNOWN"

@dataclass(frozen=True)
class _RoutedPlan:
    tasks: Tuple[RoutedAcquisitionTask, ...]
    def by_priority(self):
        return self.tasks
