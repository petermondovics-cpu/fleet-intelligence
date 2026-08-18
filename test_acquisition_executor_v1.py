from dataclasses import dataclass

from comparison.acquisition_executor import (
    AcquisitionExecutor,
)


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


class Plan:
    def __init__(self, tasks):
        self.tasks = tasks

    def by_priority(self):
        return self.tasks


def main():

    # ========================================================
    # TEST 1 - VALID OBSERVED CONTRACT
    # ========================================================

    task = Task(
        provider="Arval",
        action_type="COLLECT_OBSERVED_PRICED_CONTRACT_VARIANT",
        target_dimension="CONTRACT",
        priority=10,
        blocker_code="CONTRACT_NORMALIZATION_INCOMPLETE",
        strategy="x",
        allowed_sources=(
            "PROVIDER_PRICED_OFFER_PAGE",
        ),
        prohibited_sources=(
            "UNPRICED_QUOTE_CONTROL",
        ),
        canonical_vehicle_key="BYD|ATTO 2|PHEV",
        message="",
    )

    executor = AcquisitionExecutor(
        contract_discovery=lambda task: {
            "source_type": "PROVIDER_PRICED_OFFER_PAGE",
            "source_url": "https://example.com",
            "monthly_fee": 180000,
            "duration": 48,
            "mileage": 20000,
        }
    )

    result = executor.execute_task(
        task
    )

    assert result.status == "VALIDATED"
    assert (
        result.candidate_type
        == "OBSERVED_PRICED_CONTRACT_VARIANT"
    )

    print(
        "TEST 1 PASSED - "
        "OBSERVED PRICED CONTRACT VALIDATED"
    )

    # ========================================================
    # TEST 2 - AYVENS SLIDER REJECTED
    # ========================================================

    ayvens_task = Task(
        provider="Ayvens",
        action_type="COLLECT_OBSERVED_PRICED_CONTRACT_VARIANT",
        target_dimension="CONTRACT",
        priority=10,
        blocker_code="CONTRACT_NORMALIZATION_INCOMPLETE",
        strategy="x",
        allowed_sources=(
            "PROVIDER_PRICED_OFFER_PAGE",
        ),
        prohibited_sources=(
            "AYVENS_DURATION_MILEAGE_SLIDER",
        ),
        canonical_vehicle_key="BYD|ATTO 2|PHEV",
        message="",
    )

    executor = AcquisitionExecutor(
        contract_discovery=lambda task: {
            "source_type": "AYVENS_DURATION_MILEAGE_SLIDER",
            "duration": 60,
            "mileage": 20000,
            "monthly_fee": 189990,
        }
    )

    result = executor.execute_task(
        ayvens_task
    )

    assert result.status == "REJECTED"

    print(
        "TEST 2 PASSED - "
        "AYVENS SLIDER CANNOT BECOME PRICING EVIDENCE"
    )

    # ========================================================
    # TEST 3 - EXPLICIT DOWN PAYMENT
    # ========================================================

    financial_task = Task(
        provider="Arval",
        action_type="FIND_EXPLICIT_DOWN_PAYMENT_CONDITION",
        target_dimension="FINANCIAL",
        priority=10,
        blocker_code="DOWN_PAYMENT_EVIDENCE_INCOMPLETE",
        strategy="x",
        allowed_sources=(
            "PROVIDER_TERMS_OR_PDF",
        ),
        prohibited_sources=(
            "DEFAULT_20_PERCENT_ASSUMPTION",
        ),
        canonical_vehicle_key="BYD|ATTO 2|PHEV",
        message="",
    )

    executor = AcquisitionExecutor(
        financial_discovery=lambda task: {
            "source_type": "PROVIDER_TERMS_OR_PDF",
            "source_url": "https://example.com/terms.pdf",
            "down_payment_percent": 20,
            "source_text": "Induló díj: 20%",
        }
    )

    result = executor.execute_task(
        financial_task
    )

    assert result.status == "VALIDATED"
    assert (
        result.payload["down_payment_percent"]
        == 20
    )

    print(
        "TEST 3 PASSED - "
        "EXPLICIT DOWN PAYMENT VALIDATED"
    )

    # ========================================================
    # TEST 4 - EMPTY EQUIPMENT NOT ZERO
    # ========================================================

    equipment_task = Task(
        provider="Arval",
        action_type="FIND_EQUIPMENT_SPECIFICATION_SOURCE",
        target_dimension="EQUIPMENT",
        priority=20,
        blocker_code="EQUIPMENT_EVIDENCE_INCOMPLETE",
        strategy="x",
        allowed_sources=(
            "MANUFACTURER_BROCHURE_OR_PDF",
        ),
        prohibited_sources=(),
        canonical_vehicle_key="BYD|ATTO 2|PHEV",
        message="",
    )

    executor = AcquisitionExecutor(
        equipment_discovery=lambda task: {
            "source_type": "MANUFACTURER_BROCHURE_OR_PDF",
            "source_url": "https://example.com/spec.pdf",
            "equipment_items": [],
        }
    )

    result = executor.execute_task(
        equipment_task
    )

    assert result.status == "REJECTED"

    print(
        "TEST 4 PASSED - "
        "EMPTY EQUIPMENT LIST NOT ACCEPTED AS ZERO EQUIPMENT"
    )

    # ========================================================
    # TEST 5 - NO CALLBACK => UNRESOLVED
    # ========================================================

    executor = AcquisitionExecutor()

    result = executor.execute_task(
        financial_task
    )

    assert result.status == "UNRESOLVED"

    print(
        "TEST 5 PASSED - "
        "MISSING ACQUISITION CAPABILITY PRESERVED AS UNRESOLVED"
    )

    execution = executor.execute_plan(
        Plan((financial_task,))
    )

    assert len(execution.task_timings) == 1
    timing = execution.task_timings[0]
    assert timing.provider == "Arval"
    assert timing.target_dimension == "FINANCIAL"
    assert (
        timing.action_type
        == "FIND_EXPLICIT_DOWN_PAYMENT_CONDITION"
    )
    assert timing.seconds >= 0
    assert execution.candidates[0].status == "UNRESOLVED"

    print(
        "TEST 6 PASSED - ACQUISITION TASK TIMING PRESERVES "
        "PROVIDER, DIMENSION AND ACTION"
    )

    print(
        "\nALL ACQUISITION EXECUTOR V1 TESTS PASSED"
    )


if __name__ == "__main__":
    main()
