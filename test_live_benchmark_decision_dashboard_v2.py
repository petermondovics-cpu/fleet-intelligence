from market_intelligence.benchmark_decision_dashboard_service_v2 import BenchmarkDecisionDashboardServiceV2

def main():
    print("=" * 100)
    print("LIVE BENCHMARK DECISION DASHBOARD V2")
    print("=" * 100)
    data = BenchmarkDecisionDashboardServiceV2().load()

    print("pair_count:", data.pair_count)
    print("group_count:", data.group_count)
    print("evaluated_count:", data.evaluated_count)
    print("failed_count:", data.failed_count)
    print("evaluated_rate:", data.evaluated_rate)
    print("price_comparable_count:", data.price_comparable_count)
    print("price_comparable_rate:", data.price_comparable_rate)

    print("\n--- VERDICTS ---")
    for k, v in data.verdict_counts.items():
        print(k, v)

    print("\n--- DECISION REASONS ---")
    for k, v in data.decision_reason_counts.items():
        print(k, v)

    print("\n--- OBSERVED LOWER PROVIDER ---")
    for k, v in data.observed_lower_provider_counts.items():
        print(k, v)

    print("\n--- PRICE WINNERS ---")
    for k, v in data.price_winner_counts.items():
        print(k, v)

    print("\n--- NOMINAL DIFFERENCE ---")
    print("average_huf:", data.average_nominal_difference_huf)
    print("average_percent:", data.average_nominal_difference_percent)

    print("\n--- NEXT BEST ACTIONS ---")
    for k, v in data.next_best_action_counts.items():
        print(v, "|", k)

    print("\n--- MANAGEMENT SUMMARY ---")
    print(data.management_summary)

    assert data.pair_count > 0
    assert data.evaluated_count > 0
    assert data.group_count > 0
    assert data.verdict_counts

    print("\nTEST PASSED - LATEST BENCHMARK RUN IS EXPOSED THROUGH DECISION-AWARE DASHBOARD V2.")

if __name__ == "__main__":
    main()
