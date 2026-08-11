from core import FleetIQ

from comparison.engine import ComparisonEngine
from benchmark.engine import BenchmarkEngine

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
        "FLEETIQ MARKET BENCHMARK V1"
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

    benchmark_engine = (
        BenchmarkEngine()
    )

    benchmarks = (
        benchmark_engine.build(
            offers,
            comparisons,
        )
    )

    print(
        f"Benchmark results: "
        f"{len(benchmarks)}"
    )

    for result in benchmarks:

        print(
            "\n" + "-" * 70
        )

        print(
            f"🚗 "
            f"{result.brand} "
            f"{result.model}"
        )

        print(
            f"Fuel types: "
            f"{', '.join(result.fuel_types)}"
        )

        print(
            f"Providers: "
            f"{', '.join(result.providers)}"
        )

        print(
            f"Lowest monthly: "
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
            f"Vehicle match: "
            f"{result.vehicle_confidence}% "
            f"({result.vehicle_match_type})"
        )

        if result.comparison_available:

            print(
                "Comparison: "
                "AVAILABLE"
            )

            if result.contract_comparable:

                print(
                    "Contract: "
                    "COMPARABLE"
                )

            else:

                print(
                    "Contract: "
                    "NOT_COMPARABLE"
                )

                if result.contract_difference:

                    print(
                        f"Reason: "
                        f"{result.contract_difference}"
                    )

        else:

            print(
                "Comparison: "
                "NOT_AVAILABLE"
            )

            print(
                "Contract: "
                "N/A"
            )

        print(
            f"Price winner: "
            f"{result.valid_price_winner}"
        )

        if result.data_quality_warning:

            print(
                "⚠️ Data quality: WARNING"
            )

    print(
        "\n================================"
    )


if __name__ == "__main__":
    main()