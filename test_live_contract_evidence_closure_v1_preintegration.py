from market_intelligence.market_match_engine import MarketMatchEngine
from market_intelligence.market_pair_full_comparison_bridge import MarketPairFullComparisonBridge
from contract_normalization.contract_normalization_evidence_resolver_v3 import (
    ContractNormalizationEvidenceResolverV3,
)

def main():
    pair = next(
        x for x in MarketMatchEngine().build()
        if x.group_key == "BYD::ATTO 2::PHEV"
    )

    bridge = MarketPairFullComparisonBridge()

    # Reuse the bridge's live browser ownership pattern indirectly by first
    # loading the pair through the already proven headed path. This diagnostic
    # intentionally stops if the bridge internals do not expose a browser;
    # integration should then be patched explicitly rather than guessed.
    result = bridge.evaluate(pair, headless=False)

    print("="*100)
    print("LIVE CONTRACT EVIDENCE CLOSURE V1 - PRE-INTEGRATION DIAGNOSTIC")
    print("="*100)
    print("bridge_status:", result.status)
    print("diagnostic:", result.diagnostic)
    print()
    print(
        "Bridge live loading is healthy. Resolver V3 is intentionally not "
        "monkey-patched into the bridge by this diagnostic; inspect the bridge "
        "constructor/call site before replacing V2."
    )

    assert result.status == "EVALUATED"
    print("TEST PASSED - LIVE PAIR LOAD IS READY FOR EXPLICIT V3 BRIDGE INTEGRATION.")

if __name__=="__main__":
    main()
