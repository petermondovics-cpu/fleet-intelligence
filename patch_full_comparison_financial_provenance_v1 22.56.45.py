from pathlib import Path

PATH = Path("comparison/full_comparison_orchestrator.py")
BACKUP = Path(
    "comparison/full_comparison_orchestrator.py.pre_financial_provenance_v1.bak"
)

SIGNATURE_OLD = """        right_financial=None,
        contract_evidence=None,
    ) -> FullComparisonResult:
"""
SIGNATURE_NEW = """        right_financial=None,
        contract_evidence=None,
        left_financial_review=None,
        right_financial_review=None,
    ) -> FullComparisonResult:
"""

CALL_OLD = """        financial_status = (
            self._financial_status(
                financial_left,
                financial_right,
                barriers,
            )
        )
"""
CALL_NEW = """        financial_status = (
            self._financial_status(
                financial_left,
                financial_right,
                barriers,
                left_review=left_financial_review,
                right_review=right_financial_review,
            )
        )
"""

DEF_OLD = """    def _financial_status(
        self,
        left,
        right,
        barriers,
    ) -> str:
"""
DEF_NEW = """    def _financial_status(
        self,
        left,
        right,
        barriers,
        left_review=None,
        right_review=None,
    ) -> str:
"""

BLOCK_OLD = """                    message=(
                        "Down payment is not explicitly "
                        "observed for both offers. "
                        "No default 20% assumption "
                        "is allowed."
                    ),
"""
BLOCK_NEW = """                    message=(
                        self._down_payment_incomplete_message(
                            left,
                            right,
                            left_review,
                            right_review,
                        )
                    ),
"""

HELPER_ANCHOR = """    @staticmethod
    def _same_down_payment(
"""

HELPER = '    @staticmethod\n    def _financial_review_summary(\n        side_label,\n        financial,\n        review,\n    ):\n        down_payment = getattr(\n            financial,\n            "down_payment",\n            None,\n        )\n        status = getattr(\n            down_payment,\n            "status",\n            None,\n        )\n\n        if status == EVIDENCE_OBSERVED:\n            percent = getattr(\n                down_payment,\n                "percent",\n                None,\n            )\n            amount = getattr(\n                down_payment,\n                "amount",\n                None,\n            )\n\n            if percent is not None:\n                value = f"{percent}%"\n            elif amount is not None:\n                value = f"{amount} Ft"\n            else:\n                value = "explicit condition"\n\n            return f"{side_label}: OBSERVED ({value})"\n\n        if review is None:\n            return (\n                f"{side_label}: UNKNOWN "\n                "(no deep publication review context)"\n            )\n\n        review_status = getattr(\n            review,\n            "status",\n            "UNRESOLVED",\n        )\n        surfaces = ", ".join(\n            getattr(\n                review,\n                "reviewed_surfaces",\n                (),\n            )\n        ) or "none"\n\n        if review_status == "REVIEWED_NOT_PUBLISHED":\n            return (\n                f"{side_label}: UNKNOWN / REVIEWED_NOT_PUBLISHED "\n                f"(reviewed: {surfaces})"\n            )\n\n        if review_status == "OBSERVED":\n            return (\n                f"{side_label}: OBSERVED "\n                f"(reviewed: {surfaces})"\n            )\n\n        return (\n            f"{side_label}: UNKNOWN / REVIEW_UNRESOLVED "\n            f"(reviewed: {surfaces})"\n        )\n\n    @classmethod\n    def _down_payment_incomplete_message(\n        cls,\n        left,\n        right,\n        left_review,\n        right_review,\n    ):\n        left_text = cls._financial_review_summary(\n            "Left",\n            left,\n            left_review,\n        )\n        right_text = cls._financial_review_summary(\n            "Right",\n            right,\n            right_review,\n        )\n\n        return (\n            "Down payment is not explicitly observed for both offers. "\n            + left_text\n            + ". "\n            + right_text\n            + ". REVIEWED_NOT_PUBLISHED means publication was actively "\n            "checked; it does not mean 0% down payment. "\n            "No default 20% or zero-down assumption is allowed."\n        )\n\n'

def main():
    if not PATH.exists():
        raise SystemExit(f"Missing: {PATH}")

    text = PATH.read_text(encoding="utf-8")

    if (
        "left_financial_review=None" in text
        and "_down_payment_incomplete_message" in text
    ):
        print("Already patched - no changes made.")
        return

    required = [
        SIGNATURE_OLD,
        CALL_OLD,
        DEF_OLD,
        BLOCK_OLD,
        HELPER_ANCHOR,
    ]

    missing = [x[:80] for x in required if x not in text]
    if missing:
        print("Missing anchors:")
        for item in missing:
            print("-", repr(item))
        raise SystemExit("Refusing unsafe financial provenance patch.")

    if not BACKUP.exists():
        BACKUP.write_text(text, encoding="utf-8")
        print("Backup:", BACKUP)

    text = text.replace(SIGNATURE_OLD, SIGNATURE_NEW, 1)
    text = text.replace(CALL_OLD, CALL_NEW, 1)
    text = text.replace(DEF_OLD, DEF_NEW, 1)
    text = text.replace(BLOCK_OLD, BLOCK_NEW, 1)
    text = text.replace(HELPER_ANCHOR, HELPER + HELPER_ANCHOR, 1)

    compile(text, str(PATH), "exec")
    PATH.write_text(text, encoding="utf-8")

    print("Patched:", PATH)
    print("Financial provenance integration: INSTALLED")

if __name__ == "__main__":
    main()
