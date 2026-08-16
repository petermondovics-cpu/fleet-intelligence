from datetime import datetime

from comparison.engine import ComparisonResult
from contract_normalization.engine import (
    ContractNormalizationEngine,
)
from models.offer import Offer


def create_offer(
    provider,
    fee,
    duration,
    mileage=20000,
):
    return Offer(
        provider=provider,
        brand="BYD",
        model="ATTO 2",
        trim="",
        fuel_type="EV",
        monthly_fee=fee,
        duration=duration,
        mileage=mileage,
        url="",
        scraped_at=datetime.now(),
    )


def create_comparison(
    offer_a,
    offer_b,
):
    comparable = (
        offer_a.duration == offer_b.duration
        and offer_a.mileage == offer_b.mileage
    )

    return ComparisonResult(
        brand="BYD",
        model="ATTO 2",
        fuel_type_a=offer_a.fuel_type,
        fuel_type_b=offer_b.fuel_type,
        vehicle_confidence=100,
        vehicle_match_type="EXACT_MATCH",
        contract_comparable=comparable,
        contract_difference=(
            ""
            if comparable
            else _contract_difference(
                offer_a,
                offer_b,
            )
        ),
        duration_similarity=100,
        mileage_similarity=100,
        contract_similarity=100,
        offers=[
            offer_a,
            offer_b,
        ],
        best_provider=(
            offer_a.provider
            if offer_a.monthly_fee
            <= offer_b.monthly_fee
            else offer_b.provider
        ),
        best_monthly_fee=min(
            offer_a.monthly_fee,
            offer_b.monthly_fee,
        ),
        price_difference=abs(
            offer_a.monthly_fee
            - offer_b.monthly_fee
        ),
        annual_saving=(
            abs(
                offer_a.monthly_fee
                - offer_b.monthly_fee
            )
            * 12
        ),
        price_winner=(
            "NOT_COMPARABLE"
            if not comparable
            else (
                offer_a.provider
                if offer_a.monthly_fee
                < offer_b.monthly_fee
                else offer_b.provider
            )
        ),
        price_winner_is_valid=(
            comparable
        ),
        price_difference_percent=0.0,
    )


def _contract_difference(
    offer_a,
    offer_b,
):
    differences = []

    if offer_a.duration != offer_b.duration:
        differences.append(
            f"Duration differs: "
            f"{offer_a.duration} vs "
            f"{offer_b.duration} months."
        )

    if offer_a.mileage != offer_b.mileage:
        differences.append(
            f"Mileage differs: "
            f"{offer_a.mileage:,} vs "
            f"{offer_b.mileage:,} km/year."
        )

    return "; ".join(differences)


