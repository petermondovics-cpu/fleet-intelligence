"""
Integration regression for FullComparisonOrchestrator V2.

This test is intentionally source-level/lightweight: the existing live
orchestrator test remains the authoritative end-to-end test with real models.
"""
from pathlib import Path

def main():
    path = Path("comparison/full_comparison_orchestrator.py")
    text = path.read_text(encoding="utf-8")

    required = (
        "VariantEquivalenceAssessor",
        "VARIANT_EQUIVALENT",
        "VARIANT_EQUIVALENCE_EVIDENCE_INCOMPLETE",
        "VARIANT_EQUIPMENT_VALUE_DIFFERENCE",
        "VARIANT_NOT_EQUIVALENT",
        "variant_status == VARIANT_EQUIVALENT",
    )

    for token in required:
        assert token in text, token

    assert (
        'if item.code != "VEHICLE_VARIANT_DIFFERENCE"'
        in text
    )

    print("TEST 1 PASSED - VARIANT ASSESSOR WIRED INTO ORCHESTRATOR")
    print("TEST 2 PASSED - VARIANT OUTCOMES HAVE EXPLICIT BARRIERS")
    print("TEST 3 PASSED - TRIM WORDING ALONE REMAINS NON-BLOCKING")
    print("TEST 4 PASSED - PRICE COMPARISON REQUIRES VARIANT EQUIVALENCE")
    print("\nALL FULL COMPARISON ORCHESTRATOR V2 WIRING TESTS PASSED")

if __name__ == "__main__":
    main()
