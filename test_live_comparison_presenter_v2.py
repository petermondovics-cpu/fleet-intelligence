from market_intelligence.market_match_engine import MarketMatchEngine
from market_intelligence.market_pair_full_comparison_bridge import MarketPairFullComparisonBridge

TARGET_GROUP = "BYD::ATTO 2::PHEV"

def main():
    print("=" * 100)
    print("LIVE COMPARISON PRESENTER V2 / UNIFIED API RESPONSE")
    print("=" * 100)

    pair = next((item for item in MarketMatchEngine().build() if item.group_key == TARGET_GROUP), None)
    assert pair is not None

    result = MarketPairFullComparisonBridge().evaluate(pair, headless=False)
    response = result.response
    decision = result.decision

    assert response is not None
    assert decision is not None

    payload = response.to_dict()

    print()
    print("--- API VERSION ---")
    print(payload["api_version"])

    print()
    print("--- UNIFIED DECISION ---")
    print(payload["decision"])

    print()
    print("--- TOP-LEVEL COMPARISON ---")
    print("status:", payload["status"])
    print("price_comparison_allowed:", payload["price_comparison_allowed"])
    print("price_winner:", payload["price_winner"])

    assert payload["api_version"] == "comparison.v2"
    assert payload["decision"]["verdict"] == decision.verdict
    assert payload["decision"]["price_comparison_allowed"] == payload["price_comparison_allowed"]
    assert payload["decision"]["price_winner"] == payload["price_winner"]
    assert payload["decision"]["observed_price_difference"]["normalized"] is False
    assert payload["decision"]["observed_price_difference"]["difference_huf"] == 2322
    assert "NO_COMMON_PRICED_CONTRACT_STATE" in payload["decision"]["decision_reasons"]
    assert "no price winner can be declared" in payload["decision"]["management_summary"]

    v1 = response.to_v1().to_dict()
    assert v1["api_version"] == "comparison.v1"
    assert "decision" not in v1

    print()
    print("TEST PASSED - COMPARISON.V2 PROVIDES ONE UNIFIED API PAYLOAD WITH DECISION, MANAGEMENT SUMMARY AND NEXT BEST ACTION, WHILE V1 CAN STILL BE PROJECTED EXPLICITLY.")

if __name__ == "__main__":
    main()
