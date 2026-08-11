from matching.contract_matcher import ContractMatcher
from models.offer import Offer


def create_offer(
    provider: str,
    duration: int,
    mileage: int,
    monthly_fee: int,
):

    return Offer(
        provider=provider,
        brand="BYD",
        model="ATTO 2",
        trim="PHEV",
        fuel_type="PHEV",
        monthly_fee=monthly_fee,
        duration=duration,
        mileage=mileage,
        url="https://example.com/test",
    )


def print_result(
    title: str,
    result,
):

    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

    print(
        f"Duration match:       "
        f"{result.duration_match}"
    )

    print(
        f"Mileage match:        "
        f"{result.mileage_match}"
    )

    print(
        f"Comparable:           "
        f"{result.comparable}"
    )

    print(
        f"Duration difference:  "
        f"{result.duration_difference} months"
    )

    print(
        f"Mileage difference:   "
        f"{result.mileage_difference:,} km/year"
    )

    print(
        f"Duration similarity:  "
        f"{result.duration_similarity}%"
    )

    print(
        f"Mileage similarity:   "
        f"{result.mileage_similarity}%"
    )

    print(
        f"Contract similarity:  "
        f"{result.contract_similarity}%"
    )

    print(
        f"Difference:           "
        f"{result.difference}"
    )


def main():

    matcher = ContractMatcher()

    # ------------------------------------------
    # TEST 1
    # Exact contract
    # ------------------------------------------

    result = matcher.match(
        create_offer(
            "Arval",
            60,
            20000,
            192312,
        ),
        create_offer(
            "Ayvens",
            60,
            20000,
            189990,
        ),
    )

    print_result(
        "TEST 1 - EXACT CONTRACT",
        result,
    )

    # ------------------------------------------
    # TEST 2
    # 60 vs 48 months
    # ------------------------------------------

    result = matcher.match(
        create_offer(
            "Arval",
            60,
            20000,
            192312,
        ),
        create_offer(
            "Ayvens",
            48,
            20000,
            189990,
        ),
    )

    print_result(
        "TEST 2 - DIFFERENT DURATION",
        result,
    )

    # ------------------------------------------
    # TEST 3
    # 20k vs 15k km
    # ------------------------------------------

    result = matcher.match(
        create_offer(
            "Arval",
            60,
            20000,
            192312,
        ),
        create_offer(
            "Ayvens",
            60,
            15000,
            189990,
        ),
    )

    print_result(
        "TEST 3 - DIFFERENT MILEAGE",
        result,
    )

    # ------------------------------------------
    # TEST 4
    # Both different
    # ------------------------------------------

    result = matcher.match(
        create_offer(
            "Arval",
            60,
            20000,
            192312,
        ),
        create_offer(
            "Ayvens",
            48,
            15000,
            189990,
        ),
    )

    print_result(
        "TEST 4 - BOTH DIFFERENT",
        result,
    )


if __name__ == "__main__":
    main()