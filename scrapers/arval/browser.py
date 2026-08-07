from playwright.sync_api import sync_playwright


ARVAL_URL = "https://www.arval.hu/kis-es-kozepvallalkozasok/ajanlat-hosszu-tavu-igenyekre"


def open_arval():
    print("🌐 Opening Arval...")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False
        )

        page = browser.new_page()

        page.goto(ARVAL_URL)

        print("✅ Page loaded")

        input("Press ENTER to close the browser...")

        browser.close()

        print("🔒 Browser closed")
        