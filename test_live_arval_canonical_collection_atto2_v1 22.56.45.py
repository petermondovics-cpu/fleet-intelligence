from scrapers.arval.scraper import (
    ArvalScraper,
)


TARGET = (
    "byd-atto-2-15-phev-boost-at"
)


def main():

    print("=" * 100)
    print("LIVE ARVAL CANONICAL COLLECTION - BYD ATTO 2 V1")
    print("=" * 100)

    offers = (
        ArvalScraper()
        .collect()
    )

    matching = [
        item
        for item in offers
        if TARGET
        in (
            item.url
            or ""
        ).casefold()
    ]

    print()
    print(
        "Matching ATTO 2 offers:",
        len(matching),
    )

    for item in matching:
        print(
            item.model,
            "|",
            item.duration,
            "hó |",
            item.mileage,
            "km/év |",
            item.monthly_fee,
            "Ft |",
            item.url,
        )

        assert (
            "/"
            + TARGET
            + "/"
            + TARGET
        ) not in (
            item.url
            .casefold()
        )

    assert matching

    print()
    print(
        "TEST PASSED - ARVAL LIVE COLLECTION "
        "BROWSES AND RETURNS THE BYD ATTO 2 "
        "WITH A CANONICAL URL."
    )


if __name__ == "__main__":
    main()
