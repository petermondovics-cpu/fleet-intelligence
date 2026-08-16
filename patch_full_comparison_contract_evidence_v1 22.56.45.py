from pathlib import Path

PATH = Path("comparison/full_comparison_orchestrator.py")
BACKUP = Path(
    "comparison/full_comparison_orchestrator.py.pre_contract_evidence_v1.bak"
)

SIGNATURE_ANCHOR = """        left_financial=None,
        right_financial=None,
    ) -> FullComparisonResult:
"""

SIGNATURE_REPLACEMENT = """        left_financial=None,
        right_financial=None,
        contract_evidence=None,
    ) -> FullComparisonResult:
"""

CONTRACT_START = """        # ====================================================
        # 5. CONTRACT NORMALIZATION
        # ====================================================
"""

FINANCIAL_START = """        # ====================================================
        # 6. FINANCIAL CONDITIONS
        # ====================================================
"""

NEW_CONTRACT_SECTION = '        # ====================================================\n        # 5. CONTRACT NORMALIZATION - EXPLICIT EVIDENCE V1\n        # ====================================================\n\n        contract_result = (\n            self.contracts.normalize(\n                left,\n                right,\n                observed_offer_pool=(\n                    observed_offer_pool\n                    or [\n                        lc.offer,\n                        rc.offer,\n                    ]\n                ),\n                other_barriers_passed=False,\n            )\n        )\n\n        normalization = (\n            contract_result.normalization\n        )\n\n        contract_status = normalization.normalization_status\n        contract_price_available = normalization.normalized_price_available\n        contract_normalized_left = (\n            normalization.normalized_monthly_fee_a\n            if contract_price_available\n            else None\n        )\n        contract_normalized_right = (\n            normalization.normalized_monthly_fee_b\n            if contract_price_available\n            else None\n        )\n        contract_method = normalization.normalization_method\n        contract_confidence = normalization.normalization_confidence\n        contract_blocker_message = normalization.normalization_reason\n\n        if contract_evidence is not None:\n            selected = getattr(\n                contract_evidence,\n                "selected_coordinate",\n                None,\n            )\n\n            if (\n                getattr(\n                    contract_evidence,\n                    "status",\n                    None,\n                ) == "RESOLVED"\n                and selected is not None\n            ):\n                contract_status = "EXACT_COMMON_CONTRACT_OBSERVED"\n                contract_price_available = True\n                contract_normalized_left = selected.left.monthly_fee\n                contract_normalized_right = selected.right.monthly_fee\n                contract_method = "EXPLICIT_COMMON_CONTRACT_STATE"\n                contract_confidence = 100\n                contract_blocker_message = ""\n\n            else:\n                contract_status = "EVIDENCE_UNRESOLVED"\n                contract_price_available = False\n                contract_normalized_left = None\n                contract_normalized_right = None\n                contract_method = "EXPLICIT_COMMON_CONTRACT_STATE"\n                contract_confidence = 0\n\n                left_observed = tuple(\n                    getattr(\n                        contract_evidence,\n                        "left_observations",\n                        (),\n                    )\n                )\n                right_observed = tuple(\n                    getattr(\n                        contract_evidence,\n                        "right_observations",\n                        (),\n                    )\n                )\n                attempted = tuple(\n                    getattr(\n                        contract_evidence,\n                        "attempted_coordinates",\n                        (),\n                    )\n                )\n\n                left_text = ", ".join(\n                    f"{item.provider} {item.duration}m/{item.mileage}km = "\n                    f"{item.monthly_fee} Ft"\n                    for item in left_observed\n                ) or "none"\n\n                right_text = ", ".join(\n                    f"{item.provider} {item.duration}m/{item.mileage}km = "\n                    f"{item.monthly_fee} Ft"\n                    for item in right_observed\n                ) or "none"\n\n                attempted_text = ", ".join(\n                    f"{duration}m/{mileage}km"\n                    for duration, mileage in attempted\n                ) or "none"\n\n                contract_blocker_message = (\n                    "No exact priced common contract coordinate was "\n                    "observed for both providers. "\n                    f"Observed left: {left_text}. "\n                    f"Observed right: {right_text}. "\n                    f"Attempted common coordinates: {attempted_text}. "\n                    "No interpolation, extrapolation or provider term "\n                    "factor was used."\n                )\n\n        if not contract_price_available:\n            barriers.append(\n                FullComparisonBarrier(\n                    code="CONTRACT_NORMALIZATION_INCOMPLETE",\n                    message=contract_blocker_message,\n                )\n            )\n\n'

ALLOWED_OLD = """            and normalization
            .normalized_price_available
            and financial_status == "MATCH"
"""

ALLOWED_NEW = """            and contract_price_available
            and financial_status == "MATCH"
"""

NORMALIZED_OLD = """        normalized_left = (
            normalization
            .normalized_monthly_fee_a
            if normalization
            .normalized_price_available
            else None
        )

        normalized_right = (
            normalization
            .normalized_monthly_fee_b
            if normalization
            .normalized_price_available
            else None
        )
"""

NORMALIZED_NEW = """        normalized_left = (
            contract_normalized_left
            if contract_price_available
            else None
        )

        normalized_right = (
            contract_normalized_right
            if contract_price_available
            else None
        )
"""

METHOD_OLD = """            contract_normalization_method=(
                normalization
                .normalization_method
            ),
            contract_normalization_confidence=(
                normalization
                .normalization_confidence
            ),
"""

METHOD_NEW = """            contract_normalization_method=(
                contract_method
            ),
            contract_normalization_confidence=(
                contract_confidence
            ),
"""

def main():
    if not PATH.exists():
        raise SystemExit(f"Missing: {PATH}")

    text = PATH.read_text(encoding="utf-8")

    if (
        "contract_evidence=None" in text
        and "EXPLICIT_COMMON_CONTRACT_STATE" in text
    ):
        print("Already patched - no changes made.")
        return

    required = [
        SIGNATURE_ANCHOR,
        CONTRACT_START,
        FINANCIAL_START,
        ALLOWED_OLD,
        NORMALIZED_OLD,
        METHOD_OLD,
    ]

    missing = [anchor[:80] for anchor in required if anchor not in text]
    if missing:
        print("Missing anchors:")
        for item in missing:
            print("-", repr(item))
        raise SystemExit("Refusing unsafe orchestrator patch.")

    if not BACKUP.exists():
        BACKUP.write_text(text, encoding="utf-8")
        print("Backup:", BACKUP)

    text = text.replace(
        SIGNATURE_ANCHOR,
        SIGNATURE_REPLACEMENT,
        1,
    )

    start = text.find(CONTRACT_START)
    end = text.find(FINANCIAL_START)
    text = text[:start] + NEW_CONTRACT_SECTION + text[end:]

    text = text.replace(ALLOWED_OLD, ALLOWED_NEW, 1)
    text = text.replace(NORMALIZED_OLD, NORMALIZED_NEW, 1)
    text = text.replace(METHOD_OLD, METHOD_NEW, 1)

    compile(text, str(PATH), "exec")
    PATH.write_text(text, encoding="utf-8")

    print("Patched:", PATH)
    print("Contract evidence integration: INSTALLED")

if __name__ == "__main__":
    main()
