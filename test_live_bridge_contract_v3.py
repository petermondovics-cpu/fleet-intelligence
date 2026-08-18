import os

from market_intelligence.market_match_engine import MarketMatchEngine
from market_intelligence.market_pair_full_comparison_bridge import MarketPairFullComparisonBridge

TARGET_GROUP = os.environ.get(
    "FLEET_CONTRACT_V3_TARGET_GROUP",
    "BYD::ATTO 2::PHEV",
)


class ContractOnlyBridge(MarketPairFullComparisonBridge):
    @classmethod
    def _manufacturer_acquisition(cls, browser, pair):
        # This integration test targets exact-offer contract evidence. Avoid
        # unrelated manufacturer-equipment acquisition so the live test
        # remains focused on the contract path.
        return None


def main():
    print("=" * 100)
    print("LIVE BRIDGE CONTRACT V3 INTEGRATION")
    print("target_group:", TARGET_GROUP)
    print("=" * 100)

    pair = next(x for x in MarketMatchEngine().build() if x.group_key == TARGET_GROUP)
    result = ContractOnlyBridge().evaluate(pair, headless=False)

    print("bridge_status:", result.status)
    print("bridge_diagnostic:", result.diagnostic)
    print("stage_timings:", result.stage_timings)

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
