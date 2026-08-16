import json
from playwright.sync_api import sync_playwright

from contract_normalization.ayvens_exact_priced_contract_resolver import (
    AyvensExactPricedContractResolver,
)


AYVENS_URL = (
    "https://autotartosberlet.ayvens.com/"
    "byd/atto-2-dm-i"
)


def main():
    print("=" * 100)
    print("AYVENS EXACT-OFFER CONTRACT API RECORD DIAGNOSTIC V1")
    print("=" * 100)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False
        )

        try:
            resolver = (
                AyvensExactPricedContractResolver(
                    browser
                )
            )

            api_url = (
                resolver._api_url_from_offer(
                    AYVENS_URL
                )
            )

            page = browser.new_page()

            try:
                response = page.request.get(
                    api_url,
                    timeout=60000,
                )

                print(
                    "HTTP:",
                    response.status,
                )

                if not response.ok:
                    return

                data = response.json()

            finally:
                page.close()

            print()
            print(
                "API:",
                api_url,
            )

            print()
            print("--- EXPLICIT COORDINATE RECORDS ---")

            count = 0

            for path, record in resolver._walk_dicts(
                data
            ):
                parsed = (
                    resolver._explicit_coordinate(
                        record
                    )
                )

                if parsed is None:
                    continue

                count += 1

                print()
                print(
                    "RECORD",
                    count,
                    "|",
                    path,
                )

                print(
                    "PARSED:",
                    parsed,
                )

                print(
                    json.dumps(
                        record,
                        ensure_ascii=False,
                        indent=2,
                    )[:5000]
                )

            print()
            print(
                "Explicit priced coordinate record count:",
                count,
            )

            print()
            print(
                "DIAGNOSTIC COMPLETE - CONFIGURATION "
                "AVAILABILITY WITHOUT EXPLICIT PRICE WAS IGNORED."
            )

        finally:
            browser.close()


if __name__ == "__main__":
    main()
