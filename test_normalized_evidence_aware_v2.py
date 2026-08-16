from datetime import datetime

from models.offer import Offer
from models.vehicle_specification import (
    EVIDENCE_OBSERVED,
    EquipmentItem,
    VehicleEvidence,
    VehicleSpecification,
)
from models.financial_conditions import (
    EVIDENCE_UNKNOWN,
    DownPayment,
    FinancialConditions,
    FinancialEvidence,
    ServicePackage,
)
from models.composite_offer import CompositeOffer
from models.equipment_evidence import (
    EQUIPMENT_PUBLISHED,
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
    COMPARABLE,
    INSUFFICIENT_EVIDENCE,
    NORMALIZATION_REQUIRED,
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


def make(
    provider,
    model,
    trim,
    duration,
    equipment=None,
):
    offer = Offer(
        provider=provider,
        brand="BYD",
        model=model,
        trim=trim,
        fuel_type="PHEV",
        monthly_fee=190000,
        duration=duration,
        mileage=20000,
        url="https://example.com",
        scraped_at=datetime.now(),
    )

    vehicle = VehicleSpecification(
        brand="BYD",
        model=model,
        trim=trim,
        fuel_type="PHEV",
        brand_evidence=ve("BYD"),
        model_evidence=ve(model),
        trim_evidence=ve(trim),
        fuel_evidence=ve("PHEV"),
        standard_equipment=(
            equipment or []
        ),
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
        monthly_fee_evidence=fe(
            "190000 Ft/hó"
        ),
    )

    return CompositeOffer(
        offer=offer,
        vehicle=vehicle,
        services=ServicePackage(),
        financial=financial,
    )


def wrap(
    composite,
    status,
):
    return EvidenceAwareCompositeOffer(
        composite=composite,
        equipment_evidence=EquipmentEvidenceStatus(
            standard_status=status,
            optional_status=status,
        ),
    )


def eq(name):
    return EquipmentItem(
        name=name,
        category="OTHER",
        included=True,
        standard=True,
        evidence=ve(name),
    )


def main():

    engine = (
        NormalizedEvidenceAwareComparableEngine()
    )

    # TEST 1
    # Same canonical model/fuel, different trim, Arval not published:
    # must NOT be hard trim mismatch.
    arval = wrap(
        make(
            "Arval",
            "ATTO 2",
            "1.5 PHEV BOOST AT",
            60,
        ),
        EQUIPMENT_NOT_PUBLISHED,
    )

    ayvens = wrap(
        make(
            "Ayvens",
            "ATTO 2 DM-i",
            "Active 166 HP",
            48,
            equipment=[
                eq("Adaptív tempomat")
            ],
        ),
        EQUIPMENT_PUBLISHED,
    )

    result = engine.compare(
        arval,
        ayvens,
    )

    assert (
        result.status
        == INSUFFICIENT_EVIDENCE
    )

    codes = {
        r.code
        for r in result.reasons
    }

    assert (
        "VEHICLE_VARIANT_DIFFERENCE"
        in codes
    )
    assert (
        "EQUIPMENT_EVIDENCE_INCOMPLETE"
        in codes
    )
    assert (
        "VEHICLE_TRIM_MISMATCH"
        not in codes
    )

    print(
        "TEST 1 PASSED - "
        "VARIANT DIFFERENCE DEFERS TO EQUIPMENT EVIDENCE"
    )

    # TEST 2
    # Different trim wording but identical published equipment:
    # contract difference remains the only normalization barrier.
    common_equipment = [
        eq("Adaptív tempomat"),
        eq("LED fényszóró"),
    ]

    left = wrap(
        make(
            "Provider A",
            "ATTO 2",
            "Boost",
            60,
            equipment=common_equipment,
        ),
        EQUIPMENT_PUBLISHED,
    )

    right = wrap(
        make(
            "Provider B",
            "ATTO 2 DM-i",
            "Active",
            48,
            equipment=common_equipment,
        ),
        EQUIPMENT_PUBLISHED,
    )

    result = engine.compare(
        left,
        right,
    )

    assert (
        result.status
        == NORMALIZATION_REQUIRED
    )

    print(
        "TEST 2 PASSED - "
        "EQUIVALENT EQUIPMENT ALLOWS CONTRACT NORMALIZATION"
    )

    # TEST 3
    # Different published equipment sets require value normalization.
    right = wrap(
        make(
            "Provider B",
            "ATTO 2 DM-i",
            "Active",
            60,
            equipment=[
                eq("Adaptív tempomat"),
                eq("LED fényszóró"),
                eq("Panorámatető"),
            ],
        ),
        EQUIPMENT_PUBLISHED,
    )

    left = wrap(
        make(
            "Provider A",
            "ATTO 2",
            "Boost",
            60,
            equipment=[
                eq("Adaptív tempomat"),
                eq("LED fényszóró"),
            ],
        ),
        EQUIPMENT_PUBLISHED,
    )

    result = engine.compare(
        left,
        right,
    )

    assert (
        result.status
        == INSUFFICIENT_EVIDENCE
    )

    assert any(
        r.code
        == "EQUIPMENT_VALUE_NORMALIZATION_REQUIRED"
        for r in result.reasons
    )

    print(
        "TEST 3 PASSED - "
        "DIFFERENT EQUIPMENT SETS REQUIRE VALUE NORMALIZATION"
    )

    print(
        "\nALL NORMALIZED EVIDENCE-AWARE "
        "COMPARISON V2 TESTS PASSED"
    )


if __name__ == "__main__":
    main()
