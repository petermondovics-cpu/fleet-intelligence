from matching.vehicle_matcher import VehicleMatcher


def print_result(
    title: str,
    result,
):

    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

    print(
        f"Brand match:      "
        f"{result.brand_match}"
    )

    print(
        f"Model match:      "
        f"{result.model_match}"
    )

    print(
        f"Powertrain match: "
        f"{result.powertrain_match}"
    )

    print(
        f"Confidence:       "
        f"{result.confidence}%"
    )

    print(
        f"Match type:       "
        f"{result.match_type}"
    )


def main():

    matcher = VehicleMatcher()

    # 1. Pontosan ugyanaz
    result = matcher.match(
        "BYD",
        "ATTO 2",
        "PHEV",
        "BYD",
        "ATTO 2",
        "PHEV",
    )

    print_result(
        "TEST 1 - EXACT MATCH",
        result,
    )

    # 2. Combo Cargo vs Combo
    result = matcher.match(
        "OPEL",
        "COMBO CARGO",
        "Diesel",
        "OPEL",
        "COMBO",
        "Diesel",
    )

    print_result(
        "TEST 2 - MODEL ALIAS",
        result,
    )

    # 3. Ugyanaz az autó, más hajtáslánc
    result = matcher.match(
        "BYD",
        "ATTO 3",
        "PHEV",
        "BYD",
        "ATTO 3",
        "EV",
    )

    print_result(
        "TEST 3 - POWERTRAIN MISMATCH",
        result,
    )

    # 4. ŠKODA alias
    result = matcher.match(
        "ŠKODA",
        "SUPERB COMBI",
        "Diesel",
        "SKODA",
        "SUPERB COMBI",
        "Diesel",
    )

    print_result(
        "TEST 4 - BRAND ALIAS",
        result,
    )

    # 5. Teljesen különböző autók
    result = matcher.match(
        "BMW",
        "IX1",
        "EV",
        "VOLVO",
        "XC40",
        "EV",
    )

    print_result(
        "TEST 5 - NO MATCH",
        result,
    )


if __name__ == "__main__":
    main()