def main():

    engine = ContractNormalizationEngine()

    # =================================================
    # TEST 1
    # IDENTICAL CONTRACT
    # =================================================

    arval = create_offer(
        "Arval",
        180000,
        48,
        20000,
    )

    ayvens = create_offer(
        "Ayvens",
        190000,
        48,
        20000,
    )

    result = engine.normalize(
        create_comparison(
            arval,
            ayvens,
        )
    )

    assert (
        result.normalization_status
        == "NORMALIZED"
    )

    assert (
        result.normalization_method
        == "NOMINAL_PRICE"
    )

    assert (
        result.normalized_price_available
        is True
    )

    assert (
        result.normalized_monthly_fee_a
        == 180000
    )

    assert (
        result.normalized_monthly_fee_b
        == 190000
    )

    assert (
        result.duration_difference
        == 0
    )

    assert (
        result.mileage_difference
        == 0
    )

    assert (
        result.contract_similarity
        == 100
    )

    assert (
        result.normalization_confidence
        == 100
    )

    assert (
        result.normalization_quality
        == "DIRECT"
    )

    print(
        "TEST 1 PASSED - "
        "IDENTICAL CONTRACT"
    )

    # =================================================
    # TEST 2
    # TERM DIFFERENCE
    # =================================================

    arval = create_offer(
        "Arval",
        192312,
        60,
        20000,
    )

    ayvens = create_offer(
        "Ayvens",
        189990,
        48,
        20000,
    )

    result = engine.normalize(
        create_comparison(
            arval,
            ayvens,
        )
    )

    assert (
        result.normalization_status
        == "NEEDS_TERM_NORMALIZATION"
    )

    assert (
        result.normalization_method
        == "NONE"
    )

    assert (
        result.normalized_price_available
        is False
    )

    assert (
        result.normalized_monthly_fee_a
        is None
    )

    assert (
        result.normalized_monthly_fee_b
        is None
    )

    assert (
        result.duration_difference
        == 12
    )

    assert (
        result.mileage_difference
        == 0
    )

    assert (
        result.duration_similarity
        == 85
    )

    assert (
        result.mileage_similarity
        == 100
    )

    assert (
        result.contract_similarity
        == 91
    )

    assert (
        "Duration differs"
        in result.normalization_reason
    )

    assert (
        result.normalization_confidence
        == 0
    )

    assert (
        result.normalization_quality
        == "INSUFFICIENT_EVIDENCE"
    )

    print(
        "TEST 2 PASSED - "
        "TERM NORMALIZATION REQUIRED"
    )

    # =================================================
    # TEST 3
    # MILEAGE DIFFERENCE
    # =================================================

    arval = create_offer(
        "Arval",
        190000,
        48,
        30000,
    )

    ayvens = create_offer(
        "Ayvens",
        200000,
        48,
        20000,
    )

    result = engine.normalize(
        create_comparison(
            arval,
            ayvens,
        )
    )

    assert (
        result.normalization_status
        == "NEEDS_MILEAGE_NORMALIZATION"
    )

    assert (
        result.normalization_method
        == "NONE"
    )

    assert (
        result.normalized_price_available
        is False
    )

    assert (
        result.normalized_monthly_fee_a
        is None
    )

    assert (
        result.normalized_monthly_fee_b
        is None
    )

    assert (
        result.duration_difference
        == 0
    )

    assert (
        result.mileage_difference
        == 10000
    )

    assert (
        result.duration_similarity
        == 100
    )

    assert (
        result.mileage_similarity
        == 80
    )

    assert (
        result.contract_similarity
        == 92
    )

    assert (
        "Mileage differs"
        in result.normalization_reason
    )

    assert (
        result.normalization_confidence
        == 0
    )

    assert (
        result.normalization_quality
        == "INSUFFICIENT_EVIDENCE"
    )

    print(
        "TEST 3 PASSED - "
        "MILEAGE NORMALIZATION REQUIRED"
    )

    # =================================================
    # TEST 4
    # TERM + MILEAGE DIFFERENCE
    # =================================================

    arval = create_offer(
        "Arval",
        200000,
        60,
        30000,
    )

    ayvens = create_offer(
        "Ayvens",
        190000,
        48,
        20000,
    )

    result = engine.normalize(
        create_comparison(
            arval,
            ayvens,
        )
    )

    assert (
        result.normalization_status
        == "NEEDS_TERM_AND_MILEAGE_NORMALIZATION"
    )

    assert (
        result.normalization_method
        == "NONE"
    )

    assert (
        result.normalized_price_available
        is False
    )

    assert (
        result.normalized_monthly_fee_a
        is None
    )

    assert (
        result.normalized_monthly_fee_b
        is None
    )

    assert (
        result.duration_difference
        == 12
    )

    assert (
        result.mileage_difference
        == 10000
    )

    assert (
        result.duration_similarity
        == 85
    )

    assert (
        result.mileage_similarity
        == 80
    )

    assert (
        result.contract_similarity
        == 83
    )

    assert (
        "Duration differs"
        in result.normalization_reason
    )

    assert (
        "Mileage differs"
        in result.normalization_reason
    )

    assert (
        result.normalization_confidence
        == 0
    )

    assert (
        result.normalization_quality
        == "INSUFFICIENT_EVIDENCE"
    )

    print(
        "TEST 4 PASSED - "
        "TERM + MILEAGE NORMALIZATION REQUIRED"
    )

    # =================================================
    # TEST 5
    # OBSERVED TERM EVIDENCE
    #
    # Same mileage, different duration.
    # V3-compatible flat evidence.
    # =================================================

    arval = create_offer(
        "Arval",
        210000,
        48,
        20000,
    )

    ayvens = create_offer(
        "Ayvens",
        190000,
        60,
        20000,
    )

    comparison = create_comparison(
        arval,
        ayvens,
    )

    evidence = {
        "provider": "Arval",
        "source_duration": 48,
        "target_duration": 60,
        "source_mileage": 20000,
        "target_mileage": 20000,
        "source_monthly_fee": 210000,
        "target_monthly_fee": 195000,
        "sample_size": 1,
    }

    result = engine.normalize_with_evidence(
        comparison,
        evidence,
    )

    assert (
        result.normalization_status
        == "NORMALIZATION_ESTIMATED"
    )

    assert (
        result.normalization_method
        == "OBSERVED_PROVIDER_TERM_FACTOR"
    )

    assert (
        result.normalized_price_available
        is True
    )

    assert (
        result.normalized_monthly_fee_a
        == 195000
    )

    assert (
        result.normalized_monthly_fee_b
        == 190000
    )

    assert (
        result.normalization_confidence
        == 60
    )

    assert (
        result.normalization_quality
        == "EVIDENCE_SUPPORTED"
    )

    assert (
        result.term_normalization_available
        is True
    )

    assert (
        result.term_normalization_confidence
        == 60
    )

    assert (
        result.term_normalization_factor_a
        == 0.928571
    )

    assert (
        result.mileage_normalization_available
        is False
    )

    print(
        "TEST 5 PASSED - "
        "OBSERVED TERM EVIDENCE"
    )

    # =================================================
    # TEST 6
    # TERM EVIDENCE WITH WRONG MILEAGE
    #
    # V4 safety rule:
    # evidence must match the source mileage.
    # =================================================

    arval = create_offer(
        "Arval",
        210000,
        48,
        20000,
    )

    ayvens = create_offer(
        "Ayvens",
        190000,
        60,
        20000,
    )

    comparison = create_comparison(
        arval,
        ayvens,
    )

    evidence = {
        "provider": "Arval",
        "source_duration": 48,
        "target_duration": 60,
        "source_mileage": 30000,
        "target_mileage": 30000,
        "source_monthly_fee": 210000,
        "target_monthly_fee": 195000,
        "sample_size": 1,
    }

    result = engine.normalize_with_evidence(
        comparison,
        evidence,
    )

    assert (
        result.normalization_status
        == "NEEDS_TERM_NORMALIZATION"
    )

    assert (
        result.normalized_price_available
        is False
    )

    assert (
        result.normalization_confidence
        == 0
    )

    assert (
        result.normalization_quality
        == "INSUFFICIENT_EVIDENCE"
    )

    print(
        "TEST 6 PASSED - "
        "WRONG MILEAGE EVIDENCE REJECTED"
    )

    # =================================================
    # TEST 7
    # OBSERVED MILEAGE EVIDENCE
    #
    # Same duration, different mileage.
    # =================================================

    arval = create_offer(
        "Arval",
        210000,
        48,
        20000,
    )

    ayvens = create_offer(
        "Ayvens",
        230000,
        48,
        30000,
    )

    comparison = create_comparison(
        arval,
        ayvens,
    )

    evidence = {
        "provider": "Ayvens",
        "source_duration": 48,
        "target_duration": 48,
        "source_mileage": 30000,
        "target_mileage": 20000,
        "source_monthly_fee": 230000,
        "target_monthly_fee": 215000,
        "sample_size": 1,
    }

    result = engine.normalize_with_evidence(
        comparison,
        evidence,
    )

    assert (
        result.normalization_status
        == "NORMALIZATION_ESTIMATED"
    )

    assert (
        result.normalization_method
        == "OBSERVED_PROVIDER_MILEAGE_FACTOR"
    )

    assert (
        result.normalized_price_available
        is True
    )

    assert (
        result.normalized_monthly_fee_a
        == 210000
    )

    assert (
        result.normalized_monthly_fee_b
        == 215000
    )

    assert (
        result.mileage_normalization_available
        is True
    )

    assert (
        result.mileage_normalization_confidence
        == 60
    )

    assert (
        result.normalization_confidence
        == 60
    )

    assert (
        result.normalization_quality
        == "EVIDENCE_SUPPORTED"
    )

    print(
        "TEST 7 PASSED - "
        "OBSERVED MILEAGE EVIDENCE"
    )

    # =================================================
    # TEST 8
    # MILEAGE EVIDENCE WITH WRONG DURATION
    #
    # V4 safety rule:
    # mileage evidence cannot cross duration
    # without explicit duration evidence.
    # =================================================

    arval = create_offer(
        "Arval",
        210000,
        48,
        20000,
    )

    ayvens = create_offer(
        "Ayvens",
        230000,
        48,
        30000,
    )

    comparison = create_comparison(
        arval,
        ayvens,
    )

    evidence = {
        "provider": "Ayvens",
        "source_duration": 60,
        "target_duration": 60,
        "source_mileage": 30000,
        "target_mileage": 20000,
        "source_monthly_fee": 230000,
        "target_monthly_fee": 215000,
        "sample_size": 1,
    }

    result = engine.normalize_with_evidence(
        comparison,
        evidence,
    )

    assert (
        result.normalization_status
        == "NEEDS_MILEAGE_NORMALIZATION"
    )

    assert (
        result.normalized_price_available
        is False
    )

    assert (
        result.normalization_confidence
        == 0
    )

    print(
        "TEST 8 PASSED - "
        "WRONG DURATION EVIDENCE REJECTED"
    )

    # =================================================
    # TEST 9
    # TERM + MILEAGE EVIDENCE
    #
    # Both dimensions have explicit evidence.
    # =================================================

    arval = create_offer(
        "Arval",
        210000,
        48,
        20000,
    )

    ayvens = create_offer(
        "Ayvens",
        250000,
        60,
        30000,
    )

    comparison = create_comparison(
        arval,
        ayvens,
    )

    evidence = {
        "term_evidence": {
            "provider": "Arval",
            "source_duration": 48,
            "target_duration": 60,
            "source_mileage": 20000,
            "target_mileage": 20000,
            "source_monthly_fee": 210000,
            "target_monthly_fee": 195000,
            "sample_size": 5,
        },
        "mileage_evidence": {
            "provider": "Ayvens",
            "source_duration": 60,
            "target_duration": 60,
            "source_mileage": 30000,
            "target_mileage": 20000,
            "source_monthly_fee": 250000,
            "target_monthly_fee": 235000,
            "sample_size": 5,
        },
    }

    result = engine.normalize_with_evidence(
        comparison,
        evidence,
    )

    assert (
        result.term_normalization_available
        is True
    )

    assert (
        result.mileage_normalization_available
        is True
    )

    assert (
        result.term_normalization_confidence
        == 80
    )

    assert (
        result.mileage_normalization_confidence
        == 80
    )

    assert (
        result.normalization_confidence
        == 80
    )

    assert (
        result.normalization_method
        == "OBSERVED_PROVIDER_TERM_AND_MILEAGE_FACTORS"
    )

    assert (
        result.normalization_quality
        == "EVIDENCE_SUPPORTED"
    )

    assert (
        result.normalized_price_available
        is True
    )

    print(
        "TEST 9 PASSED - "
        "TERM + MILEAGE EVIDENCE"
    )

    # =================================================
    # TEST 10
    # PARTIAL NORMALIZATION
    #
    # Term differs AND mileage differs.
    # Only term evidence exists.
    #
    # V4 must NOT declare the full contract normalized.
    # =================================================

    arval = create_offer(
        "Arval",
        210000,
        48,
        20000,
    )

    ayvens = create_offer(
        "Ayvens",
        250000,
        60,
        30000,
    )

    comparison = create_comparison(
        arval,
        ayvens,
    )

    evidence = {
        "term_evidence": {
            "provider": "Arval",
            "source_duration": 48,
            "target_duration": 60,
            "source_mileage": 20000,
            "target_mileage": 20000,
            "source_monthly_fee": 210000,
            "target_monthly_fee": 195000,
            "sample_size": 1,
        },
    }

    result = engine.normalize_with_evidence(
        comparison,
        evidence,
    )

    assert (
        result.term_normalization_available
        is True
    )

    assert (
        result.mileage_normalization_available
        is False
    )

    assert (
        result.normalization_quality
        == "PARTIALLY_NORMALIZED"
    )

    assert (
        result.normalization_status
        == "PARTIALLY_NORMALIZED"
    )

    assert (
        result.normalized_price_available
        is False
    )

    assert (
        result.normalized_monthly_fee_a
        is None
    )

    assert (
        result.normalized_monthly_fee_b
        is None
    )

    assert (
        result.normalization_confidence
        == 60
    )

    print(
        "TEST 10 PASSED - "
        "PARTIAL NORMALIZATION"
    )

    # =================================================
    # FINAL
    # =================================================

    print(
        "\nALL CONTRACT NORMALIZATION V4 "
        "TESTS PASSED"
    )


if __name__ == "__main__":
    main()