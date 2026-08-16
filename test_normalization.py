from datetime import datetime

from comparison.engine import ComparisonResult
from models.offer import Offer
from normalization.engine import NormalizationEngine


def create_offer(
    provider,
    fee,
    duration,
):

    return Offer(
        provider=provider,
        brand="BYD",
        model="ATTO 2",
        trim="",
        fuel_type="EV",
        monthly_fee=fee,
        duration=duration,
        mileage=20000,
        url="",
        scraped_at=datetime.now(),
    )


def create_comparison(
    offer_a,
    offer_b,
    comparable,
    vehicle_match_type="EXACT_MATCH",
):

    return ComparisonResult(

        brand="BYD",

        model="ATTO 2",

        fuel_type_a=offer_a.fuel_type,

        fuel_type_b=offer_b.fuel_type,

        vehicle_confidence=(
            100
            if vehicle_match_type
            == "EXACT_MATCH"
            else 80
        ),

        vehicle_match_type=(
            vehicle_match_type
        ),

        contract_comparable=(
            comparable
        ),

        contract_difference=(
            ""
            if comparable
            else "futamidő: 60 vs 48 hónap"
        ),

        duration_similarity=(
            100
            if comparable
            else 85
        ),

        mileage_similarity=100,

        contract_similarity=(
            100
            if comparable
            else 91
        ),

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
            offer_a.provider
            if comparable
            and offer_a.monthly_fee
            < offer_b.monthly_fee
            else (
                offer_b.provider
                if comparable
                else "NOT_COMPARABLE"
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
        NormalizationEngine()
    )

    # ------------------------------------------------
    # TEST 1
    # DIRECT COMPARISON
    # ------------------------------------------------

    arval = create_offer(
        "Arval",
        180000,
        48,
    )

    ayvens = create_offer(
        "Ayvens",
        190000,
        48,
    )

    comparison = create_comparison(
        arval,
        ayvens,
        True,
    )

    result = engine.normalize(
        comparison
    )

    assert (
        result.position_type
        == "DIRECT_COMPARISON"
    )

    assert (
        result.normalized_fee_a
        == 180000
    )

    assert (
        result.normalized_fee_b
        == 190000
    )

    assert (
        result.normalized_price_difference
        == 10000
    )

    assert (
        result.normalized_price_winner
        == "Arval"
    )

    assert (
        result.normalized_price_winner_is_valid
        is True
    )

    assert (
        result.normalization_status
        == "NORMALIZED"
    )

    assert (
        result.normalization_method
        == "NOMINAL_PRICE"
    )

    print(
        "TEST 1 PASSED - "
        "DIRECT COMPARISON"
    )

    # ------------------------------------------------
    # TEST 2
    # NEAR COMPARISON
    # ------------------------------------------------

    arval = create_offer(
        "Arval",
        192312,
        60,
    )

    ayvens = create_offer(
        "Ayvens",
        189990,
        48,
    )

    comparison = create_comparison(
        arval,
        ayvens,
        False,
    )

    result = engine.normalize(
        comparison
    )

    assert (
        result.position_type
        == "NEAR_COMPARISON"
    )

    assert (
        result.normalized_fee_a
        is None
    )

    assert (
        result.normalized_fee_b
        is None
    )

    assert (
        result.normalized_price_winner
        == "NOT_COMPARABLE"
    )

    assert (
        result.normalized_price_winner_is_valid
        is False
    )

    assert (
        result.normalization_status
        == "NOT_NORMALIZABLE"
    )

    assert (
        result.normalization_method
        == "NONE"
    )

    print(
        "TEST 2 PASSED - "
        "NEAR COMPARISON"
    )

    # ------------------------------------------------
    # TEST 3
    # POTENTIAL MATCH
    # ------------------------------------------------

    arval = create_offer(
        "Arval",
        229889,
        60,
    )

    ayvens = create_offer(
        "Ayvens",
        249990,
        48,
    )

    comparison = create_comparison(
        arval,
        ayvens,
        False,
        "MODEL_MATCH_POWERTRAIN_MISMATCH",
    )

    result = engine.normalize(
        comparison
    )

    assert (
        result.position_type
        == "POTENTIAL_MATCH"
    )

    assert (
        result.normalization_status
        == "NOT_NORMALIZABLE"
    )

    assert (
        result.normalized_price_winner
        == "NOT_COMPARABLE"
    )

    assert (
        result.normalized_price_winner_is_valid
        is False
    )

    print(
        "TEST 3 PASSED - "
        "POTENTIAL MATCH"
    )

    print(
        "\nALL NORMALIZATION TESTS PASSED"
    )


if __name__ == "__main__":
    main()