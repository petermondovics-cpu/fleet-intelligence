from models.offer import Offer

from quality.data_quality import (
    DataQualityChecker,
)


def create_offer(
    brand,
    model,
    trim,
    fuel_type,
):

    return Offer(
        provider="Test",
        brand=brand,
        model=model,
        trim=trim,
        fuel_type=fuel_type,
        monthly_fee=200000,
        duration=48,
        mileage=20000,
        url="https://example.com/test",
    )


def print_result(
    title,
    result,
):

    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

    print(
        f"Valid:      {result.valid}"
    )

    print(
        f"Confidence: {result.confidence}%"
    )

    if not result.issues:

        print("Issues:     none")

    else:

        for issue in result.issues:

            print(
                f"{issue.severity}: "
                f"{issue.field} - "
                f"{issue.message}"
            )


def main():

    checker = DataQualityChecker()

    # 1. Normál EV
    result = checker.check_offer(
        create_offer(
            "BYD",
            "SEALION 7",
            "82.5 KWH DESIGN AWD",
            "EV",
        )
    )

    print_result(
        "TEST 1 - NORMAL EV",
        result,
    )

    # 2. Normál PHEV
    result = checker.check_offer(
        create_offer(
            "BYD",
            "ATTO 2",
            "1.5 PHEV BOOST AT",
            "PHEV",
        )
    )

    print_result(
        "TEST 2 - NORMAL PHEV",
        result,
    )

    # 3. Gyanús ATTO 3
    result = checker.check_offer(
        create_offer(
            "BYD",
            "ATTO 3",
            "EXCELLENCE 75KWH AWD",
            "PHEV",
        )
    )

    print_result(
        "TEST 3 - POWERTRAIN CONFLICT",
        result,
    )

    # 4. Ismeretlen üzemanyag
    result = checker.check_offer(
        create_offer(
            "TEST",
            "MODEL",
            "VERSION",
            "UNKNOWN",
        )
    )

    print_result(
        "TEST 4 - UNKNOWN FUEL",
        result,
    )


if __name__ == "__main__":
    main()