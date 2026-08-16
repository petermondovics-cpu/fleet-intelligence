from datetime import datetime

from market_intelligence.engine import (
    MarketIntelligenceEngine,
)

from models.offer import Offer


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


def main():

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

    engine = (
        MarketIntelligenceEngine()
    )

    result = engine.analyze(
        [
            arval,
            ayvens,
        ]
    )

    assert result.offers_count == 2

    assert result.comparison_count == 1

    assert (
        result.comparable_comparisons
        == 0
    )

    assert (
        result.non_comparable_comparisons
        == 1
    )

    assert result.benchmark_count == 1

    assert len(
        result.positioning_results
    ) == 1

    assert len(
        result.ranking_results
    ) == 0

    positioning = (
        result.positioning_results[0]
    )

    assert (
        positioning.lowest_provider
        == "Ayvens"
    )

    assert (
        positioning.price_difference
        == 2322
    )

    print(
        "TEST PASSED - "
        "MARKET INTELLIGENCE V1"
    )

    print(
        f"Offers: "
        f"{result.offers_count}"
    )

    print(
        f"Benchmarks: "
        f"{result.benchmark_count}"
    )

    print(
        f"Comparisons: "
        f"{result.comparison_count}"
    )

    print(
        f"Comparable: "
        f"{result.comparable_comparisons}"
    )

    print(
        f"Non-comparable: "
        f"{result.non_comparable_comparisons}"
    )

    print(
        f"Positioning: "
        f"{len(result.positioning_results)}"
    )

    print(
        f"Rankings: "
        f"{len(result.ranking_results)}"
    )


if __name__ == "__main__":
    main()