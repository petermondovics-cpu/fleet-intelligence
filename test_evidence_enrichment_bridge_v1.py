from dataclasses import dataclass
from comparison.acquisition_executor import (
    AcquisitionExecutionResult,
    EvidenceCandidate,
)
from comparison.evidence_enrichment_bridge import EvidenceEnrichmentBridge


@dataclass
class Vehicle:
    all_equipment: tuple

@dataclass
class Offer:
    url: str

@dataclass
class Composite:
    provider: str
    vehicle: Vehicle
    offer: Offer

@dataclass
class EquipmentEvidence:
    standard_status: str
    optional_status: str
    fully_comparable: bool = False

@dataclass
class Side:
    composite: Composite
    equipment_evidence: EquipmentEvidence

@dataclass
class EndToEnd:
    execution: AcquisitionExecutionResult


def side(provider, std, opt, items=(), fully=False):
    return Side(
        Composite(provider, Vehicle(tuple(items)), Offer("https://example.test")),
        EquipmentEvidence(std, opt, fully),
    )


def candidate(provider, owner, items, status="VALIDATED"):
    return EvidenceCandidate(
        provider=provider,
        target_dimension="EQUIPMENT",
        action_type="FIND_EQUIPMENT_SPECIFICATION_SOURCE",
        blocker_code="EQUIPMENT_EVIDENCE_INCOMPLETE",
        status=status,
        candidate_type="EQUIPMENT_SPECIFICATION",
        canonical_vehicle_key=f"{provider}|TEST",
        source_type=(
            "MANUFACTURER_MODEL_PAGE"
            if owner == "MANUFACTURER"
            else "PROVIDER_SPECIFICATION"
        ),
        source_url="https://example.test/spec",
        source_text="spec",
        payload={
            "equipment_items": tuple(items),
            "evidence_owner": owner,
        },
        diagnostic="test",
    )


def main():
    bridge = EvidenceEnrichmentBridge()

    left = side("Arval", "NOT_PUBLISHED", "NOT_PUBLISHED")
    right = side("Ayvens", "PARSING_UNRESOLVED", "PARSING_UNRESOLVED")

    execution = AcquisitionExecutionResult(
        status="EXECUTOR_PARTIAL",
        candidates=(
            candidate("Arval", "MANUFACTURER", ("camera", "heated seats")),
            candidate("Ayvens", "MANUFACTURER", ("camera",)),
        ),
    )
    ctx = bridge.enrich(left, right, EndToEnd(execution))

    assert ctx.left_equipment.usable_status == "MANUFACTURER_VALIDATED"
    assert ctx.left_equipment.provider_published is False
    assert ctx.left_equipment.source_owner == "MANUFACTURER"
    assert len(ctx.left_equipment.items) == 2
    print("TEST 1 PASSED - ARVAL MANUFACTURER FALLBACK PROMOTED SAFELY")

    assert ctx.right_equipment.usable_status == "UNRESOLVED"
    assert ctx.right_equipment.items == ()
    print("TEST 2 PASSED - PARSING_UNRESOLVED CANNOT BE BYPASSED")

    provider_side = side(
        "Ayvens", "PUBLISHED", "PUBLISHED",
        items=("provider camera",), fully=True,
    )
    ctx = bridge.enrich(left, provider_side, EndToEnd(execution))
    assert ctx.right_equipment.usable_status == "PROVIDER_VALIDATED"
    assert ctx.right_equipment.items == ("provider camera",)
    assert ctx.right_equipment.acquisition_used is False
    print("TEST 3 PASSED - COMPLETE PROVIDER EVIDENCE REMAINS AUTHORITATIVE")

    rejected = AcquisitionExecutionResult(
        status="EXECUTOR_PARTIAL",
        candidates=(
            candidate("Arval", "MANUFACTURER", ("camera",), status="REJECTED"),
        ),
    )
    ctx = bridge.enrich(left, right, EndToEnd(rejected))
    assert ctx.left_equipment.usable_status == "UNRESOLVED"
    print("TEST 4 PASSED - NON-VALIDATED CANDIDATES NEVER PROMOTED")

    assert left.equipment_evidence.standard_status == "NOT_PUBLISHED"
    assert right.equipment_evidence.standard_status == "PARSING_UNRESOLVED"
    print("TEST 5 PASSED - ORIGINAL EVIDENCE OBJECTS NOT MUTATED")

    print("\nALL EVIDENCE ENRICHMENT BRIDGE V1 TESTS PASSED")


if __name__ == "__main__":
    main()
