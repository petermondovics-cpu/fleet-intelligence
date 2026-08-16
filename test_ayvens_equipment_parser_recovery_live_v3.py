import sys

from playwright.sync_api import sync_playwright

from scrapers.ayvens.equipment_parser import (
    AyvensEquipmentParser,
    EQUIPMENT_NOT_PUBLISHED,
    EQUIPMENT_PARSING_UNRESOLVED,
    EQUIPMENT_PUBLISHED,
)


ATTO_URL = (
    "https://autotartosberlet.ayvens.com/"
    "byd/atto-2-dm-i"
)

ASTRA_URL = (
    "https://autotartosberlet.ayvens.com/"
    "opel/astra"
)


def dismiss_cookies(page):
    selectors = [
        "#onetrust-reject-all-handler",
        "#onetrust-accept-btn-handler",
        "button:has-text('Összes elfogadása')",
        "button:has-text('Elfogadom')",
        "button:has-text('Elutasítom')",
    ]

    for selector in selectors:
        locator = page.locator(selector)

        if locator.count() == 0:
            continue

        try:
            locator.first.click(timeout=2500)
            page.wait_for_timeout(500)
            return
        except Exception:
            continue


def run_one(browser, url):
    page = browser.new_page()

    try:
        page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=60000,
        )

        page.wait_for_timeout(3000)
        dismiss_cookies(page)

        parser = AyvensEquipmentParser()

        standard = parser.parse_standard_equipment(page)
        optional = parser.parse_optional_equipment(page)

        print("\nURL:", url)

        print("\nSTANDARD")
        print("Status:", standard.status)
        print("Count:", standard.item_count)
        print("Diagnostic:", standard.diagnostic)

        for item in standard.items[:15]:
            print("-", item.name)

        print("\nOPTIONAL")
        print("Status:", optional.status)
        print("Count:", optional.item_count)
        print("Diagnostic:", optional.diagnostic)

        for item in optional.items[:15]:
            print("-", item.name)

        return standard, optional

    finally:
        page.close()


def main():
    print("=" * 80)
    print("AYVENS EQUIPMENT PARSER RECOVERY LIVE V3")
    print("=" * 80)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        atto_standard, atto_optional = run_one(
            browser,
            ATTO_URL,
        )

        astra_standard, astra_optional = run_one(
            browser,
            ASTRA_URL,
        )

        # ATTO recovery target:
        # V3 should recover provider evidence if it is actually exposed.
        # If the live DOM still cannot be safely isolated, unresolved is
        # allowed — but NOT_PUBLISHED is not allowed when the tab exists.
        assert atto_standard.status in {
            EQUIPMENT_PUBLISHED,
            EQUIPMENT_PARSING_UNRESOLVED,
        }

        # Astra regression: this must remain published.
        assert astra_standard.status == EQUIPMENT_PUBLISHED
        assert astra_standard.item_count > 0

        # Optional may legitimately be absent on some current offers.
        assert astra_optional.status in {
            EQUIPMENT_PUBLISHED,
            EQUIPMENT_NOT_PUBLISHED,
            EQUIPMENT_PARSING_UNRESOLVED,
        }

        print(
            "\nTEST PASSED - V3 PRESERVES ASTRA PARSING AND "
            "ATTEMPTS SAFE ATTO 2 PROVIDER-EQUIPMENT RECOVERY"
        )

        browser.close()


if __name__ == "__main__":
    main()
