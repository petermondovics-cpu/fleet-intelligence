from urllib.parse import urlsplit

from playwright.sync_api import (
    sync_playwright,
)

from scrapers.arval.scraper import (
    ArvalScraper,
)


def duplicate_final_segment(
    url,
):
    parts = [
        item
        for item in urlsplit(
            url
        ).path.split("/")
        if item
    ]

    return (
        len(parts) >= 2
        and parts[-1].casefold()
        == parts[-2].casefold()
    )


def main():

    print("=" * 100)
    print("LIVE ARVAL COLLECTION URL CANONICALIZATION V1")
    print("=" * 100)

    scraper = ArvalScraper()

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
        )

        try:

            page = browser.new_page()

            urls = (
                scraper
                .collect_offer_urls(
                    page
                )
            )

            print()
            print(
                "Discovered canonical URLs:",
                len(urls),
            )

            bad = []

            for url in urls:

                duplicated = (
                    duplicate_final_segment(
                        url
                    )
                )

                print(
                    "DUPLICATED"
                    if duplicated
                    else "OK",
                    "|",
                    url,
                )

                if duplicated:
                    bad.append(
                        url
                    )

            assert not bad

            assert len(
                urls
            ) > 0

            print()
            print(
                "TEST PASSED - LIVE ARVAL DETAIL "
                "DISCOVERY RETURNS NO ADJACENT "
                "DUPLICATED FINAL OFFER SLUGS."
            )

        finally:
            browser.close()


if __name__ == "__main__":
    main()
