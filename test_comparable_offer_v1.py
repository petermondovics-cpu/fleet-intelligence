from datetime import datetime

from models.offer import Offer
from models.vehicle_specification import (
    EVIDENCE_OBSERVED,
    EVIDENCE_UNKNOWN,
    EquipmentItem,
    VehicleEvidence,
    VehicleSpecification,
)
from models.financial_conditions import (
    DownPayment,
    FinancialConditions,
    FinancialEvidence,
    ServiceItem,
    ServicePackage,
)
from models.composite_offer import CompositeOffer
from models.comparable_offer import (
    ComparableOfferEngine,
    COMPARABLE,
    NORMALIZATION_REQUIRED,
    NOT_COMPARABLE,
    INSUFFICIENT_EVIDENCE,
)


def ve(text="source"):
    return VehicleEvidence(
        status=EVIDENCE_OBSERVED,
        source_url="https://example.com",
        source_text=text,
    )


def vu():
    return VehicleEvidence(
        status=EVIDENCE_UNKNOWN
    )


def fe(text="source"):
    return FinancialEvidence(
        status=EVIDENCE_OBSERVED,
        source_url="https://example.com",
        source_text=text,
    )


def fu():
    return FinancialEvidence(
        status=EVIDENCE_UNKNOWN
    )


def make_offer(
    duration=48,
    mileage=20000,
    model="ATTO 2",
    trim="Boost",
    fuel="PHEV",
    services=None,
    equipment=None,
    monthly_fee=189990,
):
    offer = Offer(
        provider="Test",
        brand="BYD",
        model=model,
        trim=trim,
        fuel_type=fuel,
        monthly_fee=monthly_fee,
        duration=duration,
        mileage=mileage,
        url="https://example.com",
        scraped_at=datetime.now(),
    )

    equipment_items = equipment or []

    standard_equipment = [
        item
        for item in equipment_items
        if item.standard is True
    ]

    optional_equipment = [
        item
        for item in equipment_items
        if item.standard is False
    ]

    vehicle = VehicleSpecification(
        brand="BYD",
        model=model,
        trim=trim,
        fuel_type=fuel,
        brand_evidence=ve(),
        model_evidence=ve(),
        trim_evidence=ve(),
        fuel_evidence=ve(),
        standard_equipment=(
            standard_equipment
        ),
        optional_equipment=(
            optional_equipment
        ),
    )

    package = ServicePackage(
        items=(
            services or []
        )
    )

    financial = FinancialConditions(
        monthly_fee=monthly_fee,
        down_payment=DownPayment(
            percent=None,
            amount=None,
            status=EVIDENCE_UNKNOWN,
            evidence=fu(),
        ),
        monthly_fee_evidence=fe(
            f"{monthly_fee} Ft/hó"
        ),
    )

    return CompositeOffer(
        offer=offer,
        vehicle=vehicle,
        services=package,
        financial=financial,
    )


