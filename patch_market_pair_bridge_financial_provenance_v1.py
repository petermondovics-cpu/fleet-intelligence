from pathlib import Path

PATH = Path("market_intelligence/market_pair_full_comparison_bridge.py")
BACKUP = Path(
    "market_intelligence/"
    "market_pair_full_comparison_bridge.py.pre_financial_provenance_v1.bak"
)

IMPORT_ANCHOR = """from comparison.full_comparison_orchestrator import (
    FullComparisonOrchestrator,
)
"""
IMPORT_REPLACEMENT = IMPORT_ANCHOR + """from comparison.financial_evidence_provenance import (
    FinancialEvidenceProvenanceResolverV1,
)
"""

FINAL_ANCHOR = """                final = (
                    FullComparisonOrchestrator()
                    .compare(
"""

REVIEW_BLOCK = """                financial_reviewer = (
                    FinancialEvidenceProvenanceResolverV1(
                        browser
                    )
                )

                left_financial_review = (
                    financial_reviewer.resolve(
                        pair.left_provider,
                        pair.left_url,
                        enrichment.left_financial.financial,
                    )
                )

                right_financial_review = (
                    financial_reviewer.resolve(
                        pair.right_provider,
                        pair.right_url,
                        enrichment.right_financial.financial,
                    )
                )

"""

CONTRACT_ARG = """                        contract_evidence=contract_evidence,
"""
CONTRACT_REPLACEMENT = CONTRACT_ARG + """                        left_financial_review=(
                            left_financial_review
                        ),
                        right_financial_review=(
                            right_financial_review
                        ),
"""

def main():
    if not PATH.exists():
        raise SystemExit(f"Missing: {PATH}")

    text = PATH.read_text(encoding="utf-8")

    if (
        "FinancialEvidenceProvenanceResolverV1" in text
        and "left_financial_review=" in text
    ):
        print("Already patched - no changes made.")
        return

    if IMPORT_ANCHOR not in text:
        raise SystemExit("Import anchor missing; refusing unsafe patch.")
    if FINAL_ANCHOR not in text:
        raise SystemExit("Final comparison anchor missing; refusing unsafe patch.")
    if CONTRACT_ARG not in text:
        raise SystemExit(
            "Contract evidence final argument missing. "
            "Apply contract evidence integration first."
        )

    if not BACKUP.exists():
        BACKUP.write_text(text, encoding="utf-8")
        print("Backup:", BACKUP)

    text = text.replace(IMPORT_ANCHOR, IMPORT_REPLACEMENT, 1)

    final_pos = text.find(FINAL_ANCHOR)
    text = text[:final_pos] + REVIEW_BLOCK + text[final_pos:]

    pos = text.find(CONTRACT_ARG, final_pos + len(REVIEW_BLOCK))
    if pos < 0:
        raise SystemExit("Final contract_evidence argument not found.")

    text = (
        text[:pos]
        + CONTRACT_REPLACEMENT
        + text[pos + len(CONTRACT_ARG):]
    )

    compile(text, str(PATH), "exec")
    PATH.write_text(text, encoding="utf-8")

    print("Patched:", PATH)
    print("Bridge financial provenance integration: INSTALLED")

if __name__ == "__main__":
    main()
