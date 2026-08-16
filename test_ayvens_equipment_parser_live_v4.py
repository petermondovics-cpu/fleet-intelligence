from playwright.sync_api import sync_playwright

from scrapers.ayvens.equipment_parser import (
    AyvensEquipmentParser,
    EQUIPMENT_PARSING_UNRESOLVED,
    EQUIPMENT_PUBLISHED,
)


ATTO = "https://autotartosberlet.ayvens.com/byd/atto-2-dm-i"
ASTRA = "https://autotartosberlet.ayvens.com/opel/astra"


def dismiss_cookies(page):
    for selector in (
        "#onetrust-reject-all-handler",
        "#onetrust-accept-btn-handler",
        "button:has-text('Összes elfogadása')",
        "button:has-text('Elfogadom')",
        "button:has-text('Elutasítom')",
    ):
        loc = page.locator(selector)
        if not loc.count():
            continue
        try:
            loc.first.click(timeout=2000)
            page.wait_for_timeout(300)
            return
        except Exception:
            pass


def parse_url(browser, url):
    page = browser.new_page()
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(2500)
    dismiss_cookies(page)

    parser = AyvensEquipmentParser()
    standard = parser.parse_standard_equipment(page)
    optional = parser.parse_optional_equipment(page)
    page.close()
    return standard, optional


def show(label, result):
    print(label)
    print("Status:", result.status)
    print("Count:", result.item_count)
    print("Diagnostic:", result.diagnostic)


def main():
    print("=" * 80)
    print("AYVENS EQUIPMENT PARSER LIVE V4 SEMANTIC REGRESSION")
    print("=" * 80)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        atto_std, atto_opt = parse_url(browser, ATTO)

        print("\n--- ATTO 2 DM-i ---")
        show("STANDARD", atto_std)
        show("OPTIONAL", atto_opt)

        assert atto_std.status == EQUIPMENT_PARSING_UNRESOLVED, (
            "ATTO standard panel exists but is empty/unresolved; "
            "must not become NOT_PUBLISHED."
        )
        assert atto_opt.status == EQUIPMENT_PARSING_UNRESOLVED, (
            "ATTO optional panel exists in DOM but is empty; "
            "must not become NOT_PUBLISHED."
        )

        astra_std, astra_opt = parse_url(browser, ASTRA)

        print("\n--- OPEL ASTRA ---")
        show("STANDARD", astra_std)
        show("OPTIONAL", astra_opt)

        assert astra_std.status == EQUIPMENT_PUBLISHED
        assert astra_std.item_count > 0
        assert astra_opt.status == EQUIPMENT_PUBLISHED
        assert astra_opt.item_count > 0

        browser.close()

    print(
        "\nTEST PASSED - V4 DISTINGUISHES STRUCTURAL ABSENCE FROM "
        "PRESENT-BUT-EMPTY EQUIPMENT PANELS WITHOUT BREAKING ASTRA."
    )


if __name__ == "__main__":
    main()
