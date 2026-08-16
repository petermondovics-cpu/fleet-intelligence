from scrapers.arval.scraper import ArvalScraper
from scrapers.ayvens.scraper import AyvensScraper


def run_provider(name, scraper):
    print("\n" + "=" * 80)
    print(f"{name.upper()} FULL LIVE COLLECTION")
    print("=" * 80)

    offers = scraper.collect()

    print("\n" + "-" * 80)
    print(f"{name.upper()} RESULT")
    print("-" * 80)

    print(f"Validated offers: {len(offers)}")

    for offer in offers:
        print(
            f"{offer.provider} | "
            f"{offer.model} | "
            f"{offer.duration} hó | "
            f"{offer.mileage:,} km/év | "
            f"{offer.monthly_fee:,} Ft"
        )

    return offers


def main():

    arval_offers = run_provider(
        "Arval",
        ArvalScraper(),
    )

    ayvens_offers = run_provider(
        "Ayvens",
        AyvensScraper(),
    )

    all_offers = (
        arval_offers
        + ayvens_offers
    )

    print("\n" + "=" * 80)
    print("FULL LIVE COLLECTION SUMMARY")
    print("=" * 80)

    print(
        f"Arval validated offers: "
        f"{len(arval_offers)}"
    )

    print(
        f"Ayvens validated offers: "
        f"{len(ayvens_offers)}"
    )

    print(
        f"TOTAL validated offers: "
        f"{len(all_offers)}"
    )

    assert len(arval_offers) > 0
    assert len(ayvens_offers) > 0
    assert len(all_offers) > 0

    print(
        "\nFULL LIVE COLLECTION "
        "COMPLETED"
    )


if __name__ == "__main__":
    main()
