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
        offer_a.duration
        == offer_b.duration
        and
        offer_a.mileage
        == offer_b.mileage
    )

    return ComparisonResult(

        brand="BYD",

        model="ATTO 2",

        fuel_type_a=(
            offer_a.fuel_type
        ),

        fuel_type_b=(
            offer_b.fuel_type
        ),

        vehicle_confidence=100,

        vehicle_match_type=(
            "EXACT_MATCH"
        ),

        contract_comparable=(
            comparable
        ),

        contract_difference="",

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

        price_difference_percent=(
            0.0
        ),
    )


def main():

    engine = (
        ContractNormalizationEngine()
    )

    # ------------------------------------------------
    # TEST 1
    # IDENTICAL CONTRACT
    # ------------------------------------------------

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

    comparison = create_comparison(
        arval,
        ayvens,
    )

    result = engine.normalize(
        comparison
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

    print(
        "TEST 1 PASSED - "
        "IDENTICAL CONTRACT"
    )

    # ------------------------------------------------
    # TEST 2
    # TERM DIFFERENCE
    # ------------------------------------------------

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

    comparison = create_comparison(
        arval,
        ayvens,
    )

    result = engine.normalize(
        comparison
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
        "duration differs"
        in result.normalization_reason.lower()
    )

    print(
        "TEST 2 PASSED - "
        "TERM NORMALIZATION REQUIRED"
    )

    # ------------------------------------------------
    # TEST 3
    # MILEAGE DIFFERENCE
    # ------------------------------------------------

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

    comparison = create_comparison(
        arval,
        ayvens,
    )

    result = engine.normalize(
        comparison
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
        "mileage differs"
        in result.normalization_reason.lower()
    )

    print(
        "TEST 3 PASSED - "
        "MILEAGE NORMALIZATION REQUIRED"
    )

    # ------------------------------------------------
    # TEST 4
    # TERM + MILEAGE DIFFERENCE
    # ------------------------------------------------

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

    comparison = create_comparison(
        arval,
        ayvens,
    )

    result = engine.normalize(
        comparison
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
        "duration differs"
        in result.normalization_reason.lower()
    )

    assert (
        "mileage differs"
        in result.normalization_reason.lower()
    )

    print(
        "TEST 4 PASSED - "
        "TERM + MILEAGE NORMALIZATION REQUIRED"
    )

    # ------------------------------------------------
    # FINAL
    # ------------------------------------------------

    print(
        "\nALL CONTRACT NORMALIZATION V2 "
        "TESTS PASSED"
    )


if __name__ == "__main__":
    main()