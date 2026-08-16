from datetime import datetime

from models.offer import Offer
from models.vehicle_specification import (
    EVIDENCE_OBSERVED,
    VehicleEvidence,
    VehicleSpecification,
)
from models.financial_conditions import (
    EVIDENCE_OBSERVED,
    EVIDENCE_UNKNOWN,
    DownPayment,
    FinancialConditions,
    FinancialEvidence,
    ServiceItem,
    ServicePackage,
)
from models.composite_offer import CompositeOffer
from models.equipment_evidence import (
    EQUIPMENT_NOT_PUBLISHED,
    EquipmentEvidenceStatus,
)
from comparison.evidence_aware_comparable import (
    EvidenceAwareCompositeOffer,
)
from comparison.normalized_evidence_aware import (
    NormalizedEvidenceAwareComparableEngine,
)
from models.comparable_offer import (
    INSUFFICIENT_EVIDENCE,
    NOT_COMPARABLE,
)


def ve(text):
    return VehicleEvidence(
        status=EVIDENCE_OBSERVED,
        source_url="https://example.com",
        source_text=text,
    )


def fe(text):
    return FinancialEvidence(
        status=EVIDENCE_OBSERVED,
        source_url="https://example.com",
        source_text=text,
    )


def service(name, category, included=True):
    return ServiceItem(
        name=name,
        category=category,
        included=included,
        evidence=fe(name),
    )


def make(provider, services):
    offer = Offer(
        provider=provider,
        brand="BYD",
        model="ATTO 2",
        trim="Active",
        fuel_type="PHEV",
        monthly_fee=190000,
        duration=48,
        mileage=20000,
        url="https://example.com",
        scraped_at=datetime.now(),
    )

    vehicle = VehicleSpecification(
        brand="BYD",
        model="ATTO 2",
        trim="Active",
        fuel_type="PHEV",
        brand_evidence=ve("BYD"),
        model_evidence=ve("ATTO 2"),
        trim_evidence=ve("Active"),
        fuel_evidence=ve("PHEV"),
        standard_equipment=[],
        optional_equipment=[],
    )

    financial = FinancialConditions(
        monthly_fee=190000,
        down_payment=DownPayment(
            percent=None,
            amount=None,
            status=EVIDENCE_UNKNOWN,
            evidence=FinancialEvidence(
                status=EVIDENCE_UNKNOWN
            ),
        ),
        monthly_fee_evidence=fe("190000 Ft/hó"),
    )

    composite = CompositeOffer(
        offer=offer,
        vehicle=vehicle,
        services=ServicePackage(items=services),
        financial=financial,
    )

    return EvidenceAwareCompositeOffer(
        composite=composite,
        equipment_evidence=EquipmentEvidenceStatus(
            standard_status=EQUIPMENT_NOT_PUBLISHED,
            optional_status=EQUIPMENT_NOT_PUBLISHED,
        ),
    )


def main():

    engine = NormalizedEvidenceAwareComparableEngine()

    # TEST 1: aliases match; comparison proceeds to equipment evidence.
    left = make(
        "Arval",
        [
            service(
                "Közúti segítségnyújtás",
                "MOBILITY",
                True,
            )
        ],
    )

    right = make(
        "Ayvens",
        [
            service(
                "Assistance szolgáltatás",
                "MOBILITY",
                True,
            )
        ],
    )

    result = engine.compare(left, right)
    codes = {r.code for r in result.reasons}

    assert result.status == INSUFFICIENT_EVIDENCE
    assert "SERVICE_MISMATCH" not in codes
    assert "SERVICE_EVIDENCE_INCOMPLETE" not in codes
    assert "EQUIPMENT_EVIDENCE_INCOMPLETE" in codes

    print(
        "TEST 1 PASSED - CANONICAL SERVICE ALIASES "
        "REACH EQUIPMENT BARRIER"
    )

    # TEST 2: one-sided publication is insufficient evidence.
    left = make(
        "Arval",
        [
            service(
                "Közúti segítségnyújtás",
                "MOBILITY",
                True,
            ),
            service(
                "Finanszírozás",
                "FINANCING",
                True,
            ),
        ],
    )

    right = make(
        "Ayvens",
        [
            service(
                "Assistance szolgáltatás",
                "MOBILITY",
                True,
            )
        ],
    )

    result = engine.compare(left, right)
    codes = {r.code for r in result.reasons}

    assert result.status == INSUFFICIENT_EVIDENCE
    assert "SERVICE_LEFT_ONLY_PUBLISHED" in codes
    assert "SERVICE_EVIDENCE_INCOMPLETE" in codes
    assert "SERVICE_MISMATCH" not in codes

    print(
        "TEST 2 PASSED - ONE-SIDED SERVICE PUBLICATION "
        "IS INSUFFICIENT EVIDENCE"
    )

    # TEST 3: explicit canonical contradiction is hard mismatch.
    left = make(
        "Provider A",
        [
            service("Casco", "INSURANCE", True)
        ],
    )

    right = make(
        "Provider B",
        [
            service("Casco", "INSURANCE", False)
        ],
    )

    result = engine.compare(left, right)
    codes = {r.code for r in result.reasons}

    assert result.status == NOT_COMPARABLE
    assert "SERVICE_MISMATCH" in codes

    print(
        "TEST 3 PASSED - EXPLICIT CANONICAL SERVICE "
        "CONTRADICTION BLOCKS COMPARISON"
    )

    print(
        "\nALL NORMALIZED EVIDENCE-AWARE "
        "SERVICE INTEGRATION V3 TESTS PASSED"
    )


if __name__ == "__main__":
    main()
