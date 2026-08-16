from playwright.sync_api import sync_playwright

from scrapers.ayvens.equipment_parser import (
    AyvensEquipmentParser,
    EQUIPMENT_NOT_PUBLISHED,
    EQUIPMENT_PUBLISHED,
)


AYVENS_URL = (
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

        locator = page.locator(
            selector
        )

        if locator.count() == 0:
            continue

        try:
            locator.first.click(
                timeout=2500
            )

            page.wait_for_timeout(
                500
            )

            print(
                "Cookie overlay handled"
            )

            return

        except Exception:
            continue


def main():

    print(
        "=" * 72
    )

    print(
        "AYVENS EQUIPMENT LIVE TEST V1"
    )

    print(
        "=" * 72
    )

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
        )

        page = browser.new_page()

        print(
            f"\nOpening Ayvens: "
            f"{AYVENS_URL}"
        )

        page.goto(
            AYVENS_URL,
            wait_until="domcontentloaded",
            timeout=60000,
        )

        page.wait_for_timeout(
            3000
        )

        dismiss_cookies(
            page
        )

        parser = AyvensEquipmentParser()

        result = (
            parser.parse_standard_equipment(
                page
            )
        )

        print(
            "\nStatus:",
            result.status,
        )

        print(
            "Equipment count:",
            result.item_count,
        )

        for item in result.items:
            print(
                "OBSERVED:",
                item.name,
            )

        assert result.status in {
            EQUIPMENT_PUBLISHED,
            EQUIPMENT_NOT_PUBLISHED,
        }

        if (
            result.status
            == EQUIPMENT_NOT_PUBLISHED
        ):

            assert result.item_count == 0

            print(
                "\nTEST PASSED - "
                "AYVENS EQUIPMENT IS "
                "NOT_PUBLISHED ON THIS OFFER"
            )

        else:

            assert (
                result.item_count > 0
            )

            assert all(
                item.included is True
                and item.standard is True
                for item in result.items
            )

            print(
                "\nTEST PASSED - "
                "AYVENS EQUIPMENT "
                "PUBLISHED AND PARSED"
            )

        print(
            "\nIMPORTANT:"
        )

        print(
            "NOT_PUBLISHED never means "
            "'vehicle has no standard equipment'."
        )

        browser.close()


if __name__ == "__main__":
    main()
