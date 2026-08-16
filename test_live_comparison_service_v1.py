from comparison.live_comparison_service import (
    LiveComparisonService,
)


def main():
    print("=" * 88)
    print("LIVE COMPARISON SERVICE V1")
    print("=" * 88)

    run = (
        LiveComparisonService()
        .run(
            headless=False
        )
    )

    payload = (
        run.response.to_dict()
    )

    print(
        "Status:",
        payload["status"],
    )

    print(
        "Price comparison allowed:",
        payload[
            "price_comparison_allowed"
        ],
    )

    print(
        "Price winner:",
        payload["price_winner"],
    )

    print(
        "Arval advertised:",
        payload["left_offer"]
        ["price"]
        ["advertised_monthly_fee_huf"],
    )

    print(
        "Ayvens advertised:",
        payload["right_offer"]
        ["price"]
        ["advertised_monthly_fee_huf"],
    )

    print(
        "Ayvens DP:",
        payload["right_offer"]
        ["price"]
        ["down_payment"]
        ["status"],
        payload["right_offer"]
        ["price"]
        ["down_payment"]
        ["percent"],
    )

    print(
        "Ayvens pricing basis:",
        payload["right_offer"]
        ["price"]
        ["pricing_basis"],
    )

    assert (
        payload["api_version"]
        == "comparison.v1"
    )

    assert (
        payload["right_offer"]
        ["price"]
        ["down_payment"]
        ["status"]
        == "OBSERVED"
    )

    assert (
        payload["right_offer"]
        ["price"]
        ["down_payment"]
        ["percent"]
        == 0.0
    )

    assert (
        payload["right_offer"]
        ["price"]
        ["pricing_basis"]
        == "OBSERVED_ZERO_DOWN_PAYMENT_STATE"
    )

    assert (
        payload[
            "price_comparison_allowed"
        ]
        is False
    )

    assert (
        payload["price_winner"]
        is None
    )

    print(
        "\nTEST PASSED - LIVE COMPARISON SERVICE "
        "RETURNS A FRONTEND-READY COMPARISONResponseV1 "
        "WITHOUT FABRICATING A PRICE WINNER."
    )


if __name__ == "__main__":
    main()
