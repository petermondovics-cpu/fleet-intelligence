from dataclasses import dataclass

from comparison.full_comparison_orchestrator import (
    FullComparisonOrchestrator,
)


@dataclass
class Evidence:
    fully_comparable: bool


@dataclass
class Side:
    equipment_evidence: Evidence


def main():
    engine = FullComparisonOrchestrator()

    side = Side(
        equipment_evidence=Evidence(
            fully_comparable=False
        )
    )

    # Original provider-only view remains unusable.
    assert (
        engine._equipment_view_usable(
            side,
            None,
            None,
        )
        is False
    )

    # Enriched manufacturer evidence is explicitly usable.
    assert (
        engine._equipment_view_usable(
            side,
            ("item",),
            "MANUFACTURER_VALIDATED",
        )
        is True
    )

    # Items without a trusted status must never become usable.
    assert (
        engine._equipment_view_usable(
            side,
            ("item",),
            "UNRESOLVED",
        )
        is False
    )

    # Provider-validated enriched evidence is also usable.
    assert (
        engine._equipment_view_usable(
            side,
            ("item",),
            "PROVIDER_VALIDATED",
        )
        is True
    )

    print(
        "TEST PASSED - FULL COMPARISON V5 USES "
        "ENRICHED EQUIPMENT ONLY WITH EXPLICIT TRUSTED STATUS."
    )


if __name__ == "__main__":
    main()
