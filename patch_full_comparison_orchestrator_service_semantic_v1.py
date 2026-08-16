from pathlib import Path

PATH = Path("comparison/full_comparison_orchestrator.py")
BACKUP = Path("comparison/full_comparison_orchestrator.py.pre_semantic_v1.bak")

IMPORT_ANCHOR = "from models.financial_conditions import EVIDENCE_OBSERVED"
IMPORT_BLOCK = """from comparison.service_semantic_equivalence import (
    SEMANTIC_DIFFERENCE,
    SEMANTIC_INSUFFICIENT_EVIDENCE,
    SEMANTIC_MATCH,
    SEMANTIC_PARTIAL_EQUIVALENCE,
    ServiceSemanticEquivalenceAssessor,
)

"""

INIT_ANCHOR = """        self.services = (
            ServicePackageComparisonEngine()
        )
"""
INIT_BLOCK = INIT_ANCHOR + """        self.service_semantics = (
            ServiceSemanticEquivalenceAssessor()
        )
"""

START = """        # ====================================================
        # 3. SERVICES
        # ====================================================
"""
END = """        # ====================================================
        # 4. EQUIPMENT DIMENSION
        # ====================================================
"""

NEW_SERVICES = '        # ====================================================\n        # 3. SERVICES - SEMANTIC EQUIVALENCE V1\n        # ====================================================\n\n        service_left = (\n            lc.services\n            if left_service_package is None\n            else left_service_package\n        )\n        service_right = (\n            rc.services\n            if right_service_package is None\n            else right_service_package\n        )\n\n        semantic_result = self.service_semantics.assess(\n            service_left,\n            service_right,\n        )\n        service_status = semantic_result.status\n\n        if service_status == SEMANTIC_DIFFERENCE:\n            for diff in semantic_result.contradictions:\n                barriers.append(\n                    FullComparisonBarrier(\n                        code="SERVICE_SEMANTIC_MISMATCH",\n                        message=(\n                            f"Canonical service {diff.code} has an explicit "\n                            "inclusion contradiction."\n                        ),\n                        hard=True,\n                    )\n                )\n\n        elif service_status == SEMANTIC_PARTIAL_EQUIVALENCE:\n            unresolved = (\n                tuple(\n                    f"LEFT:{code}"\n                    for code in semantic_result.left_only_codes\n                )\n                + tuple(\n                    f"RIGHT:{code}"\n                    for code in semantic_result.right_only_codes\n                )\n            )\n            barriers.append(\n                FullComparisonBarrier(\n                    code="SERVICE_SEMANTIC_EQUIVALENCE_INCOMPLETE",\n                    message=(\n                        "Core service semantics match, but additional "\n                        "one-sided published semantics remain unresolved: "\n                        + ", ".join(unresolved)\n                        + "."\n                    ),\n                    hard=False,\n                )\n            )\n\n        elif service_status == SEMANTIC_INSUFFICIENT_EVIDENCE:\n            barriers.append(\n                FullComparisonBarrier(\n                    code="SERVICE_SEMANTIC_EVIDENCE_INCOMPLETE",\n                    message=semantic_result.diagnostic,\n                    hard=False,\n                )\n            )\n\n        elif service_status != SEMANTIC_MATCH:\n            raise ValueError(\n                "Unsupported semantic service status: "\n                + str(service_status)\n            )\n\n'

def main():
    if not PATH.exists():
        raise SystemExit(f"Missing: {PATH}")

    text = PATH.read_text(encoding="utf-8")

    if (
        "ServiceSemanticEquivalenceAssessor" in text
        and "SERVICE_SEMANTIC_EQUIVALENCE_INCOMPLETE" in text
    ):
        print("Already patched - no changes made.")
        return

    if IMPORT_ANCHOR not in text:
        raise SystemExit("Import anchor not found; refusing unsafe patch.")
    if INIT_ANCHOR not in text:
        raise SystemExit("Initializer anchor not found; refusing unsafe patch.")

    start = text.find(START)
    end = text.find(END)

    if start < 0 or end < 0 or end <= start:
        raise SystemExit("Service section anchors not found; refusing unsafe patch.")

    if not BACKUP.exists():
        BACKUP.write_text(text, encoding="utf-8")
        print("Backup:", BACKUP)

    text = text.replace(
        IMPORT_ANCHOR,
        IMPORT_BLOCK + IMPORT_ANCHOR,
        1,
    )
    text = text.replace(
        INIT_ANCHOR,
        INIT_BLOCK,
        1,
    )

    start = text.find(START)
    end = text.find(END)
    text = text[:start] + NEW_SERVICES + text[end:]

    compile(text, str(PATH), "exec")
    PATH.write_text(text, encoding="utf-8")

    print("Patched:", PATH)
    print("Semantic service integration: INSTALLED")

if __name__ == "__main__":
    main()
