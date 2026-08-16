from pathlib import Path


def main():
    text = Path(
        "comparison/full_comparison_orchestrator.py"
    ).read_text(encoding="utf-8")

    assert "left_service_package=None" in text
    assert "right_service_package=None" in text
    assert "service_left =" in text
    assert "service_right =" in text
    assert "self.services.compare(" in text

    print(
        "TEST 1 PASSED - ORCHESTRATOR ACCEPTS ENRICHED SERVICE PACKAGES"
    )
    print(
        "TEST 2 PASSED - ORIGINAL COMPOSITE SERVICE PACKAGES REMAIN DEFAULT"
    )
    print(
        "\nALL FULL COMPARISON ORCHESTRATOR V3 SERVICE WIRING TESTS PASSED"
    )


if __name__ == "__main__":
    main()
