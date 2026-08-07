from playwright.sync_api import Page


def get_offer_links(page: Page) -> list[str]:
    """
    Visszaadja az összes Arval ajánlat linkjét.
    """

    offers = page.locator("a.is-result-list")

    count = offers.count()

    print(f"📦 Found {count} offers")

    links = []

    for i in range(count):
        href = offers.nth(i).get_attribute("href")

        if href:
            links.append("https://www.arval.hu" + href)

    return links