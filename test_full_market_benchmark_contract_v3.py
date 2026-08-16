from market_intelligence.benchmark_batch_engine import BenchmarkBatchEngine
from market_intelligence.benchmark_decision_dashboard_service_v2 import BenchmarkDecisionDashboardServiceV2

def main():
    print("=" * 100)
    print("FULL MARKET BENCHMARK - CONTRACT V3")
    print("=" * 100)

    engine = BenchmarkBatchEngine()
    try:
        result = engine.run(headless=False)
    finally:
        engine.close()

    print("run_id:", result.run_id)
    print("status:", result.status)
    print("candidate_count:", result.candidate_count)
    print("evaluated_count:", result.evaluated_count)
    print("failed_count:", result.failed_count)
    print("price_comparable_count:", result.price_comparable_count)

    data = BenchmarkDecisionDashboardServiceV2().load()

    print("\n--- DECISION REASONS ---")
    for key, value in data.decision_reason_counts.items():
        print(key, value)

    contract_count = data.decision_reason_counts.get("NO_COMMON_PRICED_CONTRACT_STATE", 0)

    print("\nNO_COMMON_PRICED_CONTRACT_STATE:", contract_count, "/", data.pair_count)
    print("\nTEST PASSED - CONTRACT V3 FULL-MARKET RUN COMPLETED.")

if __name__ == "__main__":
    main()
