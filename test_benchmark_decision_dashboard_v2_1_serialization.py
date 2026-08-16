from types import SimpleNamespace

from market_intelligence.benchmark_decision_dashboard_service_v2 import (
    BenchmarkDecisionDashboardServiceV2,
)

def main():
    service = BenchmarkDecisionDashboardServiceV2(repository=None)

    value = SimpleNamespace(
        id=7,
        status="COMPLETED",
    )

    result = service._serialize_record(value)

    assert result == {
        "id": 7,
        "status": "COMPLETED",
    }

    assert service._serialize_record(None) is None

    print(
        "TEST PASSED - DASHBOARD V2.1 SERIALIZES BOTH "
        "DATACLASS AND SIMPLE RECORD OBJECTS SAFELY."
    )

if __name__ == "__main__":
    main()
