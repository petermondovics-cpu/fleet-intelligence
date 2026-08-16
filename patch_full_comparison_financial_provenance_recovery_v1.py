from pathlib import Path
import re

PATH = Path("comparison/full_comparison_orchestrator.py")
BACKUP = Path(
    "comparison/full_comparison_orchestrator.py.pre_financial_provenance_recovery.bak"
)

HELPER = '    @staticmethod\n    def _financial_review_summary(\n        side_label,\n        financial,\n        review,\n    ):\n        down_payment = getattr(\n            financial,\n            "down_payment",\n            None,\n        )\n        status = getattr(\n            down_payment,\n            "status",\n            None,\n        )\n\n        if status == EVIDENCE_OBSERVED:\n            percent = getattr(\n                down_payment,\n                "percent",\n                None,\n            )\n            amount = getattr(\n                down_payment,\n                "amount",\n                None,\n            )\n\n            if percent is not None:\n                value = f"{percent}%"\n            elif amount is not None:\n                value = f"{amount} Ft"\n            else:\n                value = "explicit condition"\n\n            return f"{side_label}: OBSERVED ({value})"\n\n        if review is None:\n            return (\n                f"{side_label}: UNKNOWN "\n                "(no deep publication review context)"\n            )\n\n        review_status = getattr(\n            review,\n            "status",\n            "UNRESOLVED",\n        )\n        surfaces = ", ".join(\n            getattr(\n                review,\n                "reviewed_surfaces",\n                (),\n            )\n        ) or "none"\n\n        if review_status == "REVIEWED_NOT_PUBLISHED":\n            return (\n                f"{side_label}: UNKNOWN / REVIEWED_NOT_PUBLISHED "\n                f"(reviewed: {surfaces})"\n            )\n\n        if review_status == "OBSERVED":\n            return (\n                f"{side_label}: OBSERVED "\n                f"(reviewed: {surfaces})"\n            )\n\n        return (\n            f"{side_label}: UNKNOWN / REVIEW_UNRESOLVED "\n            f"(reviewed: {surfaces})"\n        )\n\n    @classmethod\n    def _down_payment_incomplete_message(\n        cls,\n        left,\n        right,\n        left_review,\n        right_review,\n    ):\n        left_text = cls._financial_review_summary(\n            "Left",\n            left,\n            left_review,\n        )\n        right_text = cls._financial_review_summary(\n            "Right",\n            right,\n            right_review,\n        )\n\n        return (\n            "Down payment is not explicitly observed for both offers. "\n            + left_text\n            + ". "\n            + right_text\n            + ". REVIEWED_NOT_PUBLISHED means publication was actively "\n            "checked; it does not mean 0% down payment. "\n            "No default 20% or zero-down assumption is allowed."\n        )\n\n'

def fail(msg):
    raise SystemExit("RECOVERY PATCH ABORTED: " + msg)

def main():
    if not PATH.exists():
        fail(f"missing {PATH}")

    text = PATH.read_text(encoding="utf-8")

    if (
        "left_financial_review=None" in text
        and "_down_payment_incomplete_message" in text
        and "right_financial_review=None" in text
    ):
        print("Financial provenance support is already installed.")
        return

    original = text

    sig_old = """        left_financial=None,
        right_financial=None,
        contract_evidence=None,
    ) -> FullComparisonResult:
"""
    sig_new = """        left_financial=None,
        right_financial=None,
        contract_evidence=None,
        left_financial_review=None,
        right_financial_review=None,
    ) -> FullComparisonResult:
"""
    if sig_old not in text:
        fail("compare() signature anchor not found")
    text = text.replace(sig_old, sig_new, 1)

    call_old = """        financial_status = (
            self._financial_status(
                financial_left,
                financial_right,
                barriers,
            )
        )
"""
    call_new = """        financial_status = (
            self._financial_status(
                financial_left,
                financial_right,
                barriers,
                left_review=left_financial_review,
                right_review=right_financial_review,
            )
        )
"""
    if call_old not in text:
        fail("_financial_status() call anchor not found")
    text = text.replace(call_old, call_new, 1)

    def_old = """    def _financial_status(
        self,
        left,
        right,
        barriers,
    ) -> str:
"""
    def_new = """    def _financial_status(
        self,
        left,
        right,
        barriers,
        left_review=None,
        right_review=None,
    ) -> str:
"""
    if def_old not in text:
        fail("_financial_status() definition anchor not found")
    text = text.replace(def_old, def_new, 1)

    old_msg = """                    message=(
                        "Down payment is not explicitly "
                        "observed for both offers. "
                        "No default 20% assumption "
                        "is allowed."
                    ),
"""
    new_msg = """                    message=(
                        self._down_payment_incomplete_message(
                            left,
                            right,
                            left_review,
                            right_review,
                        )
                    ),
"""
    if old_msg not in text:
        fail("generic down-payment blocker message not found")
    text = text.replace(old_msg, new_msg, 1)

    helper_anchor = """    @staticmethod
    def _same_down_payment(
"""
    if helper_anchor not in text:
        fail("_same_down_payment() helper anchor not found")
    text = text.replace(helper_anchor, HELPER + helper_anchor, 1)

    required = (
        "SERVICE_SEMANTIC_EQUIVALENCE_INCOMPLETE",
        "contract_evidence=None",
        "EXPLICIT_COMMON_CONTRACT_STATE",
        "left_financial_review=None",
        "right_financial_review=None",
        "left_review=left_financial_review",
        "right_review=right_financial_review",
        "_down_payment_incomplete_message",
        "REVIEWED_NOT_PUBLISHED means publication was actively",
    )
    for item in required:
        if item not in text:
            fail("post-patch safety check failed: " + item)

    compile(text, str(PATH), "exec")

    if not BACKUP.exists():
        BACKUP.write_text(original, encoding="utf-8")
        print("Backup:", BACKUP)

    PATH.write_text(text, encoding="utf-8")
    print("Patched:", PATH)
    print("Financial provenance orchestrator recovery: INSTALLED")

if __name__ == "__main__":
    main()
