from dataclasses import dataclass

from comparison.provider_acquisition_router import (
    ProviderAcquisitionRouter,
)


@dataclass
class Offer:
    duration: int
    mileage: int
    url: str


@dataclass
class Composite:
    provider: str
    offer: Offer


@dataclass
class Side:
    composite: Composite


@dataclass(frozen=True)
class Task:
    provider: str
    action_type: str
    target_dimension: str
    priority: int
    blocker_code: str
    strategy: str
    allowed_sources: tuple
    prohibited_sources: tuple
    canonical_vehicle_key: str
    message: str


class Connector:
    def contract_discovery(self, task):
        return {
            "provider": task.provider,
            "duration": task.current_duration,
            "mileage": task.current_mileage,
        }


class RecordingExecutor:
    def __init__(self):
        self.tasks = None

    def execute_plan(self, plan):
        self.tasks = plan.by_priority()
        return "EXECUTION"


class RecordingManufacturerAcquisition:
    def __init__(self, status="UNRESOLVED"):
        self.calls = []
        self.status = status

    def acquire(self, task, offer, provider_equipment_status):
        self.calls.append((task, offer, provider_equipment_status))
        return type(
            "ManufacturerResult",
            (),
            {
                "status": self.status,
                "source_type": None,
                "source_url": None,
                "source_text": None,
                "brand": None,
                "model": None,
                "trim": None,
                "fuel_type": None,
                "equipment": (),
                "provider_equipment_status": provider_equipment_status,
                "manufacturer_equipment_status": "UNRESOLVED",
            },
        )()


class FixedPlan:
    status = "ACQUISITION_PLAN_READY"

    def __init__(self, tasks):
        self.tasks = tasks

    def by_priority(self):
        return self.tasks


class FixedPlanner:
    def __init__(self, tasks):
        self.tasks = tasks

    def plan(self, full_comparison_result, left, right):
        return FixedPlan(self.tasks)


def main():

    left = Side(
        Composite(
            "Arval",
            Offer(
                60,
                20000,
                "https://arval.example/offer",
            ),
        )
    )

    right = Side(
        Composite(
            "Ayvens",
            Offer(
                48,
                20000,
                "https://ayvens.example/offer",
            ),
        )
    )

    router = ProviderAcquisitionRouter(
        arval_connector=Connector(),
        ayvens_connector=Connector(),
    )

    arval_task = Task(
        provider="Arval",
        action_type="X",
        target_dimension="CONTRACT",
        priority=10,
        blocker_code="X",
        strategy="X",
        allowed_sources=(),
        prohibited_sources=(),
        canonical_vehicle_key="BYD|ATTO 2|PHEV",
        message="",
    )

    routed = router._route_task(
        arval_task,
        left,
        right,
    )

    assert routed.current_duration == 60
    assert routed.current_mileage == 20000
    assert (
        routed.current_url
        == "https://arval.example/offer"
    )

    print(
        "TEST 1 PASSED - "
        "CURRENT PROVIDER CONTRACT CONTEXT ATTACHED"
    )

    ayvens_task = Task(
        provider="Ayvens",
        action_type="X",
        target_dimension="CONTRACT",
        priority=10,
        blocker_code="X",
        strategy="X",
        allowed_sources=(),
        prohibited_sources=(),
        canonical_vehicle_key="BYD|ATTO 2|PHEV",
        message="",
    )

    routed = router._route_task(
        ayvens_task,
        left,
        right,
    )

    assert routed.current_duration == 48

    assert (
        router._connector_for("Arval")
        is router.arval
    )

    assert (
        router._connector_for("Ayvens")
        is router.ayvens
    )

    print(
        "TEST 2 PASSED - "
        "TASKS ROUTE TO CORRECT PROVIDER CONNECTOR"
    )

    service_task = Task(
        provider="Arval",
        action_type="X",
        target_dimension="SERVICES",
        priority=20,
        blocker_code="X",
        strategy="X",
        allowed_sources=(),
        prohibited_sources=(),
        canonical_vehicle_key="BYD|ATTO 2|PHEV",
        message="",
    )

    filtered_router = ProviderAcquisitionRouter(
        arval_connector=Connector(),
        ayvens_connector=Connector(),
        excluded_dimensions=("contract",),
    )
    filtered_router.planner = FixedPlanner(
        (arval_task, ayvens_task, service_task)
    )
    filtered_router.executor = RecordingExecutor()

    acquisition = filtered_router.execute(
        object(),
        left,
        right,
    )

    assert acquisition.plan_status == "ACQUISITION_PLAN_READY"
    assert acquisition.task_count == 1
    assert acquisition.execution == "EXECUTION"
    assert tuple(
        task.target_dimension
        for task in filtered_router.executor.tasks
    ) == ("SERVICES",)

    print(
        "TEST 3 PASSED - OPT-IN DIMENSION FILTER SKIPS CONTRACT "
        "ACQUISITION WITHOUT AFFECTING OTHER TASKS"
    )

    equipment_a = Task(
        provider="Arval",
        action_type="FIND_EQUIPMENT_SPECIFICATION_SOURCE",
        target_dimension="EQUIPMENT",
        priority=20,
        blocker_code="EQUIPMENT_EVIDENCE_INCOMPLETE",
        strategy="X",
        allowed_sources=(),
        prohibited_sources=(),
        canonical_vehicle_key="BYD|ATTO 2|PHEV",
        message="",
    )
    equipment_b = Task(
        provider="Arval",
        action_type="VERIFY_VARIANT_EQUIVALENCE",
        target_dimension="EQUIPMENT",
        priority=30,
        blocker_code="VARIANT_EQUIVALENCE_EVIDENCE_INCOMPLETE",
        strategy="X",
        allowed_sources=(),
        prohibited_sources=(),
        canonical_vehicle_key="BYD|ATTO 2|PHEV",
        message="",
    )
    manufacturer = RecordingManufacturerAcquisition()
    cached_router = ProviderAcquisitionRouter(
        arval_connector=Connector(),
        ayvens_connector=Connector(),
        manufacturer_equipment=manufacturer,
    )
    cached_router.planner = FixedPlanner((equipment_a, equipment_b))
    cached_result = cached_router.execute(object(), left, right)

    assert len(manufacturer.calls) == 1
    assert len(cached_result.execution.candidates) == 2
    assert all(
        candidate.status == "UNRESOLVED"
        for candidate in cached_result.execution.candidates
    )

    # A new execute call intentionally starts a fresh cache so live evidence
    # is never retained across comparisons.
    cached_router.execute(object(), left, right)
    assert len(manufacturer.calls) == 2

    print(
        "TEST 4 PASSED - DUPLICATE EQUIPMENT ACTIONS SHARE ONE "
        "MANUFACTURER DISCOVERY ONLY WITHIN A SINGLE EXECUTION"
    )

    print(
        "\nALL PROVIDER ACQUISITION ROUTER V1 TESTS PASSED"
    )


if __name__ == "__main__":
    main()
