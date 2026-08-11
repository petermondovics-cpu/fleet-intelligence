from datetime import datetime

from models.offer import Offer
from comparison.engine import ComparisonEngine


def create_offer(
    provider: str,
    brand: str,
    model: str,
    fuel_type: str,
    monthly_fee: int,
    duration: int,
    mileage: int,
) -> Offer:

    return Offer(
        provider=provider,
        brand=brand,
        model=model,
        trim="",
        fuel_type=fuel_type,
        monthly_fee=monthly_fee,
        duration=duration,
        mileage=mileage,
        url="https://example.com",
        scraped_at=datetime.now(),
    )


def print_result(
    title: str,
    result,
) -> None:

    print()
    print("=" * 60)
    print(title)
    print("=" * 60)

    print(
        f"Vehicle: "
        f"{result.brand} {result.model}"
    )

    print(
        f"Vehicle confidence: "
        f"{result.vehicle_confidence}%"
    )

    print(
        f"Vehicle match: "
        f"{result.vehicle_match_type}"
    )

    print(
        f"Contract comparable: "
        f"{result.contract_comparable}"
    )

    print(
        f"Contract similarity: "
        f"{result.contract_similarity}%"
    )

    print(
        f"Price difference: "
        f"{result.price_difference:,} Ft"
    )

    print(
        f"Annual difference: "
        f"{result.annual_saving:,} Ft"
    )

    print(
        f"Price difference: "
        f"{result.price_difference_percent:.2f}%"
    )

    print(
        f"Price winner: "
        f"{result.price_winner}"
    )

    print(
        f"Valid price winner: "
        f"{result.price_winner_is_valid}"
    )

    print(
        f"Best provider: "
        f"{result.best_provider}"
    )

    print(
        f"Best monthly fee: "
        f"{result.best_monthly_fee:,} Ft"
    )

    if result.contract_difference:

        print(
            f"Contract difference: "
            f"{result.contract_difference}"
        )


def main():

    engine = ComparisonEngine()

    # ========================================================
    # TEST 1
    # EXACT CONTRACT
    # ========================================================

    arval = create_offer(
        provider="Arval",
        brand="BYD",
        model="ATTO 2",
        fuel_type="PHEV",
        monthly_fee=180_000,
        duration=48,
        mileage=20_000,
    )

    ayvens = create_offer(
        provider="Ayvens",
        brand="BYD",
        model="ATTO 2",
        fuel_type="PHEV",
        monthly_fee=190_000,
        duration=48,
        mileage=20_000,
    )

    results = engine.compare(
        [arval, ayvens]
    )

    print_result(
        "TEST 1 - EXACT CONTRACT",
        results[0],
    )

    assert (
        results[0].contract_comparable
        is True
    )

    assert (
        results[0].price_winner
        == "Arval"
    )

    assert (
        results[0].price_winner_is_valid
        is True
    )

    assert (
        results[0].price_difference
        == 10_000
    )

    assert (
        results[0].annual_saving
        == 120_000
    )

    assert (
        results[0].price_difference_percent
        == 5.26
    )

    # ========================================================
    # TEST 2
    # DIFFERENT DURATION
    # ========================================================

    arval = create_offer(
        provider="Arval",
        brand="BYD",
        model="ATTO 2",
        fuel_type="PHEV",
        monthly_fee=180_000,
        duration=60,
        mileage=20_000,
    )

    ayvens = create_offer(
        provider="Ayvens",
        brand="BYD",
        model="ATTO 2",
        fuel_type="PHEV",
        monthly_fee=170_000,
        duration=48,
        mileage=20_000,
    )

    results = engine.compare(
        [arval, ayvens]
    )

    print_result(
        "TEST 2 - DIFFERENT DURATION",
        results[0],
    )

    assert (
        results[0].contract_comparable
        is False
    )

    assert (
        results[0].price_winner
        == "NOT_COMPARABLE"
    )

    assert (
        results[0].price_winner_is_valid
        is False
    )

    assert (
        results[0].price_difference
        == 10_000
    )

    # ========================================================
    # TEST 3
    # DIFFERENT MILEAGE
    # ========================================================

    arval = create_offer(
        provider="Arval",
        brand="BYD",
        model="ATTO 2",
        fuel_type="PHEV",
        monthly_fee=180_000,
        duration=48,
        mileage=20_000,
    )

    ayvens = create_offer(
        provider="Ayvens",
        brand="BYD",
        model="ATTO 2",
        fuel_type="PHEV",
        monthly_fee=170_000,
        duration=48,
        mileage=15_000,
    )

    results = engine.compare(
        [arval, ayvens]
    )

    print_result(
        "TEST 3 - DIFFERENT MILEAGE",
        results[0],
    )

    assert (
        results[0].contract_comparable
        is False
    )

    assert (
        results[0].price_winner
        == "NOT_COMPARABLE"
    )

    assert (
        results[0].price_winner_is_valid
        is False
    )

    assert (
        results[0].price_difference
        == 10_000
    )


if __name__ == "__main__":
    main()