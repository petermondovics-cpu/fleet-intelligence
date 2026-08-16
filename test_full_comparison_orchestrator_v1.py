from datetime import datetime

from models.offer import Offer
from models.vehicle_specification import (
    EVIDENCE_OBSERVED,
    EquipmentItem,
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
    EQUIPMENT_PUBLISHED,
    EquipmentEvidenceStatus,
)
from comparison.evidence_aware_comparable import (
    EvidenceAwareCompositeOffer,
)
from comparison.full_comparison_orchestrator import (
    FULL_BLOCKED,
    FULL_NOT_COMPARABLE,
    FULL_READY,
    FullComparisonOrchestrator,
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


def eq(name):
    return EquipmentItem(
        name=name,
        category="OTHER",
        included=True,
        standard=True,
        evidence=ve(name),
    )


def service(name, category):
    return ServiceItem(
        name=name,
        category=category,
        included=True,
        evidence=fe(name),
    )


def observed_dp(percent):
    return DownPayment(
        percent=percent,
        amount=None,
        status=EVIDENCE_OBSERVED,
        evidence=fe(
            f"{percent}% önerő"
        ),
    )


def unknown_dp():
    return DownPayment(
        percent=None,
        amount=None,
        status=EVIDENCE_UNKNOWN,
        evidence=FinancialEvidence(
            status=EVIDENCE_UNKNOWN
        ),
    )


def make_offer(
    provider,
    fee,
    duration,
    model="ATTO 2",
    trim="Boost",
    mileage=20000,
):
    return Offer(
        provider=provider,
        brand="BYD",
        model=model,
        trim=trim,
        fuel_type="PHEV",
        monthly_fee=fee,
        duration=duration,
        mileage=mileage,
        url="https://example.com",
        scraped_at=datetime.now(),
    )


def wrap(
    offer,
    down_payment,
    equipment_status=EQUIPMENT_PUBLISHED,
    equipment=None,
    services=None,
):
    vehicle = VehicleSpecification(
        brand=offer.brand,
        model=offer.model,
        trim=offer.trim,
        fuel_type=offer.fuel_type,
        brand_evidence=ve(offer.brand),
        model_evidence=ve(offer.model),
        trim_evidence=ve(offer.trim),
        fuel_evidence=ve(offer.fuel_type),
        standard_equipment=(
            equipment or []
        ),
        optional_equipment=[],
    )

    financial = FinancialConditions(
        monthly_fee=offer.monthly_fee,
        down_payment=down_payment,
        other_one_off_fees=0,
        other_recurring_fees=0,
        monthly_fee_evidence=fe(
            f"{offer.monthly_fee} Ft/hó"
        ),
    )

    return EvidenceAwareCompositeOffer(
        composite=CompositeOffer(
            offer=offer,
            vehicle=vehicle,
            services=ServicePackage(
                items=services or []
            ),
            financial=financial,
        ),
        equipment_evidence=EquipmentEvidenceStatus(
            standard_status=equipment_status,
            optional_status=equipment_status,
        ),
    )


def common_services(provider):
    if provider == "Arval":
        return [
            service(
                "Közúti segítségnyújtás",
                "MOBILITY",
            )
        ]

    return [
        service(
            "Assistance szolgáltatás",
            "MOBILITY",
        )
    ]


def main():

    engine = FullComparisonOrchestrator()

    # ========================================================
    # TEST 1 - EVERYTHING DIRECTLY COMPARABLE
    # ========================================================

    a_offer = make_offer(
        "Provider A",
        180000,
        48,
    )

    b_offer = make_offer(
        "Provider B",
        190000,
        48,
    )

    # Same service wording is canonicalized.
    common = [
        service(
            "Assistance szolgáltatás",
            "MOBILITY",
        )
    ]

    equipment = [
        eq("Fűthető kormánykerék")
    ]

    result = engine.compare(
        wrap(
            a_offer,
            observed_dp(20),
            equipment=equipment,
            services=common,
        ),
        wrap(
            b_offer,
            observed_dp(20),
            equipment=equipment,
            services=common,
        ),
        observed_offer_pool=[
            a_offer,
            b_offer,
        ],
    )

    assert result.status == FULL_READY
    assert result.price_comparison_allowed is True
    assert result.price_winner == "Provider A"
    assert result.normalized_monthly_fee_left == 180000
    assert result.normalized_monthly_fee_right == 190000

    print(
        "TEST 1 PASSED - "
        "FULLY COMPARABLE OFFERS PRODUCE VALID PRICE WINNER"
    )

    # ========================================================
    # TEST 2 - UNKNOWN DOWN PAYMENT BLOCKS WINNER
    # ========================================================

    result = engine.compare(
        wrap(
            a_offer,
            unknown_dp(),
            equipment=equipment,
            services=common,
        ),
        wrap(
            b_offer,
            unknown_dp(),
            equipment=equipment,
            services=common,
        ),
        observed_offer_pool=[
            a_offer,
            b_offer,
        ],
    )

    assert result.status == FULL_BLOCKED
    assert result.price_comparison_allowed is False
    assert result.price_winner is None
    assert (
        "DOWN_PAYMENT_EVIDENCE_INCOMPLETE"
        in result.blocker_codes
    )

    print(
        "TEST 2 PASSED - "
        "UNKNOWN DOWN PAYMENT BLOCKS PRICE WINNER"
    )

    # ========================================================
    # TEST 3 - CONTRACT EVIDENCE NORMALIZES 60 -> 48
    # ========================================================

    arval_48 = make_offer(
        "Arval",
        180000,
        48,
        trim="Boost",
    )

    arval_60 = make_offer(
        "Arval",
        192000,
        60,
        trim="Boost",
    )

    ayvens_48 = make_offer(
        "Ayvens",
        190000,
        48,
        model="ATTO 2 DM-i",
        trim="Boost",
    )

    result = engine.compare(
        wrap(
            arval_60,
            observed_dp(20),
            equipment=equipment,
            services=common_services("Arval"),
        ),
        wrap(
            ayvens_48,
            observed_dp(20),
            equipment=equipment,
            services=common_services("Ayvens"),
        ),
        observed_offer_pool=[
            arval_48,
            arval_60,
            ayvens_48,
        ],
    )

    assert result.status == FULL_READY
    assert result.price_comparison_allowed is True
    assert result.normalized_monthly_fee_left == 180000
    assert result.normalized_monthly_fee_right == 190000
    assert result.price_winner == "Arval"

    print(
        "TEST 3 PASSED - "
        "OBSERVED CONTRACT EVIDENCE ENABLES NORMALIZED WINNER"
    )

    # ========================================================
    # TEST 4 - EQUIPMENT NOT PUBLISHED BLOCKS WINNER
    # ========================================================

    result = engine.compare(
        wrap(
            arval_48,
            observed_dp(20),
            equipment_status=EQUIPMENT_NOT_PUBLISHED,
            services=common_services("Arval"),
        ),
        wrap(
            ayvens_48,
            observed_dp(20),
            equipment=equipment,
            services=common_services("Ayvens"),
        ),
        observed_offer_pool=[
            arval_48,
            ayvens_48,
        ],
    )

    assert result.status == FULL_BLOCKED
    assert result.price_winner is None
    assert (
        "EQUIPMENT_EVIDENCE_INCOMPLETE"
        in result.blocker_codes
    )

    print(
        "TEST 4 PASSED - "
        "MISSING EQUIPMENT PUBLICATION BLOCKS WINNER"
    )

    # ========================================================
    # TEST 5 - DOWN PAYMENT MISMATCH IS HARD
    # ========================================================

    result = engine.compare(
        wrap(
            a_offer,
            observed_dp(10),
            equipment=equipment,
            services=common,
        ),
        wrap(
            b_offer,
            observed_dp(20),
            equipment=equipment,
            services=common,
        ),
        observed_offer_pool=[
            a_offer,
            b_offer,
        ],
    )

    assert result.status == FULL_NOT_COMPARABLE
    assert result.price_winner is None
    assert "DOWN_PAYMENT_MISMATCH" in result.blocker_codes

    print(
        "TEST 5 PASSED - "
        "OBSERVED DOWN PAYMENT MISMATCH IS HARD BLOCKER"
    )

    print(
        "\nALL FULL COMPARISON ORCHESTRATOR V1 TESTS PASSED"
    )


if __name__ == "__main__":
    main()
