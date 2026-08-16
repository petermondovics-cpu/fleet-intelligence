from types import SimpleNamespace

from market_intelligence.benchmark_decision_dashboard_service_v2 import (
    BenchmarkDecisionDashboardServiceV2,
)

def main():
    service = BenchmarkDecisionDashboardServiceV2(repository=None)

    row = SimpleNamespace(
        id=1,
        pair_key="p1",
        group_key="G1",
    )

    result = service._serialize_record(row)

    assert result == {
        "id": 1,
        "pair_key": "p1",
        "group_key": "G1",
    }

    print(
        "TEST PASSED - DASHBOARD V2.2 SERIALIZES SIMPLE RESULT ROWS SAFELY."
    )

if __name__ == "__main__":
    main()
