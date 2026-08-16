from pathlib import Path

PATH = Path("comparison/evidence_enrichment_bridge.py")


def main():
    text = PATH.read_text(encoding="utf-8")

    old = '''        provider = side.composite.provider
        original = side.composite.financial

        financial_candidates = tuple(
'''

    new = '''        provider = side.composite.provider

        # Backward compatibility:
        # some older unit-test Composite stubs do not define a financial
        # attribute at all. Financial enrichment is optional and must not
        # break equipment/service-only contexts.
        original = getattr(
            side.composite,
            "financial",
            None,
        )

        if original is None:
            return EnrichedFinancialEvidence(
                provider=provider,
                usable_status="NOT_AVAILABLE_IN_CONTEXT",
                financial=None,
                source_url=None,
                pricing_basis=None,
                acquisition_used=False,
                diagnostic=(
                    "This comparison context does not expose financial "
                    "conditions; financial enrichment was skipped."
                ),
            )

        financial_candidates = tuple(
'''

    if old not in text:
        raise RuntimeError(
            "Expected financial enrichment block not found."
        )

    updated = text.replace(old, new, 1)

    updated = updated.replace(
        "    financial: FinancialConditions\n",
        "    financial: Optional[FinancialConditions]\n",
        1,
    )

    compile(updated, str(PATH), "exec")

    backup = PATH.with_suffix(
        ".py.pre_financial_v3_backward_compat"
    )

    if not backup.exists():
        backup.write_text(
            text,
            encoding="utf-8",
        )

    PATH.write_text(
        updated,
        encoding="utf-8",
    )

    print("PATCHED:", PATH)
    print("BACKUP :", backup)
    print("FINANCIAL ENRICHMENT V3 BACKWARD-COMPATIBILITY PATCH APPLIED")


if __name__ == "__main__":
    main()
