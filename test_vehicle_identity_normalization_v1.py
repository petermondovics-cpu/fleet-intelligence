from models.vehicle_identity_normalizer import (
    VehicleIdentityNormalizer,
)


def check(
    normalizer,
    brand,
    model,
    trim,
    fuel,
    expected_brand,
    expected_model,
    expected_fuel,
):
    result = normalizer.normalize(
        brand,
        model,
        trim,
        fuel,
    )

    assert result.brand == expected_brand
    assert result.model == expected_model
    assert result.fuel_type == expected_fuel


def main():

    n = VehicleIdentityNormalizer()

    # TEST 1 - BYD ATTO 2
    check(
        n,
        "BYD",
        "ATTO 2",
        "1.5 PHEV BOOST AT",
        "PHEV",
        "BYD",
        "ATTO 2",
        "PHEV",
    )

    check(
        n,
        "BYD",
        "ATTO 2 DM-i",
        "Active 166 HP",
        "PHEV",
        "BYD",
        "ATTO 2",
        "PHEV",
    )

    print(
        "TEST 1 PASSED - "
        "BYD ATTO 2 / ATTO 2 DM-i NORMALIZED"
    )

    # TEST 2 - BYD SEAL U
    check(
        n,
        "BYD",
        "SEAL U",
        "PHEV DM-I COMFORT AT",
        "PHEV",
        "BYD",
        "SEAL U",
        "PHEV",
    )

    check(
        n,
        "BYD",
        "Seal U DM-i",
        "Boost 218 HP",
        "PHEV",
        "BYD",
        "SEAL U",
        "PHEV",
    )

    print(
        "TEST 2 PASSED - "
        "BYD SEAL U / SEAL U DM-i NORMALIZED"
    )

    # TEST 3 - BYD SEALION 7
    check(
        n,
        "BYD",
        "SEALION 7 82.5 KWH DESIGN AWD",
        "SEALION 7 82.5 KWH DESIGN AWD",
        "EV",
        "BYD",
        "SEALION 7",
        "EV",
    )

    check(
        n,
        "BYD",
        "SEALION 7",
        "Comfort 230 HP",
        "EV",
        "BYD",
        "SEALION 7",
        "EV",
    )

    print(
        "TEST 3 PASSED - "
        "BYD SEALION 7 NORMALIZED"
    )

    # TEST 4 - OPEL COMBO CARGO / COMBO
    check(
        n,
        "OPEL",
        "COMBO CARGO",
        "1.5 DÍZEL (75 KW/100 LE)",
        "Diesel",
        "OPEL",
        "COMBO",
        "DIESEL",
    )

    check(
        n,
        "Opel",
        "Combo",
        "Furgon alap 1.5 Dízel MT6 100 HP",
        "Diesel",
        "OPEL",
        "COMBO",
        "DIESEL",
    )

    print(
        "TEST 4 PASSED - "
        "OPEL COMBO CARGO / COMBO NORMALIZED"
    )

    # TEST 5 - VOLVO XC40
    check(
        n,
        "VOLVO",
        "XC40 B3 PLUS DARK 5D",
        "XC40 B3 PLUS DARK 5D",
        "Petrol",
        "VOLVO",
        "XC40",
        "PETROL",
    )

    check(
        n,
        "VOLVO",
        "XC40",
        "B3 Core AT 163 HP",
        "Benzin mild-hibrid",
        "VOLVO",
        "XC40",
        "MHEV",
    )

    print(
        "TEST 5 PASSED - "
        "VOLVO XC40 MODEL NORMALIZED; "
        "FUEL DIFFERENCE PRESERVED"
    )

    # TEST 6 - DO NOT COLLAPSE ATTO 2 AND ATTO 3
    a = n.normalize(
        "BYD",
        "ATTO 2 DM-i",
        "Active",
        "PHEV",
    )

    b = n.normalize(
        "BYD",
        "ATTO 3 EVO",
        "Design",
        "EV",
    )

    assert a.model != b.model

    print(
        "TEST 6 PASSED - "
        "DISTINCT MODELS REMAIN DISTINCT"
    )

    print(
        "\nALL VEHICLE IDENTITY "
        "NORMALIZATION V1 TESTS PASSED"
    )


if __name__ == "__main__":
    main()
