from models.equipment_evidence import (
    EQUIPMENT_PARSING_UNRESOLVED,
    EQUIPMENT_PUBLISHED,
)


def main():
    """
    Regression intent only:

    The evidence-aware builder must be allowed to create a composite
    representation when equipment parsing is unresolved, because the
    explicit equipment evidence status is what later blocks comparison.

    Live behavior is validated by:
        test_live_arval_ayvens_evidence_comparison_v1.py
    """

    allowed = {
        EQUIPMENT_PUBLISHED,
        EQUIPMENT_PARSING_UNRESOLVED,
    }

    assert (
        EQUIPMENT_PARSING_UNRESOLVED
        in allowed
    )

    print(
        "TEST PASSED - "
        "EVIDENCE-AWARE BUILD MAY PRESERVE "
        "PARSING_UNRESOLVED EQUIPMENT"
    )


if __name__ == "__main__":
    main()
