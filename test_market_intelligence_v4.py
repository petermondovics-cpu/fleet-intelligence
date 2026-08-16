from datetime import datetime

from market_intelligence.engine import (
    MarketIntelligenceEngine,
)
from comparison.engine import ComparisonResult
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

    difference = ""

    if offer_a.duration != offer_b.duration:
        difference += (
            f"Duration differs: "
            f"{offer_a.duration} vs "
            f"{offer_b.duration} months."
        )

    if offer_a.mileage != offer_b.mileage:
        if difference:
            difference += " "
        difference += (
            f"Mileage differs: "
            f"{offer_a.mileage:,} vs "
            f"{offer_b.mileage:,} km/year."
        )

    price_difference = abs(
        offer_a.monthly_fee
        - offer_b.monthly_fee
    )

    annual_saving = (
        price_difference * 12
    )

    if comparable:
        if (
            offer_a.monthly_fee
            < offer_b.monthly_fee
        ):
            price_winner = offer_a.provider
        elif (
            offer_b.monthly_fee
            < offer_a.monthly_fee
        ):
            price_winner = offer_b.provider
        else:
            price_winner = "TIE"

        price_winner_is_valid = True

    else:
        price_winner = "NOT_COMPARABLE"
        price_winner_is_valid = False

    highest_price = max(
        offer_a.monthly_fee,
        offer_b.monthly_fee,
    )

    if highest_price:
        price_difference_percent = round(
            price_difference
            / highest_price
            * 100,
            2,
        )
    else:
        price_difference_percent = 0.0

    return ComparisonResult(
        brand="BYD",
        model="ATTO 2",
        fuel_type_a=offer_a.fuel_type,
        fuel_type_b=offer_b.fuel_type,
        vehicle_confidence=100,
        vehicle_match_type="EXACT_MATCH",
        contract_comparable=comparable,
        contract_difference=difference,
        duration_similarity=(
            100
            if offer_a.duration == offer_b.duration
            else 85
        ),
        mileage_similarity=(
            100
            if offer_a.mileage == offer_b.mileage
            else 80
        ),
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
        price_difference=price_difference,
        annual_saving=annual_saving,
        price_winner=price_winner,
        price_winner_is_valid=(
            price_winner_is_valid
        ),
        price_difference_percent=(
            price_difference_percent
        ),
        variant_confidence=100,
        variant_match_type="EXACT_VARIANT",
        variant_key_a="BYD|ATTO 2|EV",
        variant_key_b="BYD|ATTO 2|EV",
    )


