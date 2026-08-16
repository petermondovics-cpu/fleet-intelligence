from datetime import datetime

from comparison.engine import ComparisonResult
from models.offer import Offer
from ranking.engine import RankingEngine


def create_offer(
    provider,
    fee,
):

    return Offer(
        provider=provider,
        brand="BYD",
        model="ATTO 2",
        trim="",
        fuel_type="EV",
        monthly_fee=fee,
        duration=48,
        mileage=20000,
        url="",
        scraped_at=datetime.now(),
    )


def create_comparison(
    offer_a,
    offer_b,
):

    if (
        offer_a.monthly_fee
        <= offer_b.monthly_fee
    ):

        winner = offer_a.provider

    else:

        winner = offer_b.provider

    difference = abs(
        offer_a.monthly_fee
        - offer_b.monthly_fee
    )

    highest = max(
        offer_a.monthly_fee,
        offer_b.monthly_fee,
    )

    if highest > 0:

        difference_percent = (
            difference
            / highest
            * 100
        )

    else:

        difference_percent = 0.0

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

        contract_comparable=True,

        contract_difference="",

        duration_similarity=100,

        mileage_similarity=100,

        contract_similarity=100,

        offers=[
            offer_a,
            offer_b,
        ],

        best_provider=winner,

        best_monthly_fee=min(
            offer_a.monthly_fee,
            offer_b.monthly_fee,
        ),

        price_difference=difference,

        annual_saving=(
            difference * 12
        ),

        price_winner=winner,

        price_winner_is_valid=True,

        price_difference_percent=round(
            difference_percent,
            2,
        ),
    )


def main():

    arval_1 = create_offer(
        "Arval",
        180000,
    )

    ayvens_1 = create_offer(
        "Ayvens",
        190000,
    )

    arval_2 = create_offer(
        "Arval",
        200000,
    )

    ayvens_2 = create_offer(
        "Ayvens",
        195000,
    )

    comparisons = [

        create_comparison(
            arval_1,
            ayvens_1,
        ),

        create_comparison(
            arval_2,
            ayvens_2,
        ),
    ]

    engine = RankingEngine()

    rankings = engine.rank(
        comparisons
    )

    print(
        "=" * 60
    )

    print(
        "TEST - PROVIDER RANKING"
    )

    print(
        "=" * 60
    )

    for result in rankings:

        print(
            f"\n#{result.rank} "
            f"{result.provider}"
        )

        print(
            f"Comparable: "
            f"{result.comparable_comparisons}"
        )

        print(
            f"Wins: "
            f"{result.wins}"
        )

        print(
            f"Win rate: "
            f"{result.win_rate}%"
        )

        print(
            f"Average monthly advantage: "
            f"{result.average_monthly_advantage:,.0f} Ft"
        )

        print(
            f"Average price advantage: "
            f"{result.average_price_advantage_percent}%"
        )

        print(
            f"Annual saving: "
            f"{result.total_annual_saving:,} Ft"
        )

        print(
            f"Competitive rate: "
            f"{result.competitive_rate}%"
        )


if __name__ == "__main__":
    main()