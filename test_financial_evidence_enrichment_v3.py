from dataclasses import dataclass, field

from comparison.acquisition_executor import (
    AcquisitionExecutionResult,
    EvidenceCandidate,
)
from comparison.evidence_enrichment_bridge import (
    EvidenceEnrichmentBridge,
)
from models.financial_conditions import (
    EVIDENCE_OBSERVED,
    EVIDENCE_UNKNOWN,
    DownPayment,
    FinancialConditions,
    FinancialEvidence,
    ServicePackage,
)


@dataclass
class Vehicle:
    all_equipment: tuple = ()


@dataclass
class Offer:
    url: str = "https://example.test"


@dataclass
class Composite:
    provider: str
    financial: FinancialConditions
    services: ServicePackage = field(default_factory=ServicePackage)
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


def unknown_financial(monthly_fee):
    return FinancialConditions(
        monthly_fee=monthly_fee,
        down_payment=DownPayment(
            percent=None,
            amount=None,
            status=EVIDENCE_UNKNOWN,
            evidence=FinancialEvidence(
                status=EVIDENCE_UNKNOWN,
            ),
        ),
        monthly_fee_evidence=FinancialEvidence(
            status=EVIDENCE_OBSERVED,
            source_url="https://example.test/original",
            source_text=f"{monthly_fee} Ft/hó",
        ),
    )


def observed_zero_financial_candidate(
    provider="Ayvens",
    status="VALIDATED",
    scope="EXACT_OFFER",
):
    return EvidenceCandidate(
        provider=provider,
        target_dimension="FINANCIAL",
        action_type="FIND_EXPLICIT_DOWN_PAYMENT_CONDITION",
        blocker_code="DOWN_PAYMENT_EVIDENCE_INCOMPLETE",
        status=status,
        candidate_type="EXPLICIT_DOWN_PAYMENT",
        canonical_vehicle_key="BYD|ATTO 2|PHEV",
        source_type="PROVIDER_OFFER_PAGE",
        source_url="https://autotartosberlet.ayvens.com/byd/atto-2-dm-i",
        source_text=(
            "Observed Ayvens financial switch states on exact offer: "
            "20% initial payment -> 189990 Ft/hó; "
            "0% initial payment -> 223990 Ft/hó; "
            "48 hó; 20000 km/év."
        ),
        payload={
            "down_payment_percent": 0.0,
            "monthly_fee": 223990,
            "duration": 48,
            "mileage": 20000,
            "pricing_basis": "OBSERVED_ZERO_DOWN_PAYMENT_STATE",
            "applicability_scope": scope,
            "financial_variants": (
                {
                    "down_payment_percent": 20.0,
                    "monthly_fee": 189990,
                    "duration": 48,
                    "mileage": 20000,
                    "switch_checked": True,
                },
                {
                    "down_payment_percent": 0.0,
                    "monthly_fee": 223990,
                    "duration": 48,
                    "mileage": 20000,
                    "switch_checked": False,
                },
            ),
        },
        diagnostic="Explicit provider down-payment condition discovered.",
    )


def main():
    left = Side(
        Composite(
            provider="Arval",
            financial=unknown_financial(192312),
        )
    )

    right = Side(
        Composite(
            provider="Ayvens",
            financial=unknown_financial(189990),
        )
    )

    acquisition = EndToEnd(
        AcquisitionExecutionResult(
            status="EXECUTOR_PARTIAL",
            candidates=(
                observed_zero_financial_candidate(),
            ),
        )
    )

    ctx = EvidenceEnrichmentBridge().enrich(
        left,
        right,
        acquisition,
    )

    # --------------------------------------------------------
    # 1. Ayvens exact-offer observed state is promoted
    # --------------------------------------------------------

    ef = ctx.right_financial

    assert ef.acquisition_used is True
    assert ef.usable_status == "ENRICHED_PROVIDER_EVIDENCE"
    assert ef.pricing_basis == "OBSERVED_ZERO_DOWN_PAYMENT_STATE"

    assert ef.financial.monthly_fee == 223990
    assert ef.financial.down_payment.status == EVIDENCE_OBSERVED
    assert ef.financial.down_payment.percent == 0.0
    assert ef.financial.down_payment.amount is None

    assert ef.financial.monthly_fee_evidence.status == EVIDENCE_OBSERVED
    assert (
        ef.financial.monthly_fee_evidence.source_url
        == "https://autotartosberlet.ayvens.com/byd/atto-2-dm-i"
    )

    print(
        "TEST 1 PASSED - AYVENS OBSERVED 0% / 223990 BASELINE PROMOTED"
    )

    # --------------------------------------------------------
    # 2. Original offer remains untouched
    # --------------------------------------------------------

    assert right.composite.financial.monthly_fee == 189990
    assert right.composite.financial.down_payment.status == EVIDENCE_UNKNOWN
    assert right.composite.financial.down_payment.percent is None

    print(
        "TEST 2 PASSED - ORIGINAL AYVENS FINANCIAL OBJECT NOT MUTATED"
    )

    # --------------------------------------------------------
    # 3. Arval remains original/unknown
    # --------------------------------------------------------

    assert ctx.left_financial.acquisition_used is False
    assert ctx.left_financial.usable_status == "ORIGINAL_ONLY"
    assert (
        ctx.left_financial.financial.down_payment.status
        == EVIDENCE_UNKNOWN
    )

    print(
        "TEST 3 PASSED - ARVAL UNKNOWN FINANCIAL EVIDENCE REMAINS UNKNOWN"
    )

    # --------------------------------------------------------
    # 4. Generic scope is not promotable
    # --------------------------------------------------------

    generic = EndToEnd(
        AcquisitionExecutionResult(
            status="EXECUTOR_PARTIAL",
            candidates=(
                observed_zero_financial_candidate(
                    scope="GENERIC_PROVIDER_DOCUMENTATION",
                ),
            ),
        )
    )

    ctx2 = EvidenceEnrichmentBridge().enrich(
        left,
        right,
        generic,
    )

    assert ctx2.right_financial.acquisition_used is False
    assert ctx2.right_financial.financial.monthly_fee == 189990
    assert (
        ctx2.right_financial.financial.down_payment.status
        == EVIDENCE_UNKNOWN
    )

    print(
        "TEST 4 PASSED - NON-EXACT FINANCIAL CANDIDATE NOT PROMOTED"
    )

    # --------------------------------------------------------
    # 5. Rejected candidate is ignored
    # --------------------------------------------------------

    rejected = EndToEnd(
        AcquisitionExecutionResult(
            status="EXECUTOR_PARTIAL",
            candidates=(
                observed_zero_financial_candidate(
                    status="REJECTED",
                ),
            ),
        )
    )

    ctx3 = EvidenceEnrichmentBridge().enrich(
        left,
        right,
        rejected,
    )

    assert ctx3.right_financial.acquisition_used is False
    assert (
        ctx3.right_financial.financial.down_payment.status
        == EVIDENCE_UNKNOWN
    )

    print(
        "TEST 5 PASSED - NON-VALIDATED FINANCIAL CANDIDATE NEVER PROMOTED"
    )

    print(
        "\nALL FINANCIAL EVIDENCE ENRICHMENT V3 TESTS PASSED"
    )


if __name__ == "__main__":
    main()
