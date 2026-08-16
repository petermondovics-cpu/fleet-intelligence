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
    ServiceItem,
    ServicePackage,
)
from models.composite_offer import (
    CompositeOffer,
)
from composite_comparison.engine import (
    CompositeComparisonEngine,
    PRICE_COMPARABLE,
    PRICE_UNAVAILABLE,
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


def make_composite(
    provider,
    fee,
    duration=48,
    mileage=20000,
    model="ATTO 2",
    trim="Boost",
    fuel="PHEV",
    services=None,
    standard_equipment=None,
    optional_equipment=None,
):

    offer = Offer(
        provider=provider,
        brand="BYD",
        model=model,
        trim=trim,
        fuel_type=fuel,
        monthly_fee=fee,
        duration=duration,
        mileage=mileage,
        url="https://example.com",
        scraped_at=datetime.now(),
    )

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
            standard_equipment or []
        ),
        optional_equipment=(
            optional_equipment or []
        ),
    )

    financial = FinancialConditions(
        monthly_fee=fee,
        down_payment=DownPayment(
            percent=None,
            amount=None,
            status=EVIDENCE_UNKNOWN,
            evidence=fe_unknown(),
        ),
        monthly_fee_evidence=(
            fe_observed(
                f"{fee} Ft/hó"
            )
        ),
    )

    return CompositeOffer(
        offer=offer,
        vehicle=vehicle,
        services=ServicePackage(
            items=services or []
        ),
        financial=financial,
    )


def main():

    engine = CompositeComparisonEngine()

    # ========================================================
    # TEST 1 - DIRECT COMPARISON
    # ========================================================

    arval = make_composite(
        "Arval",
        192000,
    )

    ayvens = make_composite(
        "Ayvens",
        189000,
    )

    result = engine.compare(
        arval,
        ayvens,
    )

    assert (
        result.status
        == PRICE_COMPARABLE
    )

    assert (
        result.price_winner
        == "Ayvens"
    )

    assert (
        result.comparable_monthly_fee_a
        == 192000
    )

    assert (
        result.comparable_monthly_fee_b
        == 189000
    )

    print(
        "TEST 1 PASSED - "
        "DIRECT COMPOSITE PRICE COMPARISON"
    )

    # ========================================================
    # TEST 2 - TERM DIFFERENCE BLOCKED WITHOUT EVIDENCE
    # ========================================================

    arval = make_composite(
        "Arval",
        192000,
        duration=60,
    )

    ayvens = make_composite(
        "Ayvens",
        189000,
        duration=48,
    )

    result = engine.compare(
        arval,
        ayvens,
    )

    assert (
        result.status
        == PRICE_UNAVAILABLE
    )

    assert (
        result.price_winner
        is None
    )

    assert (
        result.normalization
        is not None
    )

    assert (
        result.normalization
        .normalized_price_available
        is False
    )

    print(
        "TEST 2 PASSED - "
        "TERM DIFFERENCE BLOCKED WITHOUT EVIDENCE"
    )

    # ========================================================
    # TEST 3 - SERVICE MISMATCH BLOCKS PRICE
    # ========================================================

    casco_in = ServiceItem(
        name="Casco",
        category="INSURANCE",
        included=True,
        evidence=fe_observed(
            "Casco included"
        ),
    )

    casco_out = ServiceItem(
        name="Casco",
        category="INSURANCE",
        included=False,
        evidence=fe_observed(
            "Casco excluded"
        ),
    )

    arval = make_composite(
        "Arval",
        180000,
        services=[casco_in],
    )

    ayvens = make_composite(
        "Ayvens",
        190000,
        services=[casco_out],
    )

    result = engine.compare(
        arval,
        ayvens,
    )

    assert (
        result.status
        == PRICE_UNAVAILABLE
    )

    assert (
        result.price_winner
        is None
    )

    assert (
        result.legacy_comparison
        is None
    )

    print(
        "TEST 3 PASSED - "
        "SERVICE MISMATCH BLOCKS PRICE"
    )

    # ========================================================
    # TEST 4 - EQUIPMENT MISMATCH BLOCKS PRICE
    # ========================================================

    panorama_in = EquipmentItem(
        name="Panorámatető",
        category="COMFORT",
        included=True,
        standard=False,
        evidence=ve(
            "Panorámatető included"
        ),
    )

    panorama_out = EquipmentItem(
        name="Panorámatető",
        category="COMFORT",
        included=False,
        standard=False,
        evidence=ve(
            "Panorámatető excluded"
        ),
    )

    arval = make_composite(
        "Arval",
        180000,
        optional_equipment=[
            panorama_in
        ],
    )

    ayvens = make_composite(
        "Ayvens",
        190000,
        optional_equipment=[
            panorama_out
        ],
    )

    result = engine.compare(
        arval,
        ayvens,
    )

    assert (
        result.status
        == PRICE_UNAVAILABLE
    )

    assert result.price_winner is None

    print(
        "TEST 4 PASSED - "
        "EQUIPMENT MISMATCH BLOCKS PRICE"
    )

    # ========================================================
    # TEST 5 - UNKNOWN SERVICE DOES NOT CREATE FALSE MISMATCH
    # ========================================================

    fuel_unknown = ServiceItem(
        name="Üzemanyagkártya",
        category="FUEL",
        included=None,
        evidence=fe_unknown(),
    )

    fuel_included = ServiceItem(
        name="Üzemanyagkártya",
        category="FUEL",
        included=True,
        evidence=fe_observed(
            "Fuel card included"
        ),
    )

    arval = make_composite(
        "Arval",
        180000,
        services=[fuel_unknown],
    )

    ayvens = make_composite(
        "Ayvens",
        190000,
        services=[fuel_included],
    )

    result = engine.compare(
        arval,
        ayvens,
    )

    assert (
        result.status
        == PRICE_COMPARABLE
    )

    assert (
        result.price_winner
        == "Arval"
    )

    print(
        "TEST 5 PASSED - "
        "UNKNOWN SERVICE PRESERVED THROUGH INTEGRATION"
    )

    print(
        "\nALL COMPOSITE COMPARISON "
        "INTEGRATION V1 TESTS PASSED"
    )


if __name__ == "__main__":
    main()
