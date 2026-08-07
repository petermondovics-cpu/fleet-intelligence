from scrapers.arval.offers import get_offer_links

from playwright.sync_api import sync_playwright

from scrapers.arval.cookies import accept_cookies

ARVAL_URL = "https://www.arval.hu/kis-es-kozepvallalkozasok/ajanlat-hosszu-tavu-igenyekre"


def open_arval():
    print("🌐 Opening Arval...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        page = browser.new_page()

        page.goto(ARVAL_URL)
        page.wait_for_load_state("networkidle")

        accepted = accept_cookies(page)
        print(f"Cookie accepted: {accepted}")

        print("⏸ Opening Playwright Inspector...")
        links = get_offer_links(page)

        print()

        for link in links[:5]:
            print(link)

input("Press ENTER to close the browser...")

        print("✅ Page ready")

        input("Press ENTER to close the browser...")

        browser.close()

        print("🔒 Browser closed")