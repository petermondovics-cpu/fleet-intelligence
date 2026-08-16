from dataclasses import dataclass

from comparison.evidence_gap_resolver import (
    EvidenceGapResolver,
)


@dataclass(frozen=True)
class Barrier:
    code: str
    message: str
    hard: bool = False


@dataclass(frozen=True)
class FakeResult:
    barriers: tuple


def main():

    resolver = EvidenceGapResolver()

    result = resolver.resolve(
        FakeResult(
            barriers=(
                Barrier(
                    "SERVICE_EVIDENCE_INCOMPLETE",
                    "",
                ),
                Barrier(
                    "EQUIPMENT_EVIDENCE_INCOMPLETE",
                    "",
                ),
                Barrier(
                    "CONTRACT_NORMALIZATION_INCOMPLETE",
                    "",
                ),
                Barrier(
                    "DOWN_PAYMENT_EVIDENCE_INCOMPLETE",
                    "",
                ),
                Barrier(
                    "VEHICLE_VARIANT_DIFFERENCE",
                    "",
                ),
            )
        )
    )

    types = {
        item.action_type
        for item in result.actions
    }

    assert (
        "FIND_PROVIDER_SERVICE_DOCUMENTATION"
        in types
    )
    assert (
        "FIND_EQUIPMENT_SPECIFICATION_SOURCE"
        in types
    )
    assert (
        "COLLECT_OBSERVED_PRICED_CONTRACT_VARIANT"
        in types
    )
    assert (
        "FIND_EXPLICIT_DOWN_PAYMENT_CONDITION"
        in types
    )
    assert (
        "VERIFY_VARIANT_EQUIVALENCE"
        in types
    )

    priorities = [
        item.priority
        for item in result.by_priority()
    ]

    assert priorities == sorted(priorities)

    print(
        "TEST 1 PASSED - "
        "BLOCKERS CONVERT TO EVIDENCE ACQUISITION ACTIONS"
    )

    result = resolver.resolve(
        FakeResult(
            barriers=(
                Barrier(
                    "VEHICLE_MODEL_MISMATCH",
                    "",
                    True,
                ),
            )
        )
    )

    assert (
        result.actions[0].action_type
        == "REJECT_OR_REVIEW_HARD_MISMATCH"
    )

    print(
        "TEST 2 PASSED - "
        "HARD MISMATCH IS NOT TREATED AS DATA-GAP NORMALIZATION"
    )

    print(
        "\nALL EVIDENCE GAP RESOLVER V1 TESTS PASSED"
    )


if __name__ == "__main__":
    main()
