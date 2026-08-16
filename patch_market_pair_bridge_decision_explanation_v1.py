from pathlib import Path

PATH = Path("market_intelligence/market_pair_full_comparison_bridge.py")
BACKUP = Path("market_intelligence/market_pair_full_comparison_bridge.py.pre_decision_explanation_v1.bak")

IMPORT_ANCHOR = """from comparison.full_comparison_orchestrator import (
    FullComparisonOrchestrator,
)
"""
IMPORT_NEW = IMPORT_ANCHOR + """from comparison.comparison_decision_explainer_v1 import (
    ComparisonDecisionExplainerV1,
)
"""
FIELD_ANCHOR = """    response: Optional[object]
    diagnostic: str = ""
"""
FIELD_NEW = """    response: Optional[object]
    decision: Optional[object] = None
    diagnostic: str = ""
"""
PRESENT_ANCHOR = """                response = (
                    ComparisonPresenterV1()
"""
DECISION_BLOCK = """                decision = (
                    ComparisonDecisionExplainerV1()
                    .explain(
                        final,
                        left,
                        right,
                    )
                )

"""
RETURN_ANCHOR = """                    response=response,
                    diagnostic=(
"""
RETURN_NEW = """                    response=response,
                    decision=decision,
                    diagnostic=(
"""

def main():
    text = PATH.read_text(encoding="utf-8")
    if "decision=decision" in text:
        print("Already patched - no changes made.")
        return
    for anchor in (IMPORT_ANCHOR, FIELD_ANCHOR, PRESENT_ANCHOR, RETURN_ANCHOR):
        if anchor not in text:
            raise SystemExit("Required bridge anchor missing; refusing unsafe patch.")
    if not BACKUP.exists():
        BACKUP.write_text(text, encoding="utf-8")
        print("Backup:", BACKUP)
    text = text.replace(IMPORT_ANCHOR, IMPORT_NEW, 1)
    text = text.replace(FIELD_ANCHOR, FIELD_NEW, 1)
    text = text.replace(PRESENT_ANCHOR, DECISION_BLOCK + PRESENT_ANCHOR, 1)
    text = text.replace(RETURN_ANCHOR, RETURN_NEW, 1)
    compile(text, str(PATH), "exec")
    PATH.write_text(text, encoding="utf-8")
    print("Patched:", PATH)
    print("Comparison Decision Explanation V1: INSTALLED")

if __name__ == "__main__":
    main()