def main():

    engine = ComparableOfferEngine()

    # ========================================================
    # TEST 1 - IDENTICAL OFFERS
    # ========================================================

    a = make_offer()
    b = make_offer()

    result = engine.compare(a, b)

    assert result.status == COMPARABLE

    print(
        "TEST 1 PASSED - "
        "IDENTICAL OFFERS"
    )

    # ========================================================
    # TEST 2 - TERM NORMALIZATION
    # ========================================================

    a = make_offer(duration=48)
    b = make_offer(duration=60)

    result = engine.compare(a, b)

    assert (
        result.status
        == NORMALIZATION_REQUIRED
    )

    assert any(
        reason.code
        == "TERM_NORMALIZATION_REQUIRED"
        for reason in result.reasons
    )

    print(
        "TEST 2 PASSED - "
        "TERM NORMALIZATION REQUIRED"
    )

    # ========================================================
    # TEST 3 - MILEAGE NORMALIZATION
    # ========================================================

    a = make_offer(mileage=20000)
    b = make_offer(mileage=30000)

    result = engine.compare(a, b)

    assert (
        result.status
        == NORMALIZATION_REQUIRED
    )

    assert any(
        reason.code
        == "MILEAGE_NORMALIZATION_REQUIRED"
        for reason in result.reasons
    )

    print(
        "TEST 3 PASSED - "
        "MILEAGE NORMALIZATION REQUIRED"
    )

    # ========================================================
    # TEST 4 - TERM + MILEAGE
    # ========================================================

    a = make_offer(
        duration=48,
        mileage=20000,
    )

    b = make_offer(
        duration=60,
        mileage=30000,
    )

    result = engine.compare(a, b)

    assert (
        result.status
        == NORMALIZATION_REQUIRED
    )

    codes = {
        reason.code
        for reason in result.reasons
    }

    assert (
        "TERM_NORMALIZATION_REQUIRED"
        in codes
    )

    assert (
        "MILEAGE_NORMALIZATION_REQUIRED"
        in codes
    )

    print(
        "TEST 4 PASSED - "
        "TERM + MILEAGE NORMALIZATION"
    )

    # ========================================================
    # TEST 5 - MODEL MISMATCH
    # ========================================================

    a = make_offer(model="ATTO 2")
    b = make_offer(model="SEALION 5")

    result = engine.compare(a, b)

    assert (
        result.status
        == NOT_COMPARABLE
    )

    print(
        "TEST 5 PASSED - "
        "MODEL MISMATCH REJECTED"
    )

    # ========================================================
    # TEST 6 - FUEL MISMATCH
    # ========================================================

    a = make_offer(fuel="PHEV")
    b = make_offer(fuel="EV")

    result = engine.compare(a, b)

    assert (
        result.status
        == NOT_COMPARABLE
    )

    print(
        "TEST 6 PASSED - "
        "FUEL MISMATCH REJECTED"
    )

    # ========================================================
    # TEST 7 - SERVICE MISMATCH
    # ========================================================

    service_a = ServiceItem(
        name="Casco",
        category="INSURANCE",
        included=True,
        evidence=fe(
            "Casco included"
        ),
    )

    service_b = ServiceItem(
        name="Casco",
        category="INSURANCE",
        included=False,
        evidence=fe(
            "Casco excluded"
        ),
    )

    a = make_offer(
        services=[service_a]
    )

    b = make_offer(
        services=[service_b]
    )

    result = engine.compare(a, b)

    assert (
        result.status
        == NOT_COMPARABLE
    )

    print(
        "TEST 7 PASSED - "
        "SERVICE MISMATCH REJECTED"
    )

    # ========================================================
    # TEST 8 - UNKNOWN SERVICE DOES NOT BECOME MISMATCH
    # ========================================================

    service_unknown = ServiceItem(
        name="Üzemanyagkártya",
        category="FUEL",
        included=None,
        evidence=fu(),
    )

    service_included = ServiceItem(
        name="Üzemanyagkártya",
        category="FUEL",
        included=True,
        evidence=fe(
            "Fuel card included"
        ),
    )

    a = make_offer(
        services=[service_unknown]
    )

    b = make_offer(
        services=[service_included]
    )

    result = engine.compare(a, b)

    assert result.status == COMPARABLE

    print(
        "TEST 8 PASSED - "
        "UNKNOWN SERVICE NOT TREATED AS EXCLUSION"
    )

    # ========================================================
    # TEST 9 - EQUIPMENT MISMATCH
    # ========================================================

    equipment_a = EquipmentItem(
        name="Panorámatető",
        category="COMFORT",
        included=True,
        standard=True,
        evidence=ve(),
    )

    equipment_b = EquipmentItem(
        name="Panorámatető",
        category="COMFORT",
        included=False,
        standard=False,
        evidence=ve(),
    )

    a = make_offer(
        equipment=[equipment_a]
    )

    b = make_offer(
        equipment=[equipment_b]
    )

    result = engine.compare(a, b)

    assert (
        result.status
        == NOT_COMPARABLE
    )

    print(
        "TEST 9 PASSED - "
        "EQUIPMENT MISMATCH REJECTED"
    )

    # ========================================================
    # TEST 10 - UNKNOWN FUEL
    # ========================================================

    offer = Offer(
        provider="Test",
        brand="BYD",
        model="ATTO 2",
        trim="Boost",
        fuel_type="",
        monthly_fee=189990,
        duration=48,
        mileage=20000,
        url="https://example.com",
        scraped_at=datetime.now(),
    )

    vehicle = VehicleSpecification(
        brand="BYD",
        model="ATTO 2",
        trim="Boost",
        fuel_type=None,
        brand_evidence=ve(),
        model_evidence=ve(),
        trim_evidence=ve(),
        fuel_evidence=vu(),
    )

    composite = CompositeOffer(
        offer=offer,
        vehicle=vehicle,
        services=ServicePackage(),
        financial=FinancialConditions(
            monthly_fee=189990,
            down_payment=DownPayment(
                percent=None,
                amount=None,
                status=EVIDENCE_UNKNOWN,
                evidence=fu(),
            ),
            monthly_fee_evidence=fe(),
        ),
    )

    result = engine.compare(
        make_offer(),
        composite,
    )

    assert (
        result.status
        == INSUFFICIENT_EVIDENCE
    )

    print(
        "TEST 10 PASSED - "
        "UNKNOWN FUEL REJECTED FOR INSUFFICIENT EVIDENCE"
    )

    print(
        "\nALL COMPARABLE OFFER V1 "
        "TESTS PASSED"
    )


if __name__ == "__main__":
    main()
