import sys

from playwright.sync_api import sync_playwright

from scrapers.ayvens.equipment_parser import (
    AyvensEquipmentParser,
)


DEFAULT_URL = (
    "https://autotartosberlet.ayvens.com/"
    "byd/atto-2-dm-i"
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
            locator.first.click(
                timeout=2500
            )
            page.wait_for_timeout(500)
            print("Cookie overlay handled")
            return
        except Exception:
            continue


def print_result(title, result):
    print("\n---", title, "---")
    print("Status:", result.status)
    print("Count:", result.item_count)
    print("Diagnostic:", result.diagnostic)

    for index, item in enumerate(
        result.items,
        start=1,
    ):
        print(
            f"{index:02d}. {item.name}"
        )


def main():

    url = (
        sys.argv[1]
        if len(sys.argv) > 1
        else DEFAULT_URL
    )

    print("=" * 72)
    print("AYVENS EQUIPMENT LIVE TEST V2")
    print("=" * 72)
    print("\nURL:", url)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False
        )

        page = browser.new_page()

        page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=60000,
        )

        page.wait_for_timeout(3000)

        dismiss_cookies(page)

        parser = AyvensEquipmentParser()

        standard = (
            parser.parse_standard_equipment(
                page
            )
        )

        optional = (
            parser.parse_optional_equipment(
                page
            )
        )

        print_result(
            "STANDARD EQUIPMENT",
            standard,
        )

        print_result(
            "BUILT-IN EXTRA EQUIPMENT",
            optional,
        )

        print(
            "\nIMPORTANT:"
        )
        print(
            "PARSING_UNRESOLVED means the tab exists "
            "but the parser could not safely extract items."
        )
        print(
            "It must NOT be converted to an empty "
            "equipment list."
        )

        browser.close()


if __name__ == "__main__":
    main()
