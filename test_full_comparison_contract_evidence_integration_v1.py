from pathlib import Path


def main():
    print("=" * 100)
    print("FULL COMPARISON CONTRACT EVIDENCE INTEGRATION V1")
    print("=" * 100)

    orch = Path(
        "comparison/full_comparison_orchestrator.py"
    ).read_text(
        encoding="utf-8"
    )

    bridge = Path(
        "market_intelligence/market_pair_full_comparison_bridge.py"
    ).read_text(
        encoding="utf-8"
    )

    # --------------------------------------------------------
    # ORCHESTRATOR WIRING
    # --------------------------------------------------------

    assert "contract_evidence=None" in orch
    assert "EXPLICIT_COMMON_CONTRACT_STATE" in orch
    assert "contract_price_available" in orch
    assert "EVIDENCE_UNRESOLVED" in orch
    assert "EXACT_COMMON_CONTRACT_OBSERVED" in orch

    # The source intentionally splits this message across adjacent
    # Python string literals, so do NOT assert one contiguous source line.
    assert "No interpolation, extrapolation or provider term " in orch
    assert "factor was used." in orch

    # Final decision must use the explicit-evidence gate, not the
    # legacy normalization.normalized_price_available flag.
    assert "and contract_price_available" in orch

    # --------------------------------------------------------
    # BRIDGE WIRING
    # --------------------------------------------------------

    assert (
        "ContractNormalizationEvidenceResolverV2"
        in bridge
    )

    assert (
        "contract_evidence=contract_evidence"
        in bridge
    )

    assert (
        ".resolve("
        in bridge
    )

    print(
        "TEST PASSED - FINAL FULL COMPARISON IS WIRED "
        "TO EXPLICIT COMMON-CONTRACT EVIDENCE."
    )


if __name__ == "__main__":
    main()
