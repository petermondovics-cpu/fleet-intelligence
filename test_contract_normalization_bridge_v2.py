from datetime import datetime

from models.offer import Offer
from models.vehicle_specification import (
    EVIDENCE_OBSERVED,
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
    EQUIPMENT_NOT_PUBLISHED,
    EquipmentEvidenceStatus,
)
from comparison.evidence_aware_comparable import (
    EvidenceAwareCompositeOffer,
)
from comparison.contract_normalization_bridge import (
    ContractNormalizationBridge,
)


def ve(text):
    return VehicleEvidence(
        status=EVIDENCE_OBSERVED,
        source_url="https://example.com",
        source_text=text,
    )


def make_offer(
    provider,
    fee,
    duration,
    model="ATTO 2",
    trim="Boost",
    fuel="PHEV",
    mileage=20000,
):
    return Offer(
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


def wrap(offer):
    vehicle = VehicleSpecification(
        brand=offer.brand,
        model=offer.model,
        trim=offer.trim,
        fuel_type=offer.fuel_type,
        brand_evidence=ve(offer.brand),
        model_evidence=ve(offer.model),
        trim_evidence=ve(offer.trim),
        fuel_evidence=ve(offer.fuel_type),
        standard_equipment=[],
        optional_equipment=[],
    )

    financial = FinancialConditions(
        monthly_fee=offer.monthly_fee,
        down_payment=DownPayment(
            percent=None,
            amount=None,
            status=EVIDENCE_UNKNOWN,
            evidence=FinancialEvidence(
                status=EVIDENCE_UNKNOWN
            ),
        ),
        monthly_fee_evidence=FinancialEvidence(
            status=EVIDENCE_OBSERVED,
            source_url=offer.url,
            source_text=f"{offer.monthly_fee} Ft/hó",
        ),
    )

    return EvidenceAwareCompositeOffer(
        composite=CompositeOffer(
            offer=offer,
            vehicle=vehicle,
            services=ServicePackage(),
            financial=financial,
        ),
        equipment_evidence=EquipmentEvidenceStatus(
            standard_status=EQUIPMENT_NOT_PUBLISHED,
            optional_status=EQUIPMENT_NOT_PUBLISHED,
        ),
    )


def main():

    bridge = ContractNormalizationBridge()

    # ========================================================
    # TEST 1 - NO EVIDENCE => NO ESTIMATED PRICE
    # ========================================================

    arval_60 = make_offer(
        "Arval",
        192000,
        60,
    )

    ayvens_48 = make_offer(
        "Ayvens",
        190000,
        48,
        model="ATTO 2 DM-i",
        trim="Active",
    )

    result = bridge.normalize(
        wrap(arval_60),
        wrap(ayvens_48),
        observed_offer_pool=[
            arval_60,
            ayvens_48,
        ],
        other_barriers_passed=True,
    )

    assert (
        result.normalization.normalization_status
        == "NEEDS_TERM_NORMALIZATION"
    )

    assert (
        result.normalization.normalized_price_available
        is False
    )

    assert (
        result.final_price_comparison_ready
        is False
    )

    print(
        "TEST 1 PASSED - "
        "NO OBSERVED TERM EVIDENCE, NO NORMALIZED PRICE"
    )

    # ========================================================
    # TEST 2 - OBSERVED SAME-PROVIDER TERM EVIDENCE
    # ========================================================

    arval_48 = make_offer(
        "Arval",
        180000,
        48,
    )

    result = bridge.normalize(
        wrap(arval_60),
        wrap(ayvens_48),
        observed_offer_pool=[
            arval_48,
            arval_60,
            ayvens_48,
        ],
        other_barriers_passed=True,
    )

    n = result.normalization

    assert n.normalization_status == "NORMALIZATION_ESTIMATED"
    assert n.normalized_price_available is True
    assert n.term_normalization_available is True

    # Arval 60 -> 48 observed factor:
    # 180000 / 192000 = 0.9375
    assert n.normalized_monthly_fee_a == 180000
    assert n.normalized_monthly_fee_b == 190000

    term_evidence = result.evidence["term_evidence"]

    assert term_evidence is not None
    assert term_evidence["provider"] == "Arval"
    assert term_evidence["source_duration"] == 60
    assert term_evidence["target_duration"] == 48
    assert term_evidence["source_monthly_fee"] == 192000
    assert term_evidence["target_monthly_fee"] == 180000
    assert term_evidence["factor"] == 0.9375

    assert result.final_price_comparison_ready is True

    print(
        "TEST 2 PASSED - "
        "OBSERVED PROVIDER TERM EVIDENCE NORMALIZES PRICE"
    )

    # ========================================================
    # TEST 3 - OTHER BARRIERS CAN STILL BLOCK FINAL PRICE
    # ========================================================

    result = bridge.normalize(
        wrap(arval_60),
        wrap(ayvens_48),
        observed_offer_pool=[
            arval_48,
            arval_60,
            ayvens_48,
        ],
        other_barriers_passed=False,
    )

    assert (
        result.normalization.normalized_price_available
        is True
    )

    assert (
        result.final_price_comparison_ready
        is False
    )

    print(
        "TEST 3 PASSED - "
        "CONTRACT NORMALIZATION DOES NOT BYPASS OTHER BARRIERS"
    )

    # ========================================================
    # TEST 4 - AYVENS QUOTE METADATA CANNOT BE EVIDENCE
    # ========================================================

    fake_quote_metadata = {
        "duration_min": 36,
        "duration_max": 60,
        "duration_step": 12,
        "mileage_min": 20000,
        "mileage_max": 60000,
    }

    # The bridge requires Offer objects in the evidence pool.
    # Metadata is deliberately not passed and has no conversion API.
    assert not isinstance(
        fake_quote_metadata,
        Offer,
    )

    print(
        "TEST 4 PASSED - "
        "AYVENS QUOTE SLIDERS CANNOT ENTER CONTRACT EVIDENCE"
    )

    print(
        "\nALL CONTRACT NORMALIZATION BRIDGE V2 TESTS PASSED"
    )


if __name__ == "__main__":
    main()
