from market_intelligence.market_match_engine import MarketMatchEngine
from market_intelligence.market_pair_full_comparison_bridge import MarketPairFullComparisonBridge

TARGET_GROUP = "BYD::ATTO 2::PHEV"

def main():
    print("=" * 100)
    print("LIVE COMPARISON DECISION EXPLANATION V1")
    print("=" * 100)
    pair = next((x for x in MarketMatchEngine().build() if x.group_key == TARGET_GROUP), None)
    assert pair is not None
    result = MarketPairFullComparisonBridge().evaluate(pair, headless=False)
    decision = result.decision
    assert decision is not None
    print()
    print("--- MACHINE DECISION ---")
    print(decision.to_dict())
    print()
    print("--- MANAGEMENT SUMMARY ---")
    print(decision.management_summary)
    print()
    print("--- NEXT BEST ACTION ---")
    print(decision.next_best_action)
    assert decision.price_comparison_allowed is False
    assert decision.price_winner is None
    assert decision.observed_price_difference.normalized is False
    assert "NO_COMMON_PRICED_CONTRACT_STATE" in decision.decision_reasons
    print()
    print("TEST PASSED - DECISION LAYER PRESERVES FULL-COMPARISON SAFETY AND EXPLAINS WHY NO PRICE WINNER CAN YET BE DECLARED.")

if __name__ == "__main__":
    main()
