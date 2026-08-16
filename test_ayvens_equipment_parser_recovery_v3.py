from scrapers.ayvens.equipment_parser import (
    AyvensEquipmentParser,
)


def main():
    parser = AyvensEquipmentParser()

    # ========================================================
    # TEST 1 - NOISE FILTERING
    # ========================================================

    assert parser._is_candidate_item(
        "Fűthető kormánykerék",
        parser.STANDARD_TAB,
    )

    assert not parser._is_candidate_item(
        "48 hónap",
        parser.STANDARD_TAB,
    )

    assert not parser._is_candidate_item(
        "189 990 Ft / hó",
        parser.STANDARD_TAB,
    )

    print(
        "TEST 1 PASSED - EQUIPMENT / COMMERCIAL NOISE SEPARATED"
    )

    # ========================================================
    # TEST 2 - CLEAN TEXT
    # ========================================================

    assert (
        parser._clean_text(
            "  Adaptív   tempomat \n Stop&Go  "
        )
        == "Adaptív tempomat Stop&Go"
    )

    print(
        "TEST 2 PASSED - EQUIPMENT TEXT NORMALIZED"
    )

    # ========================================================
    # TEST 3 - SAFETY CAP / BOUNDARIES ARE PRESENT
    # ========================================================

    assert parser.STANDARD_TAB == "Alapfelszereltség"
    assert parser.OPTIONAL_TAB == "Beépített extra felszereltség"

    assert (
        "Havidíjban foglalt szolgáltatások"
        in parser.SECTION_BOUNDARIES
    )

    print(
        "TEST 3 PASSED - SECTION RECOVERY BOUNDARIES DEFINED"
    )

    print(
        "\nALL AYVENS EQUIPMENT PARSER RECOVERY V3 TESTS PASSED"
    )


if __name__ == "__main__":
    main()
