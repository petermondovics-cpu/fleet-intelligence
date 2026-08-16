from core import FleetIQ

from comparison.engine import ComparisonEngine
from ranking.engine import RankingEngine

from scrapers.arval.scraper import ArvalScraper
from scrapers.ayvens.scraper import AyvensScraper


def main():

    fleet = FleetIQ()

    fleet.register(
        ArvalScraper()
    )

    fleet.register(
        AyvensScraper()
    )

    print(
        "\n================================"
    )

    print(
        "FLEETIQ MARKET RANKING V1"
    )

    print(
        "================================"
    )

    offers = fleet.collect()

    print(
        f"\nCollected offers: "
        f"{len(offers)}"
    )

    comparison_engine = (
        ComparisonEngine()
    )

    comparisons = (
        comparison_engine.compare(
            offers
        )
    )

    print(
        f"Comparison results: "
        f"{len(comparisons)}"
    )

    ranking_engine = (
        RankingEngine()
    )

    rankings = (
        ranking_engine.rank(
            comparisons
        )
    )

    print(
        f"Provider rankings: "
        f"{len(rankings)}"
    )

    for result in rankings:

        print(
            "\n" + "-" * 70
        )

        print(
            f"#{result.rank} "
            f"{result.provider}"
        )

        print(
            f"Comparable models: "
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
            f"Average winning advantage: "
            f"{result.average_monthly_advantage:,.0f} Ft"
        )

        print(
            f"Average winning advantage: "
            f"{result.average_price_advantage_percent:.2f}%"
        )

        print(
            f"Annual saving potential: "
            f"{result.total_annual_saving:,} Ft"
        )

        print(
            f"Competitive rate: "
            f"{result.competitive_rate}%"
        )

    print(
        "\n================================"
    )


if __name__ == "__main__":
    main()