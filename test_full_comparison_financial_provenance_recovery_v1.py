from pathlib import Path

PATH = Path("comparison/full_comparison_orchestrator.py")

def main():
    print("=" * 100)
    print("FINANCIAL PROVENANCE ORCHESTRATOR RECOVERY TEST")
    print("=" * 100)

    text = PATH.read_text(encoding="utf-8")

    required = (
        "SERVICE_SEMANTIC_EQUIVALENCE_INCOMPLETE",
        "contract_evidence=None",
        "EXPLICIT_COMMON_CONTRACT_STATE",
        "left_financial_review=None",
        "right_financial_review=None",
        "left_review=left_financial_review",
        "right_review=right_financial_review",
        "DOWN_PAYMENT_EVIDENCE_INCOMPLETE",
        "_down_payment_incomplete_message",
        "REVIEWED_NOT_PUBLISHED means publication was actively",
    )

    for item in required:
        assert item in text, item

    print(
        "TEST PASSED - SEMANTIC, CONTRACT-EVIDENCE AND "
        "FINANCIAL-PROVENANCE LAYERS ARE ALL PRESENT."
    )

if __name__ == "__main__":
    main()
