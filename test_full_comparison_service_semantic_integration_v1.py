from pathlib import Path

PATH = Path("comparison/full_comparison_orchestrator.py")

def main():
    print("=" * 100)
    print("FULL COMPARISON ORCHESTRATOR - SERVICE SEMANTIC INTEGRATION V1")
    print("=" * 100)

    text = PATH.read_text(encoding="utf-8")

    assert "ServiceSemanticEquivalenceAssessor" in text
    assert "self.service_semantics" in text
    assert "SERVICE_SEMANTIC_EQUIVALENCE_INCOMPLETE" in text
    assert "SERVICE_SEMANTIC_EVIDENCE_INCOMPLETE" in text
    assert "SERVICE_SEMANTIC_MISMATCH" in text

    assert 'code="SERVICE_LEFT_ONLY_PUBLISHED"' not in text
    assert 'code="SERVICE_RIGHT_ONLY_PUBLISHED"' not in text
    assert 'code="SERVICE_EVIDENCE_INCOMPLETE"' not in text

    print(
        "TEST PASSED - ORCHESTRATOR USES SEMANTIC SERVICE POLICY "
        "AND OLD NOISY SERVICE BLOCKERS ARE REMOVED."
    )

if __name__ == "__main__":
    main()
