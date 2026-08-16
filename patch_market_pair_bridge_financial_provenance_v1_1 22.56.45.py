from pathlib import Path

PATH = Path(
    "market_intelligence/market_pair_full_comparison_bridge.py"
)
BACKUP = Path(
    "market_intelligence/"
    "market_pair_full_comparison_bridge.py.pre_financial_provenance_v1_1.bak"
)

OLD_IMPORT = """from comparison.financial_evidence_provenance import (
    FinancialEvidenceProvenanceResolverV1,
)
"""

NEW_IMPORT = """from comparison.financial_evidence_provenance import (
    FinancialEvidenceProvenanceResolverV1_1,
)
"""

OLD_INIT = """                    FinancialEvidenceProvenanceResolverV1(
                        browser
                    )
"""

NEW_INIT = """                    FinancialEvidenceProvenanceResolverV1_1(
                        browser
                    )
"""


def main():
    if not PATH.exists():
        raise SystemExit(
            f"Missing: {PATH}"
        )

    text = PATH.read_text(
        encoding="utf-8"
    )

    if (
        "FinancialEvidenceProvenanceResolverV1_1"
        in text
    ):
        print(
            "Already patched to V1.1 - no changes made."
        )
        return

    if OLD_IMPORT not in text:
        raise SystemExit(
            "V1 financial provenance import not found; "
            "refusing unsafe patch."
        )

    if OLD_INIT not in text:
        raise SystemExit(
            "V1 financial provenance initializer not found; "
            "refusing unsafe patch."
        )

    if not BACKUP.exists():
        BACKUP.write_text(
            text,
            encoding="utf-8",
        )
        print(
            "Backup:",
            BACKUP,
        )

    text = text.replace(
        OLD_IMPORT,
        NEW_IMPORT,
        1,
    )

    text = text.replace(
        OLD_INIT,
        NEW_INIT,
        1,
    )

    compile(
        text,
        str(PATH),
        "exec",
    )

    PATH.write_text(
        text,
        encoding="utf-8",
    )

    print(
        "Patched:",
        PATH,
    )
    print(
        "Financial provenance V1.1 bridge integration: INSTALLED"
    )


if __name__ == "__main__":
    main()
