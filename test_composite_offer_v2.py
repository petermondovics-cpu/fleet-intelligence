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
from models.composite_offer import (
    CompositeOffer,
)


def observed(text="Observed source"):
    return VehicleEvidence(
        status=EVIDENCE_OBSERVED,
        source_url="https://example.com/vehicle",
        source_text=text,
    )


def financial_observed(text="Observed source"):
    return FinancialEvidence(
        status=EVIDENCE_OBSERVED,
        source_url="https://example.com/offer",
        source_text=text,
    )


def unknown_vehicle():
    return VehicleEvidence(
        status=EVIDENCE_UNKNOWN
    )


def unknown_financial():
    return FinancialEvidence(
        status=EVIDENCE_UNKNOWN
    )


def create_base_offer():
    return Offer(
        provider="Ayvens",
        brand="BYD",
        model="ATTO 2",
        trim="Boost",
        fuel_type="PHEV",
        monthly_fee=189990,
        duration=48,
        mileage=20000,
        url="https://example.com/offer",
        scraped_at=datetime.now(),
    )


def create_vehicle():
    return VehicleSpecification(
        brand="BYD",
        model="ATTO 2",
        trim="Boost",
        fuel_type="PHEV",
        brand_evidence=observed("BYD"),
        model_evidence=observed("BYD ATTO 2"),
        trim_evidence=observed("Boost"),
        fuel_evidence=observed("Plug-in hibrid"),
        standard_equipment=[
            EquipmentItem(
                name="LED fényszóró",
                category="LIGHTING",
                included=True,
                standard=True,
                evidence=observed(
                    "LED fényszóró"
                ),
            )
        ],
        optional_equipment=[
            EquipmentItem(
                name="Panorámatető",
                category="COMFORT",
                included=True,
                standard=False,
                evidence=observed(
                    "Panorámatető – opcionális"
                ),
            )
        ],
    )


def create_services():
    return ServicePackage(
        items=[
            ServiceItem(
                name="Casco biztosítás",
                category="INSURANCE",
                included=True,
                evidence=financial_observed(
                    "Casco a havidíjban"
                ),
            ),
            ServiceItem(
                name="Üzemanyagkártya",
                category="FUEL",
                included=None,
                evidence=unknown_financial(),
            ),
        ]
    )


def create_financial():
    return FinancialConditions(
        monthly_fee=189990,
        down_payment=DownPayment(
            percent=20.0,
            amount=None,
            status=EVIDENCE_OBSERVED,
            evidence=financial_observed(
                "20% önerő"
            ),
        ),
        monthly_fee_evidence=financial_observed(
            "189 990 Ft/hó"
        ),
    )


def main():

    # ========================================================
    # TEST 1
    # COMPOSITE OFFER CREATES
    # ========================================================

    composite = CompositeOffer(
        offer=create_base_offer(),
        vehicle=create_vehicle(),
        services=create_services(),
        financial=create_financial(),
    )

    assert composite.provider == "Ayvens"
    assert composite.monthly_fee == 189990
    assert composite.duration == 48
    assert composite.mileage == 20000

    print(
        "TEST 1 PASSED - "
        "COMPOSITE OFFER CREATION"
    )

    # ========================================================
    # TEST 2
    # VEHICLE DATA AVAILABLE
    # ========================================================

    assert composite.vehicle.brand == "BYD"
    assert composite.vehicle.model == "ATTO 2"
    assert (
        composite.vehicle.trim
        == "Boost"
    )

    assert (
        composite.standard_equipment_count
        == 1
    )

    assert (
        composite.optional_equipment_count
        == 1
    )

    print(
        "TEST 2 PASSED - "
        "VEHICLE SPECIFICATION ATTACHED"
    )

    # ========================================================
    # TEST 3
    # SERVICES AVAILABLE
    # ========================================================

    assert composite.has_service(
        "INSURANCE",
        "Casco biztosítás",
    ) is True

    assert composite.has_service(
        "FUEL",
        "Üzemanyagkártya",
    ) is None

    assert (
        composite.included_service_count
        == 1
    )

    print(
        "TEST 3 PASSED - "
        "SERVICE PACKAGE ATTACHED"
    )

    # ========================================================
    # TEST 4
    # FINANCIAL CONDITIONS AVAILABLE
    # ========================================================

    assert (
        composite.financial.monthly_fee
        == 189990
    )

    assert (
        composite.financial.down_payment.percent
        == 20.0
    )

    assert (
        composite.down_payment_known
        is True
    )

    print(
        "TEST 4 PASSED - "
        "FINANCIAL CONDITIONS ATTACHED"
    )

    # ========================================================
    # TEST 5
    # MONTHLY FEE CONSISTENCY
    # ========================================================

    try:

        bad_financial = FinancialConditions(
            monthly_fee=199990,
            down_payment=DownPayment(
                percent=None,
                amount=None,
                status=EVIDENCE_UNKNOWN,
                evidence=unknown_financial(),
            ),
        )

        CompositeOffer(
            offer=create_base_offer(),
            vehicle=create_vehicle(),
            services=create_services(),
            financial=bad_financial,
        )

    except ValueError:
        pass

    else:
        raise AssertionError(
            "Composite offer accepted "
            "inconsistent monthly fee."
        )

    print(
        "TEST 5 PASSED - "
        "MONTHLY FEE CONSISTENCY"
    )

    # ========================================================
    # TEST 6
    # VEHICLE IDENTITY CONSISTENCY
    # ========================================================

    bad_vehicle = VehicleSpecification(
        brand="Toyota",
        model="Corolla",
        trim="Base",
        fuel_type="PHEV",
        brand_evidence=observed(),
        model_evidence=observed(),
        trim_evidence=unknown_vehicle(),
        fuel_evidence=observed(),
    )

    try:

        CompositeOffer(
            offer=create_base_offer(),
            vehicle=bad_vehicle,
            services=create_services(),
            financial=create_financial(),
        )

    except ValueError:
        pass

    else:
        raise AssertionError(
            "Composite offer accepted "
            "inconsistent vehicle identity."
        )

    print(
        "TEST 6 PASSED - "
        "VEHICLE IDENTITY CONSISTENCY"
    )

    # ========================================================
    # TEST 7
    # UNKNOWN SERVICE REMAINS UNKNOWN
    # ========================================================

    assert (
        composite.has_service(
            "FUEL",
            "Üzemanyagkártya",
        )
        is None
    )

    print(
        "TEST 7 PASSED - "
        "UNKNOWN SERVICE PRESERVED"
    )

    # ========================================================
    # TEST 8
    # ADVERTISED PRICE IS NOT NORMALIZED PRICE
    # ========================================================

    assert (
        composite.advertised_price
        == 189990
    )

    # There is intentionally no effective/normalized
    # price property in CompositeOffer V2 yet.

    assert not hasattr(
        composite,
        "effective_monthly_cost",
    )

    print(
        "TEST 8 PASSED - "
        "RAW PRICE KEPT SEPARATE"
    )

    print(
        "\nALL COMPOSITE OFFER V2 "
        "TESTS PASSED"
    )


if __name__ == "__main__":
    main()
