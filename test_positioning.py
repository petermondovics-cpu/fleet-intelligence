from datetime import datetime

from comparison.engine import ComparisonResult
from models.offer import Offer
from positioning.engine import MarketPositioningEngine


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
    difference,
):

    if (
        offer_a.monthly_fee
        <= offer_b.monthly_fee
    ):

        winner = offer_a.provider

    else:

        winner = offer_b.provider

    price_difference = abs(
        offer_a.monthly_fee
        - offer_b.monthly_fee
    )

    highest = max(
        offer_a.monthly_fee,
        offer_b.monthly_fee,
    )

    if highest > 0:

        price_difference_percent = (
            price_difference
            / highest
            * 100
        )

    else:

        price_difference_percent = 0.0

    return ComparisonResult(

        brand="BYD",

        model="ATTO 2",

        fuel_type_a=offer_a.fuel_type,

        fuel_type_b=offer_b.fuel_type,

        vehicle_confidence=100,

        vehicle_match_type=(
            "EXACT_MATCH"
        ),

        contract_comparable=(
            comparable
        ),

        contract_difference=(
            difference
        ),

        duration_similarity=(
            100 if comparable else 85
        ),

        mileage_similarity=100,

        contract_similarity=(
            100 if comparable else 91
        ),

        offers=[
            offer_a,
            offer_b,
        ],

        best_provider=winner,

        best_monthly_fee=min(
            offer_a.monthly_fee,
            offer_b.monthly_fee,
        ),

        price_difference=(
            price_difference
        ),

        annual_saving=(
            price_difference * 12
        ),

        price_winner=(
            winner
            if comparable
            else "NOT_COMPARABLE"
        ),

        price_winner_is_valid=(
            comparable
        ),

        price_difference_percent=round(
            price_difference_percent,
            2,
        ),
    )


def main():

    # ------------------------------------------------
    # TEST 1
    # DIFFERENT CONTRACT
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
        "futamidő: 60 vs 48 hónap",
    )

    engine = (
        MarketPositioningEngine()
    )

    results = engine.build(
        [arval, ayvens],
        [comparison],
    )

    assert len(results) == 1

    result = results[0]

    assert result.lowest_provider == "Ayvens"

    assert (
        result.lowest_monthly_fee
        == 189990
    )

    assert (
        result.price_difference
        == 2322
    )

    assert (
        result.contract_comparable
        is False
    )

    assert (
        result.nominal_price_position
        == "Ayvens - LOWER_NOMINAL_PRICE"
    )

    print(
        "TEST 1 PASSED - "
        "NON-COMPARABLE MARKET POSITION"
    )

    # ------------------------------------------------
    # TEST 2
    # COMPARABLE CONTRACT
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
        "",
    )

    results = engine.build(
        [arval, ayvens],
        [comparison],
    )

    result = results[0]

    assert (
        result.contract_comparable
        is True
    )

    assert (
        result.lowest_provider
        == "Arval"
    )

    assert (
        result.nominal_price_position
        == "Arval - LOWER_PRICE"
    )

    print(
        "TEST 2 PASSED - "
        "COMPARABLE MARKET POSITION"
    )

    # ------------------------------------------------
    # TEST 3
    # SINGLE PROVIDER
    # ------------------------------------------------

    arval = create_offer(
        "Arval",
        180000,
        48,
    )

    results = engine.build(
        [arval],
        [],
    )

    assert len(results) == 0

    print(
        "TEST 3 PASSED - "
        "SINGLE PROVIDER EXCLUDED"
    )

    print(
        "\nALL POSITIONING TESTS PASSED"
    )


if __name__ == "__main__":
    main()