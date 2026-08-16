from pathlib import Path

PATH = Path(
    "market_intelligence/market_pair_full_comparison_bridge.py"
)
BACKUP = Path(
    "market_intelligence/"
    "market_pair_full_comparison_bridge.py.pre_contract_evidence_v1.bak"
)

IMPORT_ANCHOR = """from comparison.full_comparison_orchestrator import (
    FullComparisonOrchestrator,
)
"""

IMPORT_REPLACEMENT = IMPORT_ANCHOR + """from contract_normalization.contract_normalization_evidence_resolver_v2 import (
    ContractNormalizationEvidenceResolverV2,
)
"""

FINAL_ANCHOR = """                final = (
                    FullComparisonOrchestrator()
                    .compare(
"""

EVIDENCE_BLOCK = """                contract_evidence = (
                    ContractNormalizationEvidenceResolverV2(
                        browser
                    )
                    .resolve(
                        left.composite.offer,
                        right.composite.offer,
                    )
                )

"""

CLOSING_ANCHOR = """                        right_financial=(
                            enrichment"""

def main():
    if not PATH.exists():
        raise SystemExit(f"Missing: {PATH}")

    text = PATH.read_text(encoding="utf-8")

    if (
        "ContractNormalizationEvidenceResolverV2" in text
        and "contract_evidence=contract_evidence" in text
    ):
        print("Already patched - no changes made.")
        return

    if IMPORT_ANCHOR not in text:
        raise SystemExit("Import anchor not found; refusing unsafe patch.")
    if FINAL_ANCHOR not in text:
        raise SystemExit("Final comparison anchor not found; refusing unsafe patch.")

    if not BACKUP.exists():
        BACKUP.write_text(text, encoding="utf-8")
        print("Backup:", BACKUP)

    text = text.replace(IMPORT_ANCHOR, IMPORT_REPLACEMENT, 1)

    final_pos = text.find(FINAL_ANCHOR)
    text = text[:final_pos] + EVIDENCE_BLOCK + text[final_pos:]

    final_pos = text.find(FINAL_ANCHOR, final_pos + len(EVIDENCE_BLOCK))
    right_pos = text.find(CLOSING_ANCHOR, final_pos)

    if right_pos < 0:
        raise SystemExit(
            "Final right_financial anchor not found; refusing unsafe patch."
        )

    marker = """                        ),
                    )
                )
"""

    close_pos = text.find(marker, right_pos)
    if close_pos < 0:
        raise SystemExit(
            "Final compare closing anchor not found; refusing unsafe patch."
        )

    replacement = """                        ),
                        contract_evidence=contract_evidence,
                    )
                )
"""

    text = (
        text[:close_pos]
        + replacement
        + text[close_pos + len(marker):]
    )

    compile(text, str(PATH), "exec")
    PATH.write_text(text, encoding="utf-8")

    print("Patched:", PATH)
    print("Bridge contract evidence integration: INSTALLED")

if __name__ == "__main__":
    main()