def main():

    engine = MarketIntelligenceEngine()

    # ------------------------------------------------
    # TEST DATA
    #
    # 4 offers:
    #
    # 1. Arval   - 48 / 20k
    # 2. Ayvens  - 48 / 20k
    # 3. Arval   - 60 / 30k
    # 4. Ayvens  - 60 / 30k
    #
    # The controlled comparisons below cover:
    #
    # 1 identical contract
    # 1 term difference
    # 1 mileage difference
    # 1 term + mileage difference
    #
    # This deliberately tests the MarketIntelligence
    # orchestration independently from scraper behaviour.
    # ------------------------------------------------

    arval_48_20 = create_offer(
        "Arval",
        180000,
        48,
        20000,
    )

    ayvens_48_20 = create_offer(
        "Ayvens",
        190000,
        48,
        20000,
    )

    arval_60_20 = create_offer(
        "Arval",
        192000,
        60,
        20000,
    )

    ayvens_48_30 = create_offer(
        "Ayvens",
        205000,
        48,
        30000,
    )

    comparisons = [
        # ------------------------------------------------
        # 1. IDENTICAL CONTRACT
        # ------------------------------------------------
        create_comparison(
            arval_48_20,
            ayvens_48_20,
        ),

        # ------------------------------------------------
        # 2. TERM DIFFERENCE
        # ------------------------------------------------
        create_comparison(
            arval_60_20,
            ayvens_48_20,
        ),

        # ------------------------------------------------
        # 3. MILEAGE DIFFERENCE
        # ------------------------------------------------
        create_comparison(
            arval_48_20,
            ayvens_48_30,
        ),

        # ------------------------------------------------
        # 4. TERM + MILEAGE DIFFERENCE
        # ------------------------------------------------
        create_comparison(
            arval_60_20,
            ayvens_48_30,
        ),
    ]

    offers = [
        arval_48_20,
        ayvens_48_20,
        arval_60_20,
        ayvens_48_30,
    ]

    # ------------------------------------------------
    # CONTROLLED SUBSYSTEMS
    #
    # We replace only the upstream comparison and the
    # presentation layers. The real
    # ContractNormalizationEngine remains active.
    #
    # This isolates the MarketIntelligenceEngine
    # orchestration.
    # ------------------------------------------------

    engine.comparison_engine.compare = (
        lambda received_offers: comparisons
    )

    engine.benchmark_engine.build = (
        lambda received_offers, received_comparisons:
        ["BENCHMARK_1"]
    )

    engine.positioning_engine.build = (
        lambda received_offers, received_comparisons:
        ["POSITION_1"]
    )

    engine.ranking_engine.rank = (
        lambda received_comparisons:
        ["RANKING_1"]
    )

    # ------------------------------------------------
    # RUN
    # ------------------------------------------------

    result = engine.analyze(
        offers
    )

    # =================================================
    # TEST 1
    # BASIC MARKET COUNTS
    # =================================================

    assert (
        result.offers_count
        == 4
    )

    assert (
        result.comparison_count
        == 4
    )

    assert (
        result.comparable_comparisons
        == 1
    )

    assert (
        result.non_comparable_comparisons
        == 3
    )

    print(
        "TEST 1 PASSED - "
        "MARKET COUNTS"
    )

    # =================================================
    # TEST 2
    # BENCHMARK INTEGRATION
    # =================================================

    assert (
        result.benchmark_count
        == 1
    )

    assert (
        result.benchmark_results
        == ["BENCHMARK_1"]
    )

    print(
        "TEST 2 PASSED - "
        "BENCHMARK INTEGRATION"
    )

    # =================================================
    # TEST 3
    # MARKET POSITIONING INTEGRATION
    # =================================================

    assert (
        len(
            result.positioning_results
        )
        == 1
    )

    assert (
        result.positioning_results
        == ["POSITION_1"]
    )

    print(
        "TEST 3 PASSED - "
        "MARKET POSITIONING INTEGRATION"
    )

    # =================================================
    # TEST 4
    # PROVIDER RANKING INTEGRATION
    # =================================================

    assert (
        result.ranking_results
        == ["RANKING_1"]
    )

    print(
        "TEST 4 PASSED - "
        "PROVIDER RANKING INTEGRATION"
    )

    # =================================================
    # TEST 5
    # NORMALIZATION RESULT COUNT
    # =================================================

    assert (
        len(
            result.normalization_results
        )
        == 4
    )

    print(
        "TEST 5 PASSED - "
        "NORMALIZATION RESULTS"
    )

    # =================================================
    # TEST 6
    # NORMALIZATION STATUS DISTRIBUTION
    # =================================================

    statuses = [
        item.normalization_status
        for item in result.normalization_results
    ]

    assert (
        statuses.count(
            "NORMALIZED"
        )
        == 1
    )

    assert (
        statuses.count(
            "NEEDS_TERM_NORMALIZATION"
        )
        == 1
    )

    assert (
        statuses.count(
            "NEEDS_MILEAGE_NORMALIZATION"
        )
        == 1
    )

    assert (
        statuses.count(
            "NEEDS_TERM_AND_MILEAGE_NORMALIZATION"
        )
        == 1
    )

    print(
        "TEST 6 PASSED - "
        "NORMALIZATION STATUS DISTRIBUTION"
    )

    # =================================================
    # TEST 7
    # V3/V4 NORMALIZATION METRICS
    # =================================================

    assert (
        result.normalized_comparisons
        == 1
    )

    assert (
        result.estimated_normalizations
        == 0
    )

    assert (
        result.term_normalizations_required
        == 1
    )

    assert (
        result.mileage_normalizations_required
        == 1
    )

    assert (
        result.term_and_mileage_normalizations_required
        == 1
    )

    assert (
        result.unsupported_normalizations
        == 0
    )

    print(
        "TEST 7 PASSED - "
        "NORMALIZATION METRICS"
    )

    # =================================================
    # TEST 8
    # IDENTICAL CONTRACT DATA
    # =================================================

    identical = (
        result.normalization_results[0]
    )

    assert (
        identical.normalization_status
        == "NORMALIZED"
    )

    assert (
        identical.normalized_price_available
        is True
    )

    assert (
        identical.normalized_monthly_fee_a
        == 180000
    )

    assert (
        identical.normalized_monthly_fee_b
        == 190000
    )

    print(
        "TEST 8 PASSED - "
        "IDENTICAL CONTRACT DATA"
    )

    # =================================================
    # TEST 9
    # TERM DIFFERENCE DATA
    # =================================================

    term_result = (
        result.normalization_results[1]
    )

    assert (
        term_result.normalization_status
        == "NEEDS_TERM_NORMALIZATION"
    )

    assert (
        term_result.duration_difference
        == 12
    )

    assert (
        term_result.mileage_difference
        == 0
    )

    assert (
        term_result.normalized_price_available
        is False
    )

    print(
        "TEST 9 PASSED - "
        "TERM DIFFERENCE DATA"
    )

    # =================================================
    # TEST 10
    # MILEAGE DIFFERENCE DATA
    # =================================================

    mileage_result = (
        result.normalization_results[2]
    )

    assert (
        mileage_result.normalization_status
        == "NEEDS_MILEAGE_NORMALIZATION"
    )

    assert (
        mileage_result.duration_difference
        == 0
    )

    assert (
        mileage_result.mileage_difference
        == 10000
    )

    assert (
        mileage_result.normalized_price_available
        is False
    )

    print(
        "TEST 10 PASSED - "
        "MILEAGE DIFFERENCE DATA"
    )

    # =================================================
    # TEST 11
    # TERM + MILEAGE DATA
    # =================================================

    combined_result = (
        result.normalization_results[3]
    )

    assert (
        combined_result.normalization_status
        == "NEEDS_TERM_AND_MILEAGE_NORMALIZATION"
    )

    assert (
        combined_result.duration_difference
        == 12
    )

    assert (
        combined_result.mileage_difference
        == 10000
    )

    assert (
        combined_result.normalized_price_available
        is False
    )

    print(
        "TEST 11 PASSED - "
        "TERM + MILEAGE DATA"
    )

    # =================================================
    # TEST 12
    # RESULT OBJECT COMPLETENESS
    # =================================================

    assert hasattr(
        result,
        "normalization_results",
    )

    assert hasattr(
        result,
        "normalized_comparisons",
    )

    assert hasattr(
        result,
        "estimated_normalizations",
    )

    assert hasattr(
        result,
        "term_normalizations_required",
    )

    assert hasattr(
        result,
        "mileage_normalizations_required",
    )

    assert hasattr(
        result,
        "term_and_mileage_normalizations_required",
    )

    assert hasattr(
        result,
        "unsupported_normalizations",
    )

    print(
        "TEST 12 PASSED - "
        "RESULT OBJECT COMPLETENESS"
    )

    # =================================================
    # FINAL
    # =================================================

    print(
        "\nALL MARKET INTELLIGENCE V4 "
        "INTEGRATION TESTS PASSED"
    )


if __name__ == "__main__":
    main()
