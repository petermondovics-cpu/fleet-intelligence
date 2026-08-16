from dataclasses import dataclass

from comparison.evidence_acquisition_orchestrator import (
    ACQ_READY,
    EvidenceAcquisitionOrchestrator,
)


@dataclass(frozen=True)
class Barrier:
    code: str
    message: str
    hard: bool = False


@dataclass(frozen=True)
class FakeResult:
    barriers: tuple


@dataclass
class Vehicle:
    brand: str
    model: str
    fuel_type: str


@dataclass
class Composite:
    provider: str
    vehicle: Vehicle


@dataclass
class Side:
    composite: Composite


def side(provider, model="ATTO 2"):
    return Side(
        composite=Composite(
            provider=provider,
            vehicle=Vehicle(
                brand="BYD",
                model=model,
                fuel_type="PHEV",
            ),
        )
    )


def main():

    left = side("Arval")
    right = side("Ayvens", "ATTO 2 DM-i")

    result = FakeResult(
        barriers=(
            Barrier(
                "CONTRACT_NORMALIZATION_INCOMPLETE",
                "",
            ),
            Barrier(
                "DOWN_PAYMENT_EVIDENCE_INCOMPLETE",
                "",
            ),
            Barrier(
                "EQUIPMENT_EVIDENCE_INCOMPLETE",
                "",
            ),
            Barrier(
                "SERVICE_EVIDENCE_INCOMPLETE",
                "",
            ),
        )
    )

    plan = (
        EvidenceAcquisitionOrchestrator()
        .plan(
            result,
            left,
            right,
        )
    )

    assert plan.status == ACQ_READY
    assert plan.task_count == 8

    contract_tasks = [
        task
        for task in plan.tasks
        if task.target_dimension == "CONTRACT"
    ]

    assert len(contract_tasks) == 2

    ayvens_contract = next(
        task
        for task in contract_tasks
        if task.provider == "Ayvens"
    )

    assert (
        "AYVENS_DURATION_MILEAGE_SLIDER"
        in ayvens_contract.prohibited_sources
    )

    financial_tasks = [
        task
        for task in plan.tasks
        if task.target_dimension == "FINANCIAL"
    ]

    assert len(financial_tasks) == 2

    assert all(
        "DEFAULT_20_PERCENT_ASSUMPTION"
        in task.prohibited_sources
        for task in financial_tasks
    )

    equipment_tasks = [
        task
        for task in plan.tasks
        if task.target_dimension == "EQUIPMENT"
    ]

    assert len(equipment_tasks) == 2

    assert all(
        "MANUFACTURER_BROCHURE_OR_PDF"
        in task.allowed_sources
        for task in equipment_tasks
    )

    service_tasks = [
        task
        for task in plan.tasks
        if task.target_dimension == "SERVICES"
    ]

    assert len(service_tasks) == 2

    print(
        "TEST 1 PASSED - "
        "GENERIC GAPS EXPAND TO PROVIDER-SPECIFIC TASKS"
    )

    assert all(
        task.canonical_vehicle_key
        for task in plan.tasks
    )

    print(
        "TEST 2 PASSED - "
        "ALL TASKS CARRY VEHICLE IDENTITY CONTEXT"
    )

    print(
        "TEST 3 PASSED - "
        "AYVENS SLIDER AND SILENT 20% ASSUMPTION ARE PROHIBITED"
    )

    print(
        "\nALL EVIDENCE ACQUISITION ORCHESTRATOR V1 TESTS PASSED"
    )


if __name__ == "__main__":
    main()
