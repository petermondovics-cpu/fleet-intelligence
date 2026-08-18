from market_intelligence.market_pair_full_comparison_bridge import (
    MarketPairFullComparisonBridge,
)


def main():
    timings = []

    result = MarketPairFullComparisonBridge._measure(
        timings,
        "successful_stage",
        lambda: "RESULT",
    )

    assert result == "RESULT"
    assert len(timings) == 1
    assert timings[0][0] == "successful_stage"
    assert timings[0][1] >= 0

    print(
        "TEST 1 PASSED - SUCCESSFUL STAGE TIMING IS RECORDED"
    )

    try:
        MarketPairFullComparisonBridge._measure(
            timings,
            "failed_stage",
            lambda: (_ for _ in ()).throw(
                TimeoutError("stage timeout")
            ),
        )
    except TimeoutError as exc:
        assert str(exc) == "stage timeout"
    else:
        raise AssertionError(
            "Stage timing must not swallow the original exception."
        )

    assert len(timings) == 2
    assert timings[1][0] == "failed_stage"
    assert timings[1][1] >= 0

    print(
        "TEST 2 PASSED - FAILED STAGE TIMING PRESERVES EXCEPTION"
    )

    print(
        "\nALL MARKET PAIR BRIDGE STAGE TIMING V1 TESTS PASSED"
    )


if __name__ == "__main__":
    main()
