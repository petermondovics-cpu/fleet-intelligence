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
from models.comparable_offer import (
    COMPARABLE,
    NOT_COMPARABLE,
    INSUFFICIENT_EVIDENCE,
)
from models.equipment_evidence import (
    EQUIPMENT_PUBLISHED,
    EQUIPMENT_NOT_PUBLISHED,
    EQUIPMENT_PARSING_UNRESOLVED,
    EquipmentEvidenceStatus,
)
from comparison.evidence_aware_comparable import (
    EvidenceAwareCompositeOffer,
    EvidenceAwareComparableOfferEngine,
)


def ve(text="source"):
    return VehicleEvidence(
        status=EVIDENCE_OBSERVED,
        source_url="https://example.com",
        source_text=text,
    )


def fe_observed(text="source"):
    return FinancialEvidence(
        status=EVIDENCE_OBSERVED,
        source_url="https://example.com",
        source_text=text,
    )


def fe_unknown():
    return FinancialEvidence(
        status=EVIDENCE_UNKNOWN
    )


def equipment(
    name,
    included=True,
    standard=True,
):
    return EquipmentItem(
        name=name,
        category="OTHER",
        included=included,
        standard=standard,
        evidence=ve(name),
    )


def make_composite(
    provider,
    standard_equipment=None,
    optional_equipment=None,
):
    offer = Offer(
        provider=provider,
        brand="Opel",
        model="Astra",
        trim="Edition",
        fuel_type="Diesel",
        monthly_fee=180000,
        duration=48,
        mileage=20000,
        url="https://example.com",
        scraped_at=datetime.now(),
    )

    vehicle = VehicleSpecification(
        brand="Opel",
        model="Astra",
        trim="Edition",
        fuel_type="Diesel",
        brand_evidence=ve("Opel"),
        model_evidence=ve("Astra"),
        trim_evidence=ve("Edition"),
        fuel_evidence=ve("Diesel"),
        standard_equipment=(
            standard_equipment or []
        ),
        optional_equipment=(
            optional_equipment or []
        ),
    )

    financial = FinancialConditions(
        monthly_fee=180000,
        down_payment=DownPayment(
            percent=None,
            amount=None,
            status=EVIDENCE_UNKNOWN,
            evidence=fe_unknown(),
        ),
        monthly_fee_evidence=fe_observed(
            "180000 Ft/hó"
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
    standard_status,
    optional_status,
):
    return EvidenceAwareCompositeOffer(
        composite=composite,
        equipment_evidence=EquipmentEvidenceStatus(
            standard_status=standard_status,
            optional_status=optional_status,
        ),
    )


def main():

    engine = (
        EvidenceAwareComparableOfferEngine()
    )

    # ========================================================
    # TEST 1 - AYVENS PUBLISHED VS ARVAL NOT_PUBLISHED
    # ========================================================

    ayvens = wrap(
        make_composite(
            "Ayvens",
            standard_equipment=[
                equipment(
                    "Adaptív tempomat",
                    True,
                    True,
                )
            ],
            optional_equipment=[
                equipment(
                    "Metálfényezés",
                    True,
                    False,
                )
            ],
        ),
        EQUIPMENT_PUBLISHED,
        EQUIPMENT_PUBLISHED,
    )

    arval = wrap(
        make_composite(
            "Arval",
        ),
        EQUIPMENT_NOT_PUBLISHED,
        EQUIPMENT_NOT_PUBLISHED,
    )

    result = engine.compare(
        ayvens,
        arval,
    )

    assert (
        result.status
        == INSUFFICIENT_EVIDENCE
    )

    assert any(
        reason.code
        == "EQUIPMENT_EVIDENCE_INCOMPLETE"
        for reason in result.reasons
    )

    print(
        "TEST 1 PASSED - "
        "AYVENS PUBLISHED VS ARVAL NOT_PUBLISHED "
        "IS INSUFFICIENT_EVIDENCE"
    )

    # ========================================================
    # TEST 2 - NOT_PUBLISHED IS NOT ZERO EQUIPMENT
    # ========================================================

    assert (
        arval.composite
        .standard_equipment_count
        == 0
    )

    assert (
        arval.equipment_evidence
        .standard_status
        == EQUIPMENT_NOT_PUBLISHED
    )

    print(
        "TEST 2 PASSED - "
        "EMPTY LIST PRESERVES NOT_PUBLISHED MEANING"
    )

    # ========================================================
    # TEST 3 - BOTH PUBLISHED + SAME EQUIPMENT
    # ========================================================

    a = wrap(
        make_composite(
            "Provider A",
            standard_equipment=[
                equipment(
                    "Adaptív tempomat",
                    True,
                    True,
                )
            ],
        ),
        EQUIPMENT_PUBLISHED,
        EQUIPMENT_PUBLISHED,
    )

    b = wrap(
        make_composite(
            "Provider B",
            standard_equipment=[
                equipment(
                    "Adaptív tempomat",
                    True,
                    True,
                )
            ],
        ),
        EQUIPMENT_PUBLISHED,
        EQUIPMENT_PUBLISHED,
    )

    result = engine.compare(
        a,
        b,
    )

    assert result.status == COMPARABLE

    print(
        "TEST 3 PASSED - "
        "BOTH PUBLISHED + SAME EQUIPMENT COMPARABLE"
    )

    # ========================================================
    # TEST 4 - BOTH PUBLISHED + EXPLICIT MISMATCH
    # ========================================================

    a = wrap(
        make_composite(
            "Provider A",
            optional_equipment=[
                equipment(
                    "Panorámatető",
                    True,
                    False,
                )
            ],
        ),
        EQUIPMENT_PUBLISHED,
        EQUIPMENT_PUBLISHED,
    )

    b = wrap(
        make_composite(
            "Provider B",
            optional_equipment=[
                equipment(
                    "Panorámatető",
                    False,
                    False,
                )
            ],
        ),
        EQUIPMENT_PUBLISHED,
        EQUIPMENT_PUBLISHED,
    )

    result = engine.compare(
        a,
        b,
    )

    assert result.status == NOT_COMPARABLE

    print(
        "TEST 4 PASSED - "
        "PUBLISHED EQUIPMENT MISMATCH STILL REJECTED"
    )

    # ========================================================
    # TEST 5 - PARSING_UNRESOLVED BLOCKS COMPARISON
    # ========================================================

    unresolved = wrap(
        make_composite(
            "Provider C",
        ),
        EQUIPMENT_PARSING_UNRESOLVED,
        EQUIPMENT_PUBLISHED,
    )

    result = engine.compare(
        a,
        unresolved,
    )

    assert (
        result.status
        == INSUFFICIENT_EVIDENCE
    )

    print(
        "TEST 5 PASSED - "
        "PARSING_UNRESOLVED BLOCKS PRICE COMPARISON"
    )

    print(
        "\nALL EQUIPMENT EVIDENCE STATUS V1 "
        "TESTS PASSED"
    )


if __name__ == "__main__":
    main()
