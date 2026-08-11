from datetime import datetime

from models.offer import Offer
from comparison.engine import ComparisonResult
from benchmark.engine import BenchmarkEngine


def create_offer(
    provider,
    brand,
    model,
    fuel_type,
    monthly_fee,
    duration=60,
    mileage=20000,
):

    return Offer(
        provider=provider,
        brand=brand,
        model=model,
        trim="",
        fuel_type=fuel_type,
        monthly_fee=monthly_fee,
        duration=duration,
        mileage=mileage,
        url="",
        scraped_at=datetime.now(),
    )


def main():

    arval = create_offer(
        "Arval",
        "BYD",
        "ATTO 2",
        "PHEV",
        192312,
        60,
        20000,
    )

    ayvens = create_offer(
        "Ayvens",
        "BYD",
        "ATTO 2",
        "PHEV",
        189990,
        48,
        20000,
    )

    offers = [
        arval,
        ayvens,
    ]

    comparisons = []

    engine = BenchmarkEngine()

    results = engine.build(
        offers,
        comparisons,
    )

    print("=" * 60)
    print("TEST - BENCHMARK")
    print("=" * 60)

    for result in results:

        print(
            f"Vehicle: "
            f"{result.brand} "
            f"{result.model}"
        )

        print(
            f"Providers: "
            f"{', '.join(result.providers)}"
        )

        print(
            f"Lowest monthly fee: "
            f"{result.lowest_monthly_fee:,} Ft"
        )

        print(
            f"Lowest provider: "
            f"{result.lowest_provider}"
        )

        print(
            f"Contract: "
            f"{result.lowest_duration} hó / "
            f"{result.lowest_mileage:,} km"
        )

        print(
            f"Valid price winner: "
            f"{result.valid_price_winner}"
        )


if __name__ == "__main__":
    main()