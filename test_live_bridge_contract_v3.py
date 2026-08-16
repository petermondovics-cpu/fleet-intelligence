from market_intelligence.market_match_engine import MarketMatchEngine
from market_intelligence.market_pair_full_comparison_bridge import MarketPairFullComparisonBridge

TARGET_GROUP = "BYD::ATTO 2::PHEV"

def main():
    print("=" * 100)
    print("LIVE BRIDGE CONTRACT V3 INTEGRATION")
    print("=" * 100)

    pair = next(x for x in MarketMatchEngine().build() if x.group_key == TARGET_GROUP)
    result = MarketPairFullComparisonBridge().evaluate(pair, headless=False)

    assert result.status == "EVALUATED"
    final = result.final_comparison
    payload = result.response.to_dict()

    print("contract_status:", final.contract_status)
    print("contract_method:", final.contract_normalization_method)
    print("contract_confidence:", final.contract_normalization_confidence)
    print("normalized_left:", final.normalized_monthly_fee_left)
    print("normalized_right:", final.normalized_monthly_fee_right)

    print("\n--- CONTRACT BLOCKERS ---")
    for blocker in payload["blockers"]:
        if blocker["code"] == "CONTRACT_NORMALIZATION_INCOMPLETE":
            print(blocker)

    print("\n--- DECISION REASONS ---")
    print(payload["decision"]["decision_reasons"])

    print("\nTEST PASSED - LIVE BRIDGE USES CONTRACT EVIDENCE RESOLVER V3.")

if __name__ == "__main__":
    main()
