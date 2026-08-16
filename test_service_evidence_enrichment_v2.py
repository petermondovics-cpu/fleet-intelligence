from dataclasses import dataclass, field

from comparison.acquisition_executor import (
    AcquisitionExecutionResult,
    EvidenceCandidate,
)
from comparison.evidence_enrichment_bridge import EvidenceEnrichmentBridge
from comparison.service_package_comparison import (
    SERVICE_MATCH,
    ServicePackageComparisonEngine,
)
from models.financial_conditions import ServicePackage


@dataclass
class Vehicle:
    all_equipment: tuple = ()


@dataclass
class Offer:
    url: str = "https://example.test"


@dataclass
class Composite:
    provider: str
    services: ServicePackage
    vehicle: Vehicle = field(default_factory=Vehicle)
    offer: Offer = field(default_factory=Offer)


@dataclass
class EquipmentEvidence:
    standard_status: str = "PARSING_UNRESOLVED"
    optional_status: str = "PARSING_UNRESOLVED"
    fully_comparable: bool = False


@dataclass
class Side:
    composite: Composite
    equipment_evidence: EquipmentEvidence = field(
        default_factory=EquipmentEvidence
    )


@dataclass
class EndToEnd:
    execution: AcquisitionExecutionResult


def service_candidate(provider, scope=None, services=()):
    payload = {
        "services": tuple(services),
    }

    if scope is not None:
        payload["applicability_scope"] = scope

    return EvidenceCandidate(
        provider=provider,
        target_dimension="SERVICES",
        action_type="FIND_PROVIDER_SERVICE_DOCUMENTATION",
        blocker_code="SERVICE_EVIDENCE_INCOMPLETE",
        status="VALIDATED",
        candidate_type="PROVIDER_SERVICE_ASSERTIONS",
        canonical_vehicle_key="BYD|ATTO 2|PHEV",
        source_type="PROVIDER_SERVICE_PAGE",
        source_url="https://example.test/services",
        source_text="service documentation",
        payload=payload,
        diagnostic="test",
    )


def main():
    left = Side(
        Composite(
            "Arval",
            ServicePackage(),
        )
    )

    right = Side(
        Composite(
            "Ayvens",
            ServicePackage(),
        )
    )

    # 1. Generic provider documentation must NOT be promoted.
    generic = AcquisitionExecutionResult(
        status="EXECUTOR_PARTIAL",
        candidates=(
            service_candidate(
                "Arval",
                scope=None,
                services=(
                    {
                        "code": "MAINTENANCE",
                        "included": True,
                        "source_text": "maint",
                    },
                ),
            ),
        ),
    )

    ctx = EvidenceEnrichmentBridge().enrich(
        left,
        right,
        EndToEnd(generic),
    )

    assert (
        ctx.left_services.acquisition_used
        is False
    )

    assert (
        ctx.left_services.acquired_codes
        == ()
    )

    print(
        "TEST 1 PASSED - GENERIC PROVIDER DOCS NOT PROMOTED TO OFFER INCLUSION"
    )

    # 2. Explicit exact-offer scope may be promoted.
    scoped = AcquisitionExecutionResult(
        status="EXECUTOR_PARTIAL",
        candidates=(
            service_candidate(
                "Arval",
                scope="EXACT_OFFER",
                services=(
                    {
                        "code": "MAINTENANCE",
                        "included": True,
                        "source_text": "maint",
                    },
                    {
                        "code": "MOBILITY",
                        "included": True,
                        "source_text": "assist",
                    },
                ),
            ),
            service_candidate(
                "Ayvens",
                scope="EXACT_OFFER",
                services=(
                    {
                        "code": "MAINTENANCE",
                        "included": True,
                        "source_text": "maint",
                    },
                    {
                        "code": "ROADSIDE_ASSISTANCE",
                        "included": True,
                        "source_text": "assist",
                    },
                ),
            ),
        ),
    )

    ctx = EvidenceEnrichmentBridge().enrich(
        left,
        right,
        EndToEnd(scoped),
    )

    assert set(
        ctx.left_services.acquired_codes
    ) == {
        "MAINTENANCE",
        "ROADSIDE_ASSISTANCE",
    }

    assert set(
        ctx.right_services.acquired_codes
    ) == {
        "MAINTENANCE",
        "ROADSIDE_ASSISTANCE",
    }

    result = (
        ServicePackageComparisonEngine()
        .compare(
            ctx.left_services.package,
            ctx.right_services.package,
        )
    )

    assert result.status == SERVICE_MATCH

    print(
        "TEST 2 PASSED - EXACT-OFFER SERVICE EVIDENCE CAN CLOSE CANONICAL GAP"
    )

    # 3. Absence never becomes False.
    no_tax = AcquisitionExecutionResult(
        status="EXECUTOR_PARTIAL",
        candidates=(
            service_candidate(
                "Arval",
                scope="EXACT_OFFER",
                services=(
                    {
                        "code": "MAINTENANCE",
                        "included": True,
                        "source_text": "maint",
                    },
                ),
            ),
        ),
    )

    ctx = EvidenceEnrichmentBridge().enrich(
        left,
        right,
        EndToEnd(no_tax),
    )

    assert (
        "TAXES"
        not in ctx.left_services.acquired_codes
    )

    print(
        "TEST 3 PASSED - NON-PUBLICATION NEVER BECOMES EXCLUSION"
    )

    print(
        "\nALL SERVICE EVIDENCE ENRICHMENT V2 TESTS PASSED"
    )


if __name__ == "__main__":
    main()